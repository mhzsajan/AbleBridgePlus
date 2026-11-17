"""Live-show OSC/UDP bridge tools (v0.9.0).

Two jobs live here:

1. A *generic* send path out of the bridge to any OSC/UDP target on the
   show network — Behringer WING (192.168.1.3:2223), TouchDesigner, an
   AbleSet Canvas "raw external OSC target" button, a lighting desk, etc.
   ``pythonosc`` (``python-osc`` in pyproject.toml) is the only dependency;
   these tools do not need Ableton at all.

2. Thin server-side adapters over existing read-only Ableton commands
   (``get_song_transport``, ``get_master_meters``) plus MCP wrappers for the
   three v0.9 remote-script commands. Nothing here introduces a new LOM
   handler — the heavy lifting on the Ableton side already exists.

Locator macros are stored in-process (a module-level dict). Auto-firing a
macro when ``jump_to_locator`` succeeds is intentionally NOT wired here:
that tool lives in ``tools/arrangement.py`` (outside this release's file
ownership), and patching another module's registered tool through private
registry internals would be fragile. Call ``fire_locator_macro`` explicitly
after a successful jump instead.
"""
import json
import logging
import math

from mcp.server.fastmcp import Context

from MCP_Server.tools._base import _tool_handler
from MCP_Server.connections.ableton import get_ableton_connection

try:
    from pythonosc.udp_client import SimpleUDPClient
except ImportError:  # pragma: no cover - dependency is declared in pyproject
    SimpleUDPClient = None

logger = logging.getLogger("AbletonBridge")

# Named OSC macros bound to a locator / section name. Tool calls are
# serialised by _base._ableton_semaphore, so a plain dict is sufficient.
_LOCATOR_MACROS: dict = {}


# ---------------------------------------------------------------------------
# Shared OSC helpers (single implementation, reused by every tool here)
# ---------------------------------------------------------------------------

def _to_args(value):
    """Normalise a scalar or a list into a list of OSC arguments."""
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _send_osc_message(host, port, address, args):
    """Send one OSC message over UDP. Returns {"sent": bool, "error": str|None}."""
    if SimpleUDPClient is None:
        return {"sent": False,
                "error": "python-osc is not installed (python-osc>=1.8.0 required)"}
    try:
        client = SimpleUDPClient(str(host), int(port))
        client.send_message(str(address), list(args))
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
    # Locator-bound macro storage (auto-fire intentionally deferred — see
    # the module docstring; fire explicitly with fire_locator_macro)
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
        messages = _LOCATOR_MACROS.get(locator_name)
        matched = locator_name if messages is not None else None
        if messages is None:
            needle = str(locator_name).lower()
            for key, stored in _LOCATOR_MACROS.items():
                if key.lower() == needle:
                    messages = stored
                    matched = key
                    break
        if messages is None:
            return json.dumps({
                "locator_name": locator_name, "matched": None,
                "count": 0, "sent": 0, "errors": [],
                "note": "no macro registered for this locator",
            })
        result = _send_osc_batch(messages)
        return json.dumps({
            "locator_name": locator_name, "matched": matched,
            "count": result["sent"], "sent": result["sent"],
            "errors": result["errors"], "details": result["details"],
        })
