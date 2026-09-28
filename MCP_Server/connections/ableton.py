"""AbletonConnection — TCP socket connection to the Ableton Remote Script."""

import socket
import json
import logging
import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, Optional

from MCP_Server.constants import TIER_0_COMMANDS, TIER_1_COMMANDS, TIER_2_COMMANDS, MODIFYING_COMMANDS
import MCP_Server.state as state

logger = logging.getLogger("AbletonBridge")


class CommandError(Exception):
    """Handler-level error reported by Ableton; the connection itself is healthy."""
    pass

# Phase 4.5: Non-idempotent commands should NOT be retried automatically
# because a retry could create duplicate tracks, clips, etc.
NON_IDEMPOTENT_COMMANDS = frozenset([
    "create_midi_track", "create_audio_track", "create_clip",
    "create_return_track", "create_scene", "delete_track",
    "delete_clip", "delete_scene", "delete_device",
    "duplicate_track", "duplicate_clip", "duplicate_scene", "add_notes_to_clip",
    "add_notes_extended", "delete_return_track",
])


@dataclass
class AbletonConnection:
    host: str
    port: int
    sock: socket.socket = None
    _udp_sock: socket.socket = None
    _udp_port: int = 9882

    def connect(self) -> bool:
        """Connect to the Ableton Remote Script socket server"""
        if self.sock:
            return True

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5.0)
            self.sock.connect((self.host, self.port))
            self._recv_buffer = ""  # Clear buffer on new connection
            self._recv_bytes = bytearray()
            self._connected = True
            logger.info("Connected to Ableton at %s:%s", self.host, self.port)
            return True
        except Exception as e:
            logger.error("Failed to connect to Ableton: %s", e)
            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass
            self.sock = None
            self._connected = False
            return False

    def disconnect(self):
        """Disconnect from the Ableton Remote Script"""
        self._connected = False
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error("Error disconnecting from Ableton: %s", e)
            finally:
                self.sock = None
        if self._udp_sock:
            try:
                self._udp_sock.close()
            except Exception:
                pass
            finally:
                self._udp_sock = None

    def __post_init__(self):
        self._recv_buffer = ""
        self._recv_bytes = bytearray()
        self._send_lock = threading.Lock()
        # Read by server.py and dashboard/server.py to report connection
        # health. Previously never assigned, so both always reported
        # "disconnected" even with a healthy socket.
        self._connected = False

    def _ensure_udp_socket(self):
        """Create a UDP socket for real-time parameter sending if not already open."""
        if self._udp_sock is None:
            self._udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return self._udp_sock

    def send_udp_command(self, command_type: str, params: Dict[str, Any] = None):
        """Send a fire-and-forget UDP command to the Remote Script.

        No response is expected or waited for.
        """
        sock = self._ensure_udp_socket()
        command = {
            "type": command_type,
            "params": params or {}
        }
        payload = json.dumps(command).encode("utf-8")
        sock.sendto(payload, (self.host, self._udp_port))
        logger.debug("Sent UDP command: %s", command_type)

    def receive_full_response(self, sock, buffer_size=8192, timeout=15.0):
        """Receive a complete newline-delimited JSON response.

        Two correctness points this method has to get right:

        * **Incremental decoding.** ``recv`` splits wherever the packet
          boundary falls, so decoding each chunk as UTF-8 independently
          corrupts any multi-byte character straddling a boundary. Bytes are
          therefore accumulated and split on ``b"\\n"`` BEFORE decoding.
        * **A wall-clock deadline.** ``settimeout`` applies per ``recv`` call,
          so a peer dribbling one byte per (timeout - epsilon) would keep this
          loop alive forever, holding ``_send_lock`` and stalling every other
          tool. The deadline is checked on every iteration.
        """
        sock.settimeout(timeout)
        deadline = time.monotonic() + timeout

        while True:
            # A complete line already buffered?
            nl = self._recv_bytes.find(b"\n")
            if nl != -1:
                raw_line = bytes(self._recv_bytes[:nl])
                del self._recv_bytes[:nl + 1]
                line = raw_line.strip().decode("utf-8", errors="replace")
                if not line:
                    continue
                try:
                    result = json.loads(line)
                except json.JSONDecodeError as e:
                    # Payload-layer defect, not a transport fault: the socket
                    # is still perfectly healthy, so raise a type send_command
                    # re-raises without tearing the connection down.
                    logger.error("Malformed JSON from Ableton (first 200 chars): %s",
                                 line[:200])
                    raise CommandError(
                        "Ableton sent malformed JSON: {0}".format(e)) from e
                logger.debug("Received complete response (%d chars)", len(line))
                return result

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                logger.warning("Receive deadline exceeded after %.1fs", timeout)
                raise socket.timeout("no complete response from Ableton within "
                                     "{0}s".format(timeout))
            if remaining != timeout:
                sock.settimeout(remaining)

            try:
                chunk = sock.recv(buffer_size)
            except socket.timeout:
                logger.warning("Socket timeout during receive")
                raise
            except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                logger.error("Socket connection error during receive: %s", e)
                raise
            if not chunk:
                raise ConnectionError(
                    "Ableton closed the connection before sending a response")
            self._recv_bytes += chunk

    def _reconnect(self) -> bool:
        """Force a fresh reconnection, clearing all state."""
        logger.info("Forcing reconnection to Ableton...")
        self.disconnect()
        self._recv_buffer = ""
        return self.connect()

    def send_command(self, command_type: str, params: Dict[str, Any] = None, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Send a command to Ableton and return the response.

        Includes automatic retry: if the first attempt fails due to a
        socket error, the connection is reset and the command is retried once.
        Adds small delays around modifying commands for stability.

        Non-idempotent commands (create/delete operations) are NOT retried
        to prevent duplicate side-effects (Phase 4.5).
        """
        # Phase 4.5: non-idempotent commands get a single attempt
        max_attempts = 1 if command_type in NON_IDEMPOTENT_COMMANDS else 2
        is_modifying = command_type in MODIFYING_COMMANDS

        # Determine delay tier: reduced delays since the async semaphore in
        # _tool_handler already serializes tool calls, preventing command flooding.
        # Tier 0 = no delay, Tier 1 = 10ms post, Tier 2 = 10ms pre+post
        if command_type in TIER_2_COMMANDS:
            pre_delay, post_delay = 0.01, 0.01
        elif command_type in TIER_1_COMMANDS:
            pre_delay, post_delay = 0, 0.01
        else:
            pre_delay, post_delay = 0, 0

        for attempt in range(1, max_attempts + 1):
            with self._send_lock:
                if not self.sock and not self.connect():
                    raise ConnectionError("Not connected to Ableton")

                command = {
                    "type": command_type,
                    "params": params or {}
                }

                try:
                    logger.debug("Sending command: %s (attempt %d)", command_type, attempt)

                    # Bound the WRITE separately from the read. receive_full_response
                    # sets its own (up to 60s) timeout and leaves it on the socket;
                    # without an explicit value here, sendall inherits that, and a
                    # timeout mid-sendall raises with a truncated command already
                    # sent — which is unrecoverable for non-idempotent commands.
                    payload = (json.dumps(command) + '\n').encode('utf-8')
                    self.sock.settimeout(10.0)
                    self.sock.sendall(payload)

                    # Pre-delay: give Ableton time to process before we read the response
                    if pre_delay:
                        time.sleep(pre_delay)

                    # Set timeout based on command type (caller override takes priority)
                    if timeout is None:
                        from MCP_Server.constants import SLOW_COMMAND_TIMEOUTS
                        timeout = SLOW_COMMAND_TIMEOUTS.get(
                            command_type, 15.0 if is_modifying else 10.0
                        )
                    # Receive the response (already parsed by receive_full_response)
                    response = self.receive_full_response(self.sock, timeout=timeout)
                    logger.debug("Response status: %s", response.get('status', 'unknown'))

                    if response.get("status") == "error":
                        # The handler raised, but the socket is still healthy:
                        # surface the error WITHOUT tearing the connection down.
                        logger.error("Ableton error: %s", response.get('message'))
                        raise CommandError(response.get("message", "Unknown error from Ableton"))

                    # Post-delay: let Ableton settle before the next command
                    if post_delay:
                        time.sleep(post_delay)

                    return response.get("result", {})

                except CommandError:
                    # Handler-level error: connection is fine, do not retry.
                    raise
                except Exception as e:
                    logger.error("Command '%s' attempt %d failed: %s", command_type, attempt, e)
                    # Close the broken socket and clear buffer
                    self.disconnect()
                    self._recv_buffer = ""
                    self._recv_bytes = bytearray()

                    if attempt < max_attempts:
                        # Wait briefly then retry with a fresh connection
                        time.sleep(0.1)
                        if not self.connect():
                            raise ConnectionError("Failed to reconnect to Ableton")
                        logger.info("Reconnected, retrying command...")
                    else:
                        raise Exception(f"Command '{command_type}' failed after {max_attempts} attempts: {e}")


_conn_lock = threading.Lock()


def get_ableton_connection():
    """Get or create a persistent Ableton connection.

    Serialised with a module-level lock: this is reached from tool worker
    threads, the event loop (auto-checkpoint), the show-autopilot thread and
    the dashboard thread. The previous check-then-act version could let two
    threads each build a connection, publish one to the module global and
    then validate/destroy the *other* thread's live socket.
    """
    with _conn_lock:
        if state.ableton_connection is not None:
            try:
                if state.ableton_connection.sock is None:
                    raise ConnectionError("Socket is None")
                # NB: do NOT settimeout() here. It is never reverted, so the
                # next sendall inherited 1.0s and could abort part-way through a
                # large payload — silently truncating commands. getpeername()
                # is a purely local call and never blocks, so it needs no
                # timeout at all.
                state.ableton_connection.sock.getpeername()
                return state.ableton_connection
            except Exception as e:
                logger.warning("Existing connection is no longer valid: %s", e)
                try:
                    state.ableton_connection.disconnect()
                except Exception:
                    pass
                state.ableton_connection = None

        if state.ableton_connection is None:
            # Try to connect up to 3 times with a short delay between attempts
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                conn = None
                try:
                    logger.info("Connecting to Ableton (attempt %d/%d)...", attempt, max_attempts)
                    # Build and validate into a LOCAL, publish only on success.
                    conn = AbletonConnection(host="localhost", port=9877)
                    if not conn.connect():
                        continue
                    conn.send_command("get_session_info")
                    logger.info("Created new persistent connection to Ableton")
                    state.ableton_connection = conn
                    state.ableton_connected_event.set()
                    return conn
                except Exception as e:
                    logger.error("Connection attempt %d failed: %s", attempt, e)
                    if conn is not None:
                        try:
                            conn.disconnect()
                        except Exception:
                            pass
                    state.ableton_connection = None

                if attempt < max_attempts:
                    time.sleep(1.0)

            logger.error("Failed to connect to Ableton after multiple attempts")
            raise Exception(
                "Could not connect to Ableton. Make sure the Remote Script is running.")

    return state.ableton_connection
