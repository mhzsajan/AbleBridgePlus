"""
Doctor & monitoring tools for AbleBridgePlus.

Self-diagnosis: one `doctor` call that checks everything that has ever
broken in the field — control-surface connection, script version drift,
port conflicts, browser-cache staleness — in plain language with fixes.
Plus a session integrity report and a lightweight session watcher.
"""
import logging
import os
import socket
import time
from typing import Any, Dict, List

from mcp.server.fastmcp import Context

from MCP_Server.tools._base import _tool_handler
from MCP_Server.connections.ableton import get_ableton_connection
import MCP_Server.state as state

logger = logging.getLogger("MCP_Server.doctor")

ABridge_PORT = 9877

# Bumped with the release; the remote script must report the same version
# or `doctor` flags an install/repo drift (a failure mode we have hit).
EXPECTED_SCRIPT_VERSION = "0.8.0"


def register_tools(mcp):

    @mcp.tool()
    @_tool_handler("running doctor")
    def doctor(ctx: Context, deep: bool = False) -> str:
        """
        Full health check of the AbleBridgePlus stack. Checks: Ableton
        reachable, round-trip latency, remote-script version drift vs this
        server, M4L bridge status, browser cache age, and (with
        deep=true) Ableton's own log for script errors. Returns plain
        language results with a suggested fix for every problem found.
        """
        import json as _json
        checks: List[Dict[str, Any]] = []

        def _add(check: str, ok: bool, detail: str, fix: str = ""):
            checks.append({"check": check, "ok": ok, "detail": detail, "fix": fix})

        # 1. TCP reachable + round trip
        sock_ok, latency_ms = False, None
        try:
            start = time.time()
            s = socket.create_connection(("127.0.0.1", ABridge_PORT), timeout=3)
            s.close()
            latency_ms = round((time.time() - start) * 1000, 1)
            sock_ok = True
        except Exception as e:
            _add("ableton_reachable", False, "port {0} not answering: {1}".format(
                ABridge_PORT, e),
                 "Start Ableton and confirm the AbleBridgePlus control surface "
                 "is selected (Preferences > Link/Tempo/MIDI).")
        if sock_ok:
            _add("ableton_reachable", True,
                 "TCP {0} up, connect {1}ms".format(ABridge_PORT, latency_ms))

            # 2. Command round-trip + version drift
            try:
                ableton = get_ableton_connection()
                info = ableton.send_command("get_session_info")
                _add("command_roundtrip", True,
                     "tempo={0} track_count={1}".format(
                         info.get("tempo"), info.get("track_count")))
                reported = info.get("version") or info.get("script_version")
                if reported and reported != EXPECTED_SCRIPT_VERSION:
                    _add("version_match", False,
                         "script reports {0}, server expects {1}".format(
                             reported, EXPECTED_SCRIPT_VERSION),
                         "Reinstall the remote script from the current release "
                         "and restart Ableton.")
                else:
                    _add("version_match", True,
                         "script version aligned" + (" ({0})".format(reported)
                                                     if reported else
                                                     " (script does not report a "
                                                     "version yet)"))
            except Exception as e:
                _add("command_roundtrip", False, str(e),
                     "The control surface may have failed to load. Check "
                     "Ableton's Log.txt for AbleBridgePlus tracebacks.")

        # 3. M4L bridge (optional feature)
        m4l = state.m4l_connection
        if m4l is not None:
            try:
                # `x or True` is unconditionally True, so this check reported a
                # healthy bridge even with no socket, telling a user chasing
                # dead M4L devices that everything was fine.
                connected = bool(getattr(m4l, "sock", None)) or \
                    bool(getattr(m4l, "_connected", False))
                _add("m4l_bridge", connected,
                     ("connected — send {0}/recv {1} (only needed for M4L-device "
                      "features)".format(getattr(m4l, "send_port", "?"),
                                         getattr(m4l, "recv_port", "?"))
                      if connected else
                      "not connected (M4L-device features unavailable)"),
                     None if connected else
                     "Expected if you do not use Max for Live devices. If you "
                     "DO use them, check the AbleBridgePlus Max device is loaded.")
            except Exception as e:
                _add("m4l_bridge", False, str(e),
                     "Ignore if you do not use Max for Live devices.")

        # 4. Browser cache freshness
        with state.browser_cache_lock:
            count = len(state.browser_cache_flat)
            ts = state.browser_cache_timestamp
            populating = state.browser_cache_populating
        age = time.time() - ts if ts else None
        if populating:
            _add("browser_cache", True, "background scan in progress")
        elif count == 0:
            _add("browser_cache", False, "empty — browser search unavailable",
                 "Call refresh_browser_cache once Ableton is running.")
        elif age and age > 3600:
            _add("browser_cache", True, "{0} items, {1:.0f}h old".format(
                count, age / 3600),
                 "Consider refresh_browser_cache after installing packs.")
        else:
            _add("browser_cache", True,
                 "{0} items, refreshed {1:.0f}s ago".format(count, age or 0))

        # 5. Deep: scan Ableton's Log.txt for script errors
        if deep:
            log_dir = os.path.join(os.environ.get("APPDATA", ""), "Ableton")
            found_err = None
            try:
                candidates = []
                for root, _dirs, files in os.walk(log_dir):
                    if "Log.txt" in files:
                        candidates.append(os.path.join(root, "Log.txt"))
                if candidates:
                    latest = max(candidates, key=os.path.getmtime)
                    with open(latest, "r", encoding="utf-8",
                              errors="ignore") as f:
                        tail = f.readlines()[-400:]
                    for line in tail:
                        if "AbleBridgePlus" in line and \
                           ("Traceback" in line or "Error" in line):
                            found_err = line.strip()[:160]
                            break
                    _add("ableton_log_scan", True,
                         "scanned {0}".format(os.path.basename(
                             os.path.dirname(latest))) +
                         (" — no AbleBridgePlus errors" if not found_err else ""))
            except Exception as e:
                _add("ableton_log_scan", False, str(e), "")
            if found_err:
                _add("ableton_log_errors", False, found_err,
                     "See Ableton's Log.txt; report the traceback if it persists.")

        problems = [c for c in checks if not c["ok"]]
        import json as _json
        return _json.dumps({
            "status": "healthy" if not problems else "issues_found",
            "problems": len(problems),
            "checks": checks,
        }, default=str)

    @mcp.tool()
    @_tool_handler("scanning session integrity")
    def session_integrity_report(ctx: Context) -> str:
        """
        Audit the current Live set for common problems: tracks with no
        output routing, clips sitting on muted tracks, armed-but-muted
        traps, tracks with instruments but no clips used yet, clips with
        missing loop points, master volume extremes. Read-only.
        """
        ableton = get_ableton_connection()
        findings: List[Dict[str, Any]] = []
        all_tracks = ableton.send_command("get_all_tracks_info")
        for t in all_tracks.get("tracks", []):
            idx = t.get("index")
            name = t.get("name")
            try:
                info = ableton.send_command("get_track_info", {"track_index": idx})
            except Exception:
                continue
            routing = info.get("output_routing_type") or info.get("output_routing")
            if routing is not None and routing in ("", "No Output"):
                findings.append({"severity": "high", "track": name,
                                 "issue": "no output routing"})
            if t.get("arm") and t.get("mute"):
                findings.append({"severity": "high", "track": name,
                                 "issue": "armed but muted (you will not hear "
                                          "recording input)"})
            if t.get("solo") and t.get("mute"):
                findings.append({"severity": "medium", "track": name,
                                 "issue": "soloed and muted at once"})
            clips = [s.get("clip") for s in info.get("clip_slots", [])
                     if s.get("clip")]
            if info.get("is_midi_track") and not clips:
                findings.append({"severity": "info", "track": name,
                                 "issue": "MIDI track has no clips"})
            for clip in clips:
                if clip.get("looping") is False and \
                   (clip.get("end", 0) - clip.get("start", 0)) > 0 and \
                   clip.get("is_midi"):
                    findings.append({"severity": "low", "track": name,
                                     "clip": clip.get("name"),
                                     "issue": "looping disabled"})
        import json as _json
        return _json.dumps({
            "status": "clean" if not findings else "findings",
            "issue_count": len(findings), "findings": findings,
        }, default=str)

    @mcp.tool()
    @_tool_handler("watching session")
    def watch_session(ctx: Context) -> str:
        """
        One-shot live snapshot for monitoring: transport state, currently
        playing clip slots, track meters (post-gain levels), tempo and
        record status. Call repeatedly (it is cheap) to watch a performance
        or mixing pass — the AI equivalent of glancing at the screen.
        """
        ableton = get_ableton_connection()
        transport = ableton.send_command("get_song_transport")
        playing = ableton.send_command("get_playing_clips")
        meters = ableton.send_command("get_track_meters")
        import json as _json
        return _json.dumps({
            "transport": transport,
            "playing_clips": playing.get("playing_clips", playing),
            "meters": meters.get("tracks", meters) if isinstance(meters, dict)
            else meters,
        }, default=str)
