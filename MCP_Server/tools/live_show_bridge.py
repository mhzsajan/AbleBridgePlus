"""Live-show OSC/UDP bridge tools (v0.9.0, extended in v0.9.1).

Two jobs live here:

1. A *generic* send path out of the bridge to any OSC/UDP target on the
   show network — Behringer WING (192.168.1.3:2223), TouchDesigner, an
   AbleSet Canvas "raw external OSC target" button, a lighting desk, etc.
   ``pythonosc`` (``python-osc`` in pyproject.toml) is the only dependency;
   these tools do not need Ableton at all.

2. Thin server-side adapters over existing read-only Ableton commands
   (``get_song_transport``, ``get_master_meters``) plus MCP wrappers for the
   v0.9/v0.9.1 remote-script commands. The only new v0.9.1 remote command,
   ``probe_lom_capability``, lives in the remote-script layer; forwarded here.
   The heavy lifting on the Ableton side already exists in the remote script.

Locator macros are stored in-process (a module-level dict). The
``jump_to_locator`` tool in ``tools/arrangement.py`` calls the module-level
``fire_registered_macro_for`` helper after a SUCCESSFUL jump, so a section
change can fire its registered OSC macro automatically. Failed jumps never
fire. ``fire_locator_macro`` remains available for manual firing.

AbleSet show-state OSC is received by an optional background UDP listener
(default port 39052 — deliberately NOT 39051, AbleSet's own port, to avoid a
bind conflict). A human must point AbleSet's OSC output at that port in
AbleSet's settings; the bridge cannot auto-configure AbleSet.
"""
import json
import logging
import math
import socket
import threading

from mcp.server.fastmcp import Context

from MCP_Server.tools._base import _tool_handler
from MCP_Server.connections.ableton import get_ableton_connection

try:
    from pythonosc.udp_client import SimpleUDPClient
except ImportError:  # pragma: no cover - dependency is declared in pyproject
    SimpleUDPClient = None

try:
    from pythonosc.dispatcher import Dispatcher
    from pythonosc.osc_server import ThreadingOSCUDPServer
except ImportError:  # pragma: no cover - fall back to a raw UDP socket
    Dispatcher = None
    ThreadingOSCUDPServer = None

logger = logging.getLogger("AbletonBridge")

# Named OSC macros bound to a locator / section name. Tool calls are
# serialised by _base._ableton_semaphore, so a plain dict is sufficient.
_LOCATOR_MACROS: dict = {}

# WING delay-time subdivisions: milliseconds at 60 BPM (= 60000 / BPM scaled
# by the subdivision's fraction of a whole note). These five are the show's
# working set; aliases below cover the obvious spellings.
_DELAY_SUBDIVISION_MS_PER_BPM = {
    "1/4": 60000.0,          # quarter note
    "1/8": 30000.0,          # eighth note
    "1/16": 15000.0,         # sixteenth note
    "1/8 dotted": 45000.0,   # dotted eighth = 1.5 x eighth
    "1/8 triplet": 20000.0,  # eighth triplet = 2/3 x eighth
}
_DELAY_SUBDIVISION_ALIASES = {
    "quarter": "1/4", "quarter note": "1/4", "1/4 note": "1/4",
    "eighth": "1/8", "eighth note": "1/8", "1/8 note": "1/8",
    "sixteenth": "1/16", "sixteenth note": "1/16", "1/16 note": "1/16",
    "dotted 1/8": "1/8 dotted", "dotted eighth": "1/8 dotted",
    "1/8d": "1/8 dotted", "1/8.": "1/8 dotted",
    "triplet 1/8": "1/8 triplet", "eighth triplet": "1/8 triplet",
    "1/8t": "1/8 triplet",
}

# AbleSet show-state OSC listener. The dict is keyed by OSC address and holds
# the latest value received for that address. All access is under the lock:
# listener threads write, tool/resource reads snapshot it.
_ABLESET_STATE_LOCK = threading.Lock()
_ABLESET_STATE: dict = {}
_ABLESET_LISTENER = None       # ThreadingOSCUDPServer (python-osc path)
_ABLESET_LISTENER_THREAD = None
_ABLESET_LISTENER_PORT = None
_ABLESET_LISTENER_MODE = None  # "pythonosc" or "raw-udp"
_ABLESET_LISTENER_ERROR = None
_ABLESET_SOCKET = None         # raw-socket fallback
_ABLESET_STOP_EVENT = None     # raw-socket fallback
_ABLESET_TRACKED_ADDRESSES = (
    "/setlist/activeSongName",
    "/setlist/activeSectionName",
    "/setlist/activeSongStart",
    "/setlist/activeSongEnd",
    "/global/isPlaying",
)


# ---------------------------------------------------------------------------
# Shared OSC helpers (single implementation, reused by every tool here)
# ---------------------------------------------------------------------------

def _to_args(value):
    """Normalise a scalar or a list into a list of OSC arguments."""
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _coerce_osc_args(args):
    """Coerce Python ints to float for OSC transport.

    python-osc emits an ``,i`` type tag for ints and ``,f`` for floats. Several
    show devices — notably the Behringer WING — only act on numeric OSC values
    tagged ``,f`` and silently ignore ``,i`` (verified live 2026-11-17:
    ``/fx/5/time`` as int was ignored, as float it stored). Coercing ints to
    float is safe for the usual OSC consumers (they parse either as a number);
    bools are left alone (python-osc tags them ``,T``/``,F`` on purpose).
    """
    out = []
    for value in args:
        if isinstance(value, bool):
            out.append(value)
        elif isinstance(value, int):
            out.append(float(value))
        elif isinstance(value, (list, tuple)):
            out.append(_coerce_osc_args(value))
        else:
            out.append(value)
    return out


def _send_osc_message(host, port, address, args):
    """Send one OSC message over UDP. Returns {"sent": bool, "error": str|None}."""
    if SimpleUDPClient is None:
        return {"sent": False,
                "error": "python-osc is not installed (python-osc>=1.8.0 required)"}
    try:
        client = SimpleUDPClient(str(host), int(port))
        client.send_message(str(address), _coerce_osc_args(list(args)))
        return {"sent": True, "error": None}
    except Exception as exc:  # bad host, bad port, unreachable network ...
        return {"sent": False,
                "error": "{0}: {1}".format(type(exc).__name__, exc)}


def _send_osc_batch(messages):
    """Send a list of OSC message dicts. Returns a summary dict.

    Each message may use ``args`` (list) or ``value`` (scalar or list) plus
    ``host``, ``port`` and ``address``. Badly formed entries are recorded as
    errors; one failure never aborts the rest of the batch.
    """
    if not isinstance(messages, (list, tuple)):
        return {"sent": 0, "errors": ["messages must be a list of objects"],
                "details": []}

    sent = 0
    errors = []
    details = []
    for index, msg in enumerate(messages):
        if not isinstance(msg, dict):
            errors.append({"index": index, "error": "message must be an object"})
            continue
        host = msg.get("host")
        port = msg.get("port")
        address = msg.get("address")
        if "args" in msg:
            args = _to_args(msg["args"])
        elif "value" in msg:
            args = _to_args(msg["value"])
        else:
            errors.append({"index": index,
                           "error": "message has neither 'args' nor 'value'"})
            continue
        if not host or port is None or not address:
            errors.append({"index": index,
                           "error": "message needs 'host', 'port' and 'address'"})
            continue
        result = _send_osc_message(host, port, address, args)
        if result["sent"]:
            sent += 1
            details.append({"index": index, "host": host, "port": port,
                            "address": address, "args": args, "sent": True})
        else:
            errors.append({"index": index, "host": host, "port": port,
                           "address": address, "error": result["error"]})
    return {"sent": sent, "errors": errors, "details": details}


# ---------------------------------------------------------------------------
# Locator macro auto-fire hook (called by arrangement.jump_to_locator)
# ---------------------------------------------------------------------------

def _find_locator_macro(locator_name):
    """Return (matched_key, messages) for a locator name, or (None, None).

    Exact match first, then case-insensitive — the same rule as
    ``fire_locator_macro``. Names may arrive as ints (a cue index); both the
    raw value and its string form are attempted.
    """
    if locator_name in _LOCATOR_MACROS:
        return locator_name, _LOCATOR_MACROS[locator_name]
    name = str(locator_name)
    if name in _LOCATOR_MACROS:
        return name, _LOCATOR_MACROS[name]
    needle = name.lower()
    for key, stored in _LOCATOR_MACROS.items():
        if str(key).lower() == needle:
            return key, stored
    return None, None


def fire_registered_macro_for(locator_name):
    """Fire the OSC macro registered for ``locator_name`` (if any).

    Used by ``arrangement.jump_to_locator`` AFTER a successful jump. Sends via
    the shared ``_send_osc_batch``; matches exact first then case-insensitive.
    Returns a dict with a ``count`` key (0 when nothing is registered) and
    NEVER raises on a send failure — per-message errors are reported instead.
    """
    matched, messages = _find_locator_macro(locator_name)
    if messages is None:
        return {
            "locator_name": locator_name, "matched": None,
            "count": 0, "sent": 0, "errors": [],
            "note": "no macro registered for this locator",
        }
    result = _send_osc_batch(messages)
    return {
        "locator_name": locator_name, "matched": matched,
        "count": result["sent"], "sent": result["sent"],
        "errors": result["errors"], "details": result["details"],
    }


# ---------------------------------------------------------------------------
# WING delay-time math (server-side only, no remote handler)
# ---------------------------------------------------------------------------

def _normalise_subdivision(subdivision):
    """Return (canonical_name, ms_at_1_bpm) or (None, error_message)."""
    key = " ".join(str(subdivision).strip().lower().split())
    key = _DELAY_SUBDIVISION_ALIASES.get(key, key)
    if key not in _DELAY_SUBDIVISION_MS_PER_BPM:
        options = ", ".join(sorted(_DELAY_SUBDIVISION_MS_PER_BPM))
        return None, ("unknown subdivision {0!r}; supported: {1}".format(
            subdivision, options))
    return key, _DELAY_SUBDIVISION_MS_PER_BPM[key]


# ---------------------------------------------------------------------------
# AbleSet show-state listener (background UDP / OSC)
# ---------------------------------------------------------------------------

def _store_ableset_value(address, args):
    """Store one OSC message's value(s) in the shared snapshot."""
    if len(args) == 1:
        value = args[0]
    else:
        value = list(args)
    with _ABLESET_STATE_LOCK:
        _ABLESET_STATE[str(address)] = value


def _ableset_snapshot():
    """Build the shared snapshot dict (thread-safe, no blocking I/O)."""
    with _ABLESET_STATE_LOCK:
        state = dict(_ABLESET_STATE)
        running = (_ABLESET_LISTENER is not None or _ABLESET_SOCKET is not None)
        port = _ABLESET_LISTENER_PORT
        mode = _ABLESET_LISTENER_MODE
        error = _ABLESET_LISTENER_ERROR
    return {
        "listener_running": bool(running),
        "port": port,
        "mode": mode,
        "status": "ok" if state else "no_data",
        "state": state,
        "error": error,
        "tracked_addresses": list(_ABLESET_TRACKED_ADDRESSES),
        "note": ("No OSC received yet. A human must point AbleSet's OSC "
                 "output at this listener port in AbleSet's settings — the "
                 "bridge cannot auto-configure AbleSet."
                 if not state else
                 "Point AbleSet's OSC output at this listener port in "
                 "AbleSet's settings; the bridge cannot auto-configure AbleSet."),
    }


def get_ableset_snapshot():
    """Public alias of the snapshot builder, used by the MCP resource.

    Guarantees ``ableton://ableset/state`` and ``get_ableset_state`` return
    the same data from the same thread-safe read.
    """
    return _ableset_snapshot()


def _stop_ableset_listener():
    """Stop the current listener if any. Called outside the state lock."""
    global _ABLESET_LISTENER, _ABLESET_LISTENER_THREAD, _ABLESET_LISTENER_PORT
    global _ABLESET_LISTENER_MODE, _ABLESET_SOCKET, _ABLESET_STOP_EVENT

    server = _ABLESET_LISTENER
    thread = _ABLESET_LISTENER_THREAD
    sock = _ABLESET_SOCKET
    stop_event = _ABLESET_STOP_EVENT
    # Invalidate first so get_ableset_state() never reports a dead listener.
    _ABLESET_LISTENER = None
    _ABLESET_LISTENER_THREAD = None
    _ABLESET_LISTENER_PORT = None
    _ABLESET_LISTENER_MODE = None
    _ABLESET_SOCKET = None
    _ABLESET_STOP_EVENT = None

    if server is not None:
        try:
            server.shutdown()
        except Exception:
            pass
        try:
            server.server_close()
        except Exception:
            pass
    if stop_event is not None:
        stop_event.set()
    if sock is not None:
        try:
            sock.close()
        except Exception:
            pass
    if (thread is not None and thread.is_alive()
            and thread is not threading.current_thread()):
        thread.join(timeout=2.0)


def _raw_ableset_loop(sock, stop_event, port):
    """Minimal OSC decoder for the fallback when python-osc server is absent.

    AbleSet's show-state messages are single int/float/string arguments; this
    handles OSC type tags i, f, s and a best-effort decode of common others.
    """
    while not stop_event.is_set():
        try:
            data, _ = sock.recvfrom(65535)
        except OSError:
            break
        try:
            # An OSC packet is an address (NULL-padded to a 4-byte boundary),
            # then a type-tag string, then the packed arguments.
            split = data.find(b"\x00")
            if split < 0:
                continue
            address = data[:split].decode("utf-8", "replace")
            rest = data[split + 1:]
            pad = (4 - (len(address) + 1) % 4) % 4
            rest = rest[pad:]
            if not rest or rest[0:1] != b",":
                continue
            tag_end = rest.find(b"\x00")
            if tag_end < 0:
                continue
            tags = rest[1:tag_end].decode("ascii", "replace")
            pos = tag_end + 1
            pos += (4 - (pos % 4)) % 4
            values = []
            for tag in tags:
                if tag == "i":
                    values.append(int.from_bytes(rest[pos:pos + 4], "big",
                                                 signed=True))
                    pos += 4
                elif tag == "f":
                    values.append(_unpack_float(rest[pos:pos + 4]))
                    pos += 4
                elif tag == "s":
                    end = rest.find(b"\x00", pos)
                    if end < 0:
                        break
                    values.append(rest[pos:end].decode("utf-8", "replace"))
                    pos = end + 1
                    pos += (4 - (pos % 4)) % 4
                else:
                    break  # unsupported type: keep the values decoded so far
            _store_ableset_value(address, values)
        except Exception:
            logger.debug("Malformed OSC packet on AbleSet port %s", port,
                         exc_info=True)


def _unpack_float(raw):
    """Decode one big-endian IEEE-754 float (stdlib, no numpy)."""
    import struct
    if len(raw) < 4:
        return 0.0
    return struct.unpack(">f", raw[:4])[0]


def _start_ableset_listener(port):
    """Start (or restart) the background AbleSet listener. Returns a dict."""
    global _ABLESET_LISTENER, _ABLESET_LISTENER_THREAD, _ABLESET_LISTENER_PORT
    global _ABLESET_LISTENER_MODE, _ABLESET_LISTENER_ERROR, _ABLESET_SOCKET
    global _ABLESET_STOP_EVENT

    port = int(port)
    if not 1 <= port <= 65535:
        return {"status": "error", "error": "port must be 1..65535",
                "port": port}

    with _ABLESET_STATE_LOCK:
        already = (_ABLESET_LISTENER is not None or _ABLESET_SOCKET is not None)
        same_port = (_ABLESET_LISTENER_PORT == port)
    if already and same_port:
        snapshot = _ableset_snapshot()
        snapshot["status"] = "already_running"
        snapshot["note"] = ("Listener already running on port {0}. ".format(port)
                            + snapshot["note"])
        return snapshot

    _stop_ableset_listener()
    _ABLESET_LISTENER_ERROR = None

    if ThreadingOSCUDPServer is not None and Dispatcher is not None:
        try:
            dispatcher = Dispatcher()

            def make_handler(address):
                return lambda _addr, *args, _a=address: _store_ableset_value(
                    _a, args)

            for address in _ABLESET_TRACKED_ADDRESSES:
                dispatcher.map(address, make_handler(address))

            def default_handler(address, *args):
                # Keep other setlist/global state too — the e.g. list is not
                # exhaustive and AbleSet versions add addresses.
                if str(address).startswith(("/setlist/", "/global/")):
                    _store_ableset_value(address, args)

            dispatcher.set_default_handler(default_handler)
            server = ThreadingOSCUDPServer(("0.0.0.0", port), dispatcher)
            thread = threading.Thread(
                target=server.serve_forever,
                name="ableset-osc-listener", daemon=True)
            thread.start()
            _ABLESET_LISTENER = server
            _ABLESET_LISTENER_THREAD = thread
            _ABLESET_LISTENER_PORT = port
            _ABLESET_LISTENER_MODE = "pythonosc"
        except Exception as exc:
            _ABLESET_LISTENER_ERROR = "{0}: {1}".format(type(exc).__name__, exc)
            logger.warning("python-osc listener failed on port %s: %s",
                           port, _ABLESET_LISTENER_ERROR)
    if _ABLESET_LISTENER is None:
        # Raw UDP fallback (or python-osc failed to bind).
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", port))
            stop_event = threading.Event()
            thread = threading.Thread(
                target=_raw_ableset_loop, args=(sock, stop_event, port),
                name="ableset-raw-listener", daemon=True)
            thread.start()
            _ABLESET_SOCKET = sock
            _ABLESET_STOP_EVENT = stop_event
            _ABLESET_LISTENER_THREAD = thread
            _ABLESET_LISTENER_PORT = port
            _ABLESET_LISTENER_MODE = "raw-udp"
        except Exception as exc:
            _ABLESET_LISTENER_ERROR = "{0}: {1}".format(type(exc).__name__, exc)
            return {"status": "error", "error": _ABLESET_LISTENER_ERROR,
                    "port": port, "listener_running": False}

    snapshot = _ableset_snapshot()
    snapshot["status"] = "started"
    snapshot["bind"] = "0.0.0.0:{0}".format(port)
    return snapshot


def register_tools(mcp):
    """Register live-show OSC bridge tools with the MCP server."""

    # -----------------------------------------------------------------------
    # Remote-command wrappers (handlers added by the remote-script layer)
    # -----------------------------------------------------------------------

    @mcp.tool()
    @_tool_handler("clearing arrangement clip envelopes")
    def clear_arrangement_clip_envelopes(ctx: Context, track_index: int,
                                         clip_index: int) -> str:
        """Remove every automation envelope from one arrangement clip.

        track_index is 0-based; clip_index is the index within the
        arrangement (as returned by get_arrangement_clips)."""
        ableton = get_ableton_connection()
        return json.dumps(ableton.send_command("clear_arrangement_clip_envelopes", {
            "track_index": track_index,
            "clip_index": clip_index,
        }))

    @mcp.tool()
    @_tool_handler("creating a named locator")
    def create_named_locator(ctx: Context, beat: float, name: str) -> str:
        """Create a named locator (cue point) at an absolute beat position.

        The name is what ``jump_to_locator`` and ``fire_locator_macro`` use."""
        ableton = get_ableton_connection()
        return json.dumps(ableton.send_command("create_named_locator", {
            "beat": float(beat),
            "name": name,
        }))

    @mcp.tool()
    @_tool_handler("probing the MIDI CC envelope surface")
    def probe_midi_cc_envelope_surface(ctx: Context, track_index: int,
                                       clip_index: int = 0) -> str:
        """Read-only capability probe: how this Live version exposes MIDI CC
        envelopes on a clip. Opens nothing, changes nothing — pure evidence
        for envelope feature design."""
        ableton = get_ableton_connection()
        return json.dumps(ableton.send_command("probe_midi_cc_envelope_surface", {
            "track_index": track_index,
            "clip_index": clip_index,
        }))

    @mcp.tool()
    @_tool_handler("probing LOM capability")
    def probe_lom_capability(ctx: Context, root: str = "song",
                             track_index: int = 0, clip_index: int = 0,
                             device_index: int = 0, pattern: str = "") -> str:
        """Read-only capability probe of the Live Object Model (LOM).

        ``dir()``-style introspection of a WHITELISTED LOM root — nothing is
        opened, assigned or changed. Whitelisted roots are ``song``, ``track``,
        ``clip``, ``device``, ``scene`` and ``return``; bad roots are rejected
        by the remote handler, never introspected. ``pattern`` filters the
        attribute names (case-insensitive substring). An empty pattern returns
        a curated set of interesting names plus a short alphabetical sample —
        the full ``dir()`` is deliberately never dumped.

        This is pure evidence for feature design: it tells you which LOM
        attributes this Live version actually exposes before you write a tool
        that assumes they exist.
        """
        ableton = get_ableton_connection()
        return json.dumps(ableton.send_command("probe_lom_capability", {
            "root": root,
            "track_index": track_index,
            "clip_index": clip_index,
            "device_index": device_index,
            "pattern": pattern,
        }))

    # -----------------------------------------------------------------------
    # Generic external OSC/UDP tools
    # -----------------------------------------------------------------------

    @mcp.tool()
    @_tool_handler("sending an external OSC parameter")
    def set_external_param(ctx: Context, host: str, port: int, address: str,
                           value, protocol: str = "udp") -> str:
        """Write one value to ANY OSC/UDP device on the show network.

        This is the generic escape hatch — Behringer WING at
        192.168.1.3:2223, TouchDesigner, an AbleSet Canvas "raw external OSC
        target" button, a lighting desk, etc. No Ableton command is involved.

        ``value`` may be a single int/float/str or a list (sent as multiple
        OSC arguments). ``protocol`` currently supports only ``udp`` (the
        pythonosc SimpleUDPClient); any other value is reported as an error
        rather than silently ignored.
        """
        if str(protocol).lower() != "udp":
            return json.dumps({
                "host": host, "port": port, "address": address, "value": value,
                "sent": False,
                "error": "unsupported protocol {0!r}: only 'udp' is implemented".format(
                    protocol),
            })
        result = _send_osc_message(host, port, address, _to_args(value))
        return json.dumps({
            "host": host, "port": port, "address": address, "value": value,
            "sent": result["sent"], "error": result["error"],
        })

    @mcp.tool()
    @_tool_handler("sending an OSC macro")
    def send_osc_macro(ctx: Context, messages: list) -> str:
        """Send a list of OSC messages in one call.

        Each message is an object with ``host``, ``port``, ``address`` and
        either ``args`` (a list) or ``value`` (a scalar or list), e.g.::

            [{"host": "192.168.1.3", "port": 2223,
              "address": "/ch/01/mix/on", "value": 1}]

        This is the "raw external OSC target" pattern used by AbleSet Canvas
        buttons, now available from inside the bridge. One bad message does
        not stop the rest; a per-message error list is returned.
        """
        result = _send_osc_batch(messages)
        return json.dumps({
            "count": result["sent"],
            "sent": result["sent"],
            "errors": result["errors"],
            "details": result["details"],
        })

    @mcp.tool()
    @_tool_handler("pushing transport state over OSC")
    def send_transport_state(ctx: Context, host: str, port: int,
                             address_prefix: str = "/transport") -> str:
        """One-shot push of the current Ableton transport state to OSC
        subscribers (TouchDesigner, WING, visuals, ...).

        Sends separate messages beneath ``address_prefix``:
        ``/is_playing`` (int 0/1), ``/tempo`` (float), ``/beat`` (float,
        current_time in beats) and ``/locator`` (string, current section /
        locator name when the transport exposes one). Fields the transport
        read does not expose are skipped — nothing is fabricated.

        This is a ONE-SHOT push. Poll it, or call it from a show macro, for a
        continuous heartbeat.
        """
        ableton = get_ableton_connection()
        transport = ableton.send_command("get_song_transport")
        prefix = address_prefix.rstrip("/")

        sent = {}
        errors = {}

        def push(field, suffix, args):
            result = _send_osc_message(host, port, prefix + suffix, args)
            sent[field] = result["sent"]
            if result["error"]:
                errors[field] = result["error"]

        if "is_playing" in transport:
            push("is_playing", "/is_playing",
                 [1 if transport["is_playing"] else 0])
        if "tempo" in transport:
            push("tempo", "/tempo", [float(transport["tempo"])])
        if "current_time" in transport:
            push("beat", "/beat", [float(transport["current_time"])])

        # Live's transport reply does not normally carry a section name;
        # only send /locator when one of these keys is actually present.
        locator = None
        for key in ("current_section", "current_locator", "locator",
                    "section_name", "cue_name", "current_cue"):
            if transport.get(key):
                locator = transport[key]
                break
        if locator is not None:
            push("locator", "/locator", [str(locator)])

        return json.dumps({
            "host": host, "port": port, "prefix": prefix,
            "sent": sent, "errors": errors,
            "skipped": [f for f in ("is_playing", "tempo", "beat", "locator")
                        if f not in sent],
            "note": "one-shot; poll or call from a macro for continuous heartbeat",
        })

    @mcp.tool()
    @_tool_handler("watching master level over OSC")
    def show_level_watch(ctx: Context, host: str, port: int,
                         address: str = "/warning/level",
                         peak_db: float = -1.0, rms_db: float = -6.0) -> str:
        """Check Live's master meters and send an OSC warning on an over-level.

        HONESTY NOTE: Ableton exposes only broadband output meters (dBFS here),
        NOT true LUFS or a standards-compliant loudness measurement. The
        ``peak_db`` / ``rms_db`` thresholds are compared against the master's
        broadband meter readings (with a simple L/R RMS estimate); do NOT
        treat this as a broadcast loudness or true-peak checker.

        Sends one OSC warning message to ``address`` when either threshold is
        exceeded, and reports ``alerted`` / ``sent`` in the result.
        """
        ableton = get_ableton_connection()
        meters = ableton.send_command("get_master_meters")

        left = meters.get("output_meter_left")
        right = meters.get("output_meter_right")
        level = meters.get("output_meter_level")

        readings = {}
        for name, val in (("left_dbfs", left), ("right_dbfs", right),
                          ("level_dbfs", level)):
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                readings[name] = round(float(val), 2)

        candidates = [float(v) for v in (left, right, level)
                      if isinstance(v, (int, float)) and not isinstance(v, bool)]
        peak = max(candidates) if candidates else None

        rms = None
        if (isinstance(left, (int, float)) and not isinstance(left, bool)
                and isinstance(right, (int, float)) and not isinstance(right, bool)):
            lin_l = 10.0 ** (float(left) / 20.0)
            lin_r = 10.0 ** (float(right) / 20.0)
            rms_lin = math.sqrt((lin_l * lin_l + lin_r * lin_r) / 2.0)
            rms = round(20.0 * math.log10(max(rms_lin, 1e-9)), 2)

        peak_threshold = float(peak_db)
        rms_threshold = float(rms_db)
        peak_exceeded = peak is not None and peak >= peak_threshold
        rms_exceeded = rms is not None and rms >= rms_threshold
        alerted = bool(peak_exceeded or rms_exceeded)

        sent = False
        error = None
        if alerted:
            payload = {
                "peak_dbfs": peak, "rms_dbfs_est": rms,
                "peak_threshold": peak_threshold, "rms_threshold": rms_threshold,
                "reason": "peak" if peak_exceeded else "rms",
            }
            result = _send_osc_message(host, port, address, [json.dumps(payload)])
            sent = result["sent"]
            error = result["error"]

        return json.dumps({
            "host": host, "port": port, "address": address,
            "readings": readings, "peak_dbfs": peak, "rms_dbfs_est": rms,
            "thresholds": {"peak_db": peak_threshold, "rms_db": rms_threshold},
            "peak_exceeded": peak_exceeded, "rms_exceeded": rms_exceeded,
            "alerted": alerted, "sent": sent, "error": error,
            "note": "broadband dBFS meters, NOT true LUFS / true-peak",
        })

    # -----------------------------------------------------------------------
    # Locator-bound macro storage. As of v0.9.1 a successful jump_to_locator
    # auto-fires the registered macro (see arrangement.py); fire_locator_macro
    # remains available for manual/explicit firing.
    # -----------------------------------------------------------------------

    @mcp.tool()
    @_tool_handler("registering a locator macro")
    def register_locator_macro(ctx: Context, locator_name: str,
                               messages: list) -> str:
        """Store a named OSC macro bound to a locator / section name.

        The macro is a list of OSC messages in the same shape as
        ``send_osc_macro``. Storing it does NOT fire it: after a successful
        ``jump_to_locator`` to this section, call ``fire_locator_macro`` with
        the same name. (Auto-firing on the jump itself would require editing
        ``tools/arrangement.py``, which is outside this release's ownership.)

        Names are stored verbatim; ``fire_locator_macro`` matches exactly
        first, then case-insensitively.
        """
        if not isinstance(messages, list):
            raise ValueError("messages must be a list of OSC message objects")
        _LOCATOR_MACROS[str(locator_name)] = list(messages)
        return json.dumps({
            "status": "ok", "registered": locator_name,
            "messages": messages, "count": len(messages),
            "note": "stored only; call fire_locator_macro after a successful jump",
        })

    @mcp.tool()
    @_tool_handler("firing a locator macro")
    def fire_locator_macro(ctx: Context, locator_name: str) -> str:
        """Send the OSC macro registered for a locator / section name.

        Matches the name exactly first, then case-insensitively. Returns a
        zero-count result (not an error) when nothing is registered. Use this
        only AFTER a successful ``jump_to_locator`` — never fire on a failed
        jump.
        """
        return json.dumps(fire_registered_macro_for(locator_name))

    # -----------------------------------------------------------------------
    # WING tempo-synced delay (server-side, no remote handler)
    # -----------------------------------------------------------------------

    @mcp.tool()
    @_tool_handler("setting WING delay time from tempo")
    def set_wing_delay_time_from_tempo(
            ctx: Context, host: str = "192.168.1.3", port: int = 2223,
            address: str = "/fx/5/time", subdivision: str = "1/8") -> str:
        """Convert Ableton's current tempo to a delay time and write it to WING.

        HONESTY NOTE: previous live tests showed the WING console does NOT
        follow MIDI clock. This tool therefore writes the OSC parameter
        directly — a reliable workaround — instead of pretending to slave the
        desk to MIDI. The tempo is sampled from Ableton at CALL TIME (via the
        read-only get_song_transport command), NOT continuously; call this
        again from a macro when the tempo changes.

        ``subdivision`` selects the note value: 1/4 = 60000/BPM ms,
        1/8 = 30000/BPM, 1/16 = 15000/BPM, 1/8 dotted = 45000/BPM,
        1/8 triplet = 20000/BPM (a few aliases are accepted too). Unknown
        subdivisions are rejected with a clear error. Nothing is sent when
        the tempo cannot be read or the subdivision is invalid.
        """
        canonical, ms_per_bpm = _normalise_subdivision(subdivision)
        if canonical is None:
            return json.dumps({
                "tempo": None, "subdivision": subdivision, "ms": None,
                "address": address, "sent": False, "error": ms_per_bpm,
            })
        try:
            ableton = get_ableton_connection()
            transport = ableton.send_command("get_song_transport")
            tempo = transport.get("tempo") if isinstance(transport, dict) else None
        except Exception as exc:
            return json.dumps({
                "tempo": None, "subdivision": canonical, "ms": None,
                "address": address, "sent": False,
                "error": "could not read tempo: {0}: {1}".format(
                    type(exc).__name__, exc),
            })
        try:
            tempo = float(tempo)
        except (TypeError, ValueError):
            return json.dumps({
                "tempo": None, "subdivision": canonical, "ms": None,
                "address": address, "sent": False,
                "error": "get_song_transport returned no usable tempo",
            })
        if not math.isfinite(tempo) or tempo <= 0:
            return json.dumps({
                "tempo": tempo, "subdivision": canonical, "ms": None,
                "address": address, "sent": False,
                "error": "tempo must be a positive finite number (got {0})".format(
                    tempo),
            })
        delay_ms = round(ms_per_bpm / tempo, 3)
        result = _send_osc_message(host, port, address, [delay_ms])
        return json.dumps({
            "tempo": round(tempo, 3), "subdivision": canonical,
            "ms": delay_ms, "address": address,
            "host": host, "port": port,
            "sent": result["sent"], "error": result["error"],
            "note": ("WING does not follow MIDI clock (verified in live tests); "
                     "this writes the OSC parameter directly. Tempo sampled "
                     "at call time, not continuous — call from a macro for updates."),
        })

    # -----------------------------------------------------------------------
    # AbleSet show-state listener (single source of truth for the show)
    # -----------------------------------------------------------------------

    @mcp.tool()
    @_tool_handler("starting the AbleSet state listener")
    def start_ableset_listener(port: int = 39052) -> str:
        """Start (or restart) the background AbleSet show-state OSC listener.

        AbleSet is the show's single source of truth for song name, section
        and start/end. It emits these as OSC, and this tool listens on UDP
        ``port`` (default 39052 — deliberately NOT 39051, AbleSet's own port,
        to avoid a bind conflict). Idempotent: calling again with the same
        port is a no-op; a different port restarts the listener.

        HUMAN ACTION REQUIRED: you must point AbleSet's OSC output at this
        listener port in AbleSet's settings. The bridge cannot auto-configure
        AbleSet and will report ``no_data`` until AbleSet actually sends.
        """
        return json.dumps(_start_ableset_listener(port))

    @mcp.tool()
    @_tool_handler("reading the AbleSet state snapshot")
    def get_ableset_state() -> str:
        """Return the latest AbleSet show-state OSC snapshot + listener status.

        Reads the in-memory values captured by ``start_ableset_listener``;
        never blocks and never dials AbleSet. Before the listener is started
        or before AbleSet sends anything, this honestly reports
        ``listener_running: false`` and ``status: "no_data"``.

        HUMAN ACTION REQUIRED: point AbleSet's OSC output at the listener port
        (AbleSet settings) — the bridge cannot auto-configure AbleSet. The
        same snapshot is available as the ``ableton://ableset/state`` resource.
        """
        return json.dumps(_ableset_snapshot())
