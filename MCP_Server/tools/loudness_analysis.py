"""Loudness analysis tools for AbleBridgePlus (v0.7 "Ears v2").

Per-clip LUFS measurement and a mix-level audit that flags clips likely
to jump out of (or get buried in) the mix. Built on the pure-Python
BS.1770-4 approximation in MCP_Server/loudness.py — mono, gated, honest
about its precision (see that module's docstring).

Tools:
- measure_clip_loudness: integrated/momentary LUFS for one audio clip in
  the set, with a gain-to-target hint (streaming −14 LUFS by default).
- audit_mix_loudness: measures the first audio clip of every track and
  classifies the set: jumping out (>= +3 dB vs median), buried
  (<= -6 dB), balanced. This is the "who will jump out" report.
"""
import json
import logging
import os
from typing import Any, Dict, List

from mcp.server.fastmcp import Context

from MCP_Server.tools._base import _tool_handler
from MCP_Server.connections.ableton import get_ableton_connection
from MCP_Server.validation import _validate_index
from MCP_Server.loudness import measure_loudness, audit_loudness_stats
from MCP_Server.tools.audio_intelligence import _read_audio_mono

logger = logging.getLogger(__name__)

# decode rate for loudness (11 kHz: captures the energy that matters for
# integrated loudness while keeping pure-Python filtering fast)
_LOUDNESS_RATE = 11025
_MAX_MEASURE_SECONDS = 15.0


def _measure_path(path: str, label: str, max_seconds: float = _MAX_MEASURE_SECONDS) -> Dict[str, Any]:
    if not path or not os.path.isfile(path):
        raise ValueError("sample file not found on disk: " + str(path))
    samples, rate = _read_audio_mono(path, max_seconds=max_seconds,
                                     target_rate=_LOUDNESS_RATE)
    if not samples:
        raise ValueError("unreadable or unsupported sample: " + str(path))
    return measure_loudness(samples, rate, label=label)


def _audio_clip_path(conn, track_index: int, clip_index: int) -> str:
    """Resolve an audio clip's sample path; raises if none (honest errors)."""
    fp = conn.send_command("get_clip_file_path",
                           {"track_index": track_index,
                            "clip_index": clip_index})
    path = fp.get("file_path")
    if not path:
        raise ValueError("clip at track %d slot %d has no sample file path "
                         "(MIDI clip, or recorded/unsaved audio)"
                         % (track_index, clip_index))
    return path


def register_tools(mcp):
    @mcp.tool()
    @_tool_handler("measuring clip loudness")
    def measure_clip_loudness(ctx: Context, track_index: int,
                              clip_index: int) -> str:
        """
        Integrated LUFS (BS.1770-4 gated approximation, mono) for one
        AUDIO clip in the set, plus momentary max/min, loudness range,
        duration and a gain-to-target hint (streaming target -14 LUFS).

        Use it to put numbers on "this clip is way louder than the rest"
        before it happens in the mix. Relative differences between clips
        are reliable; absolutes may differ a fraction of a dB from stereo
        reference meters.
        """
        _validate_index(track_index, "track_index")
        _validate_index(clip_index, "clip_index")
        conn = get_ableton_connection()
        path = _audio_clip_path(conn, track_index, clip_index)
        result = _measure_path(path, label="track %d slot %d" % (track_index, clip_index))
        result["clip"] = {"track_index": track_index, "clip_index": clip_index,
                          "file": str(path).replace("\\", "/").rsplit("/", 1)[-1]}
        return json.dumps(result, indent=2)

    @mcp.tool()
    @_tool_handler("auditing mix loudness")
    def audit_mix_loudness(ctx: Context, max_seconds_per_clip: float = 10.0) -> str:
        """
        Measure the first audio clip of every track and classify the mix:
        which clips will JUMP OUT (>= +3 dB above the set's median loudness),
        which are BURIED (<= -6 dB), which are balanced. Median-based so a
        single screaming clip can't skew the reference.

        The "why does my mix feel lumpy" report — run it before mixing and
        again after level rides. Skips MIDI clips and clips without sample
        files (reported per track). Mono BS.1770-4 approximation.
        """
        conn = get_ableton_connection()
        try:
            seconds = max(2.0, min(float(max_seconds_per_clip), 20.0))
        except (TypeError, ValueError):
            raise ValueError("max_seconds_per_clip must be a number")
        session = conn.send_command("get_session_info")
        track_count = int(session.get("track_count", 0))
        if track_count < 1:
            raise ValueError("the set has no tracks to audit")

        measurements: List[Dict[str, Any]] = []
        skipped: List[Dict[str, Any]] = []
        for i in range(track_count):
            try:
                info = conn.send_command("get_track_info", {"track_index": i})
            except Exception as e:
                skipped.append({"track_index": i, "reason": str(e)})
                continue
            track_name = info.get("name") or ("track %d" % i)
            found = False
            for slot_idx, slot in enumerate(info.get("clip_slots", []) or []):
                if not (slot.get("has_clip") or slot.get("clip")):
                    continue
                try:
                    fp = conn.send_command("get_clip_file_path",
                                           {"track_index": i,
                                            "clip_index": slot_idx})
                    path = fp.get("file_path")
                    if not path:
                        continue
                    m = _measure_path(path, label=track_name,
                                      max_seconds=seconds)
                    m["track_index"] = i
                    m["clip_index"] = slot_idx
                    measurements.append(m)
                    found = True
                    break  # first audio clip per track
                except Exception:
                    continue  # MIDI clip or unreadable: try next slot
            if not found:
                skipped.append({"track_index": i, "track_name": track_name,
                                "reason": "no audio clip with a sample file"})

        if len(measurements) < 2:
            return json.dumps({
                "status": "error",
                "message": "audit needs at least 2 audio clips with sample "
                           "files; found %d" % len(measurements),
                "measurements": measurements,
                "skipped": skipped,
            }, indent=2)

        audit = audit_loudness_stats(measurements)
        return json.dumps({
            "status": "ok",
            "audit": audit,
            "measurements": [
                {k: m[k] for k in ("source", "integrated_lufs",
                                   "momentary_max_lufs", "loudness_range_lu",
                                   "duration_s", "gain_to_target_db")}
                for m in measurements
            ],
            "skipped": skipped,
            "note": "mono BS.1770-4 approximation; deltas between clips are "
                    "the actionable numbers, not absolute meter values",
        }, indent=2)
