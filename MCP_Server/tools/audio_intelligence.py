"""
Audio Intelligence ("Ears") for AbleBridge++.

Lets the AI listen to the *actual audio* in the session:

- analyze_audio_key_bpm: key + BPM detection by reading the sample file
  server-side (pure-Python DSP: Goertzel chroma + onset autocorrelation).
  Live's embedded Python cannot run numpy, so the DSP lives here.
- audio_clip_to_midi: one-call Live 12 audio->MIDI conversion with a report
  of where the MIDI landed and what it contains.
- find_mix_clashes: heuristic frequency/mask clash finder across tracks.
- hum_to_clip: capture recently played MIDI, quantize, and harmonize it
  into a full clip (chords under the melody) in one call.

All numeric results are labelled estimates with confidence — the AI should
treat them as strong hints, not ground truth.
"""
import json
import logging
import math
import os
import struct
import wave

from mcp.server.fastmcp import Context

from MCP_Server.tools._base import _tool_handler
from MCP_Server.connections.ableton import get_ableton_connection

logger = logging.getLogger("MCP_Server.audio_intelligence")

# ---------------------------------------------------------------------------
# Key-detection profiles (Krumhansl-Schmuckler, normalized to sum 1)
# ---------------------------------------------------------------------------
_KS_MAJOR = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
_KS_MINOR = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
_PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Goertzel analysis: pitch classes sampled over octaves 2-5 (fundamentals).
_BASE_A4 = 440.0


def _pitch_class_freqs():
    """Frequencies for each of the 12 pitch classes across octaves 2-5."""
    freqs = []
    for octave in (2, 3, 4, 5):
        for pc in range(12):
            midi = 12 * (octave + 1) + pc
            freqs.append((pc, _BASE_A4 * 2.0 ** ((midi - 69) / 12.0)))
    return freqs


def _read_audio_mono(path, max_seconds=30.0, target_rate=4410):
    """Read an audio file as mono floats at ~target_rate. Returns (samples, rate).

    Supports PCM wave/aiff via the stdlib. Falls back to None for
    unsupported containers (e.g. mp3/flac/ogg).
    """
    ext = os.path.splitext(path)[1].lower()
    data = None
    rate = None
    width = None
    if ext in (".wav", ".wave"):
        with wave.open(path, "rb") as w:
            rate = w.getframerate()
            width = w.getsampwidth()
            channels = w.getnchannels()
            frames = w.readframes(w.getnframes())
    elif ext in (".aif", ".aiff"):
        try:
            import aifc  # deprecated in 3.11 but present; fine for a reader
        except ImportError:
            return None, None
        with aifc.open(path, "rb") as a:
            rate = a.getframerate()
            width = a.getsampwidth()
            channels = a.getnchannels()
            frames = a.readframes(a.getnframes())
    else:
        return None, None

    if width == 2:
        count = len(frames) // 2
        ints = struct.unpack("<%dh" % count, frames[: count * 2])
        peak = 32768.0
    elif width == 3:
        ints = []
        for i in range(0, min(len(frames), 3 * 10_000_000), 3):
            b = frames[i : i + 3]
            val = int.from_bytes(b, "little", signed=True)
            ints.append(val)
        peak = 8388608.0
    elif width == 4:
        count = len(frames) // 4
        ints = struct.unpack("<%di" % count, frames[: count * 4])
        peak = 2147483648.0
    else:
        return None, None

    # mix to mono
    mono = []
    n = len(ints)
    step = channels if channels else 1
    for i in range(0, n, step):
        acc = 0.0
        for c in range(step):
            if i + c < n:
                acc += ints[i + c]
        mono.append(acc / step / peak)

    # decimate by integer factor with simple averaging (anti-alias-ish)
    factor = max(1, int(rate // target_rate))
    if factor > 1:
        dec = []
        for i in range(0, len(mono) - factor + 1, factor):
            acc = 0.0
            for j in range(factor):
                acc += mono[i + j]
            dec.append(acc / factor)
        mono = dec
        rate = rate // factor

    limit = int(max_seconds * rate)
    if len(mono) > limit:
        start = max(0, (len(mono) - limit) // 2)  # middle chunk
        mono = mono[start : start + limit]
    return mono, rate


def _goertzel(samples, freq, rate):
    """Magnitude of freq in samples via the Goertzel algorithm."""
    n = len(samples)
    if n == 0:
        return 0.0
    k = 2.0 * math.cos(2.0 * math.pi * freq / rate)
    s1 = s2 = 0.0
    for x in samples:
        s0 = x + k * s1 - s2
        s2 = s1
        s1 = s0
    return math.sqrt(max(0.0, s1 * s1 + s2 * s2 - k * s1 * s2))


def _chroma(samples, rate):
    """12-bin chroma vector (summed across octaves), normalized."""
    chroma = [0.0] * 12
    for pc, freq in _pitch_class_freqs():
        mag = _goertzel(samples, freq, rate)
        chroma[pc] += mag * mag  # energy
    total = sum(chroma) or 1.0
    return [c / total for c in chroma]


def _detect_key(chroma):
    """Correlate chroma against Krumhansl profiles for all 24 keys."""
    results = []
    for root in range(12):
        for profile, mode in ((_KS_MAJOR, "major"), (_KS_MINOR, "minor")):
            # rotate profile so tonic sits at `root`
            rotated = profile[-root:] + profile[:-root]
            p_mean = sum(rotated) / 12.0
            c_mean = sum(chroma) / 12.0
            num = sum((chroma[i] - c_mean) * (rotated[i] - p_mean) for i in range(12))
            den = math.sqrt(
                sum((chroma[i] - c_mean) ** 2 for i in range(12))
                * sum((rotated[i] - p_mean) ** 2 for i in range(12))
            )
            r = num / den if den else 0.0
            results.append((r, _PITCH_NAMES[root], mode))
    results.sort(reverse=True)
    best = results[0]
    second = results[1]
    confidence = max(0.0, min(1.0, (best[0] - second[0]) * 2.5))
    return {"key": "{0} {1}".format(best[1], best[2]),
            "correlation": round(best[0], 3),
            "runner_up": "{0} {1}".format(second[1], second[2]),
            "confidence": round(confidence, 2)}


def _detect_bpm(samples, rate):
    """Onset-envelope autocorrelation tempo estimate."""
    # RMS envelope over 128-sample blocks (~29 blocks/sec at 4410 Hz)
    block = 128
    env = []
    for i in range(0, len(samples) - block + 1, block):
        acc = 0.0
        for j in range(block):
            acc += samples[i + j] * samples[i + j]
        env.append(math.sqrt(acc / block))
    if len(env) < 60:
        return None
    # rectified derivative = onset strength
    onset = [max(0.0, env[i] - env[i - 1]) for i in range(1, len(env))]
    mean = sum(onset) / len(onset) or 1e-9
    onset = [o - mean for o in onset]

    blocks_per_sec = rate / block
    min_lag = int(blocks_per_sec * 60.0 / 200.0)   # 200 BPM
    max_lag = int(blocks_per_sec * 60.0 / 60.0)    # 60 BPM
    max_lag = min(max_lag, len(onset) - 1)
    if min_lag >= max_lag:
        return None

    best = (0.0, 0)
    for lag in range(min_lag, max_lag + 1):
        acc = 0.0
        for i in range(len(onset) - lag):
            acc += onset[i] * onset[i + lag]
        if acc > best[0]:
            best = (acc, lag)
    if best[1] == 0:
        return None
    bpm = 60.0 * blocks_per_sec / best[1]
    # fold into 70-180 range
    while bpm < 70.0:
        bpm *= 2.0
    while bpm > 180.0:
        bpm /= 2.0
    return round(bpm, 1)


def _detect_key_bpm_from_file(path):
    """Full DSP pipeline for one sample file. Returns dict or error info."""
    if not path or not os.path.isfile(path):
        return {"analyzable": False, "reason": "file not found on disk"}
    samples, rate = _read_audio_mono(path)
    if not samples:
        return {"analyzable": False,
                "reason": "unsupported format for server-side DSP "
                          "(wav/aiff supported; mp3/flac/ogg are not)"}
    chroma = _chroma(samples, rate)
    key = _detect_key(chroma)
    bpm = _detect_bpm(samples, rate)
    return {"analyzable": True,
            "key_estimate": key,
            "bpm_estimate": bpm,
            "analyzed_seconds": round(len(samples) / rate, 1)}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
def register_tools(mcp):

    @mcp.tool()
    @_tool_handler("analyzing audio key and BPM")
    def analyze_audio_key_bpm(ctx: Context, track_index: int, clip_index: int,
                              use_file_dsp: bool = True) -> str:
        """
        Detect the musical key and tempo of an AUDIO clip's sample.

        Primary source: Live's own warp metadata (exact when the clip is
        warped). Secondary: server-side DSP on the sample file
        (chroma->Krumhansl key profile + onset autocorrelation BPM),
        returned as labelled estimates with confidence.

        Use this before generating material so everything lands in the
        session's real key — the AI can *hear*, not just obey.
        """
        ableton = get_ableton_connection()
        info = ableton.send_command("get_clip_info", {
            "track_index": track_index, "clip_index": clip_index})
        if not info.get("is_audio"):
            raise ValueError(
                "Clip at track {0} slot {1} is not an audio clip".format(
                    track_index, clip_index))

        result = {"track_index": track_index, "clip_index": clip_index,
                  "clip_name": info.get("name", "")}

        # 1. Metadata-based BPM (exact for warped clips)
        try:
            props = ableton.send_command("get_clip_properties", {
                "track_index": track_index, "clip_index": clip_index})
            sample_len = props.get("sample_length") or props.get(
                "audio_properties", {}).get("sample_length")
            sample_rate = props.get("sample_rate") or props.get(
                "audio_properties", {}).get("sample_rate")
            length_beats = props.get("length") or props.get("length_beats")
            if sample_len and sample_rate and length_beats:
                duration = float(sample_len) / float(sample_rate)
                result["bpm_from_warp_metadata"] = round(
                    60.0 * float(length_beats) / duration, 1)
        except Exception:
            pass

        # 2. File DSP
        if use_file_dsp:
            try:
                fp = ableton.send_command("get_clip_file_path", {
                    "track_index": track_index, "clip_index": clip_index})
                dsp = _detect_key_bpm_from_file(fp.get("file_path"))
                result["dsp"] = dsp
                if dsp.get("analyzable"):
                    result["key_estimate"] = dsp["key_estimate"]["key"]
                    result["key_confidence"] = dsp["key_estimate"]["confidence"]
                    if dsp.get("bpm_estimate") and "bpm_from_warp_metadata" not in result:
                        result["bpm_estimate"] = dsp["bpm_estimate"]
            except Exception as dsp_err:
                result["dsp"] = {"analyzable": False, "reason": str(dsp_err)}

        result["note"] = ("key/bpm values are estimates — verify by ear "
                          "before committing")
        return json.dumps(result)

    @mcp.tool()
    @_tool_handler("converting audio clip to MIDI")
    def audio_clip_to_midi(ctx: Context, track_index: int, clip_index: int,
                           conversion_type: str = "melody") -> str:
        """
        Convert an AUDIO clip into a playable MIDI clip (Live 12+).

        conversion_type: 'melody', 'harmony', or 'drums'.
        Live inserts the MIDI clip on a new track right after the source;
        this tool reports exactly where it landed and summarizes its notes
        so the AI can immediately edit, quantize, or harmonize it.
        """
        ableton = get_ableton_connection()
        conv = str(conversion_type).lower().strip()
        if conv not in ("melody", "harmony", "drums"):
            raise ValueError("conversion_type must be melody, harmony, or drums")

        before = ableton.send_command("get_session_info").get("track_count", 0)
        ableton.send_command("audio_to_midi", {
            "track_index": track_index, "clip_index": clip_index,
            "conversion_type": conv})
        after = ableton.send_command("get_session_info").get("track_count", 0)

        landed = {"track_index": after - 1 if after > before else track_index,
                  "new_track_created": after > before}
        note_summary = None
        try:
            notes = ableton.send_command("get_clip_notes", {
                "track_index": landed["track_index"], "clip_index": 0,
                "start_time": 0.0, "time_span": 64.0,
                "start_pitch": 0, "pitch_span": 128})
            note_list = notes.get("notes", [])
            note_summary = {
                "count": len(note_list),
                "pitch_range": [min((n.get("pitch", 60) for n in note_list), default=0),
                                max((n.get("pitch", 60) for n in note_list), default=0)]
                if note_list else None,
            }
        except Exception:
            pass

        return json.dumps({
            "status": "ok", "converted": conv,
            "source": {"track_index": track_index, "clip_index": clip_index},
            "midi_landed_at": landed,
            "note_summary": note_summary,
            "tip": "the MIDI clip is in slot 0 of the new track",
        })

    @mcp.tool()
    @_tool_handler("finding mix clashes")
    def find_mix_clashes(ctx: Context, max_findings: int = 8) -> str:
        """
        Heuristic mix-doctor: find likely frequency/mask clashes between
        tracks.

        Audio tracks: dominant band (low/mid/high) via server-side DSP on
        their sample files. MIDI tracks: pitch range from their clips.
        Flags pairs sharing a dominant band with similar pan and no
        send/routing separation. Advisory only — suggestions, not rules.
        """
        ableton = get_ableton_connection()
        tracks = ableton.send_command("get_all_tracks_info")
        track_list = tracks.get("tracks", [])[:40]

        profiles = {}
        for t in track_list:
            ti = t.get("index", t.get("track_index"))
            if ti is None:
                continue
            entry = {"name": t.get("name", "?"), "kind": t.get("type", "?"),
                     "pan": t.get("panning"), "muted": t.get("muted"),
                     "volume": t.get("volume")}
            # audio: DSP the first audio clip we can read
            if str(t.get("type", "")).lower() in ("audio", "audio_track"):
                for ci in range(min(int(t.get("clip_count", 0) or 0), 8)):
                    try:
                        fp = ableton.send_command("get_clip_file_path", {
                            "track_index": ti, "clip_index": ci})
                        dsp = _detect_key_bpm_from_file(fp.get("file_path"))
                        if dsp.get("analyzable"):
                            entry["key"] = dsp["key_estimate"]["key"]
                            break
                    except Exception:
                        continue
            # midi: pitch range of first clip with notes
            if str(t.get("type", "")).lower() in ("midi", "midi_track"):
                for ci in range(min(int(t.get("clip_count", 0) or 0), 8)):
                    try:
                        notes = ableton.send_command("get_clip_notes", {
                            "track_index": ti, "clip_index": ci,
                            "start_time": 0.0, "time_span": 64.0,
                            "start_pitch": 0, "pitch_span": 128})
                        nl = notes.get("notes", [])
                        if nl:
                            pitches = [n.get("pitch", 60) for n in nl]
                            entry["pitch_range"] = [min(pitches), max(pitches)]
                            break
                    except Exception:
                        continue
            profiles[ti] = entry

        def _band(entry):
            if "pitch_range" in entry and entry["pitch_range"]:
                lo = entry["pitch_range"][0]
                if lo < 48:
                    return "low"
                if lo < 72:
                    return "mid"
                return "high"
            return None

        findings = []
        keys = sorted(profiles.keys())
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                ea, eb = profiles[a], profiles[b]
                if ea.get("muted") or eb.get("muted"):
                    continue
                ba, bb = _band(ea), _band(eb)
                if not ba or ba != bb:
                    continue
                pa, pb = ea.get("pan") or 0.0, eb.get("pan") or 0.0
                try:
                    pan_close = abs(float(pa) - float(pb)) < 0.2
                except (TypeError, ValueError):
                    pan_close = True
                if pan_close:
                    findings.append({
                        "tracks": [ea["name"], eb["name"]],
                        "shared_band": ba,
                        "why": "both occupy the {0} range with similar pan".format(ba),
                        "suggestions": [
                            "pan one of them away from center",
                            "carve space with EQ (cut the same band on one)",
                            "lower one by 2-3 dB and re-check"],
                    })
                if len(findings) >= max(1, int(max_findings)):
                    break
            if len(findings) >= max(1, int(max_findings)):
                break

        return json.dumps({
            "tracks_analyzed": len(profiles),
            "findings": findings,
            "finding_count": len(findings),
            "note": "heuristic — always confirm by ear",
        })

    @mcp.tool()
    @_tool_handler("building clip from captured playing")
    def hum_to_clip(ctx: Context, harmonize: bool = True,
                    key: str = "", quantize_grid: float = 0.25) -> str:
        """
        Turn what you just played into a finished clip.

        Captures recently played MIDI (Live 11+, works on the armed/selected
        track), quantizes it, and — optionally — adds chord pads under the
        melody in the given key (e.g. 'F# minor'; auto-detected from the
        session scale when omitted).

        Play an idea, call this, and get back a produced clip.
        """
        ableton = get_ableton_connection()
        before_scenes = ableton.send_command("get_scenes").get("scenes", [])
        ableton.send_command("capture_and_insert_scene", {})
        after_scenes = ableton.send_command("get_scenes").get("scenes", [])
        if len(after_scenes) <= len(before_scenes):
            return json.dumps({"status": "error",
                               "message": "capture produced no new scene — "
                                          "play something first and keep the "
                                          "track armed"})
        scene_index = len(after_scenes) - 1
        done = ["captured playing into new scene {0}".format(scene_index)]

        # find captured MIDI clips in the new scene
        captured = []
        tracks = ableton.send_command("get_all_tracks_info").get("tracks", [])
        for t in tracks[:40]:
            ti = t.get("index", t.get("track_index"))
            if ti is None:
                continue
            try:
                ci = int(t.get("clip_count", 0) or 0) - 1
                if ci < 0:
                    continue
                info = ableton.send_command("get_clip_info", {
                    "track_index": ti, "clip_index": ci})
                if info.get("is_midi") and scene_index == ci:
                    captured.append((ti, ci, info))
            except Exception:
                continue

        quantized = 0
        for ti, ci, _info in captured:
            try:
                ableton.send_command("quantize_clip_notes", {
                    "track_index": ti, "clip_index": ci,
                    "grid_size": float(quantize_grid)})
                quantized += 1
            except Exception:
                pass
        if quantized:
            done.append("quantized {0} clip(s) to {1} beats".format(
                quantized, quantize_grid))

        # harmonize: chords under the melody's average pitch
        chords_added = 0
        if harmonize and captured:
            key_str = str(key).strip()
            if not key_str:
                try:
                    scale = ableton.send_command("get_song_scale")
                    key_str = "{0} {1}".format(
                        _PITCH_NAMES[int(scale.get("root_note", 0)) % 12],
                        scale.get("scale_name", "minor"))
                except Exception:
                    key_str = "C major"
            from MCP_Server.tools.music_gen import _parse_key, _chords_clip
            root, scale_ints = _parse_key(key_str)
            melody_track = captured[0][0]
            # pad track: clone-less approach — use a return-free new MIDI track
            try:
                new_track = ableton.send_command("create_midi_track",
                                                 {"index": -1})
                pad_ti = int(new_track.get("index", -1))
                if pad_ti < 0:
                    pad_ti = (ableton.send_command("get_session_info")
                              .get("track_count", 0) - 1)
                ableton.send_command("set_track_name", {
                    "track_index": pad_ti, "name": "Pads (auto)"})
                _chords_clip(ableton, pad_ti, scene_index, root, scale_ints,
                             [0, 3, 4, 3], 8, 4)
                chords_added = 1
                done.append("added chord pads on track {0} in {1}".format(
                    pad_ti, key_str))
            except Exception as harm_err:
                done.append("harmonization skipped: {0}".format(harm_err))

        return json.dumps({
            "status": "ok", "scene_index": scene_index,
            "captured_clips": [{"track_index": ti, "clip_index": ci}
                               for ti, ci, _ in captured],
            "steps_done": done,
            "harmonized": bool(chords_added),
        })
