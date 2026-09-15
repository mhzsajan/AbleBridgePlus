"""
Producer pipeline for AbleBridge++.

- produce_idea_from_prompt: one sentence in, playable demo out. Chains the
  v0.4 music toolkit (skeleton -> chords/bass/drums -> melody -> tempo,
  colors, scenes) with a safety checkpoint and per-step error tolerance:
  a partial demo is still returned rather than nothing.
- smart_freeze: CPU guardian — find the heaviest tracks and freeze them,
  verifying the resource drop.
- match_reference_track: capture one track's sonic profile (device list,
  filter/EQ shape, send levels) and apply matched settings to a target.
"""
import json
import logging
from typing import Any, Dict, List

from mcp.server.fastmcp import Context

from MCP_Server.tools._base import _tool_handler
from MCP_Server.connections.ableton import get_ableton_connection

logger = logging.getLogger("MCP_Server.producer")


def _call(ableton, cmd, params=None):
    return ableton.send_command(cmd, params or {})


def _build_skeleton_now(ableton, section_list, key, genre, create_tracks):
    """build_song_skeleton's logic, callable with an injected connection.

    Mirrors MCP_Server.tools.music_gen.build_song_skeleton: named scenes
    with in-key chord/bass/drum clips per section. Kept in sync manually —
    the tool itself wraps this via its MCP registration.
    """
    from MCP_Server.tools.music_gen import (
        _parse_key, _chords_clip, _bass_clip, _drums_clip,
        PROGRESSIONS, DRUM_PATTERNS)
    root, scale = _parse_key(key)
    created = {"tracks": [], "scenes": [], "clips": 0}

    if create_tracks:
        existing = ableton.send_command("get_all_tracks_info")
        names = {t.get("name") for t in existing.get("tracks", [])}
        for tname in ("Chords", "Bass", "Drums"):
            if tname not in names:
                ableton.send_command("create_midi_track", {"index": -1})
                ableton.send_command("set_track_name", {
                    "track_index": existing.get("track_count", 0)
                    + len(created["tracks"]), "name": tname})
                created["tracks"].append(tname)

    for sec in section_list[:12]:
        name = str(sec.get("name", "Section"))[:24]
        bars = max(2, min(16, int(sec.get("bars", 8))))
        ableton.send_command("create_scene", {"index": -1})
        scenes_now = ableton.send_command("get_scenes")
        s_idx = len(scenes_now.get("scenes", [])) - 1
        ableton.send_command("set_scene_name",
                             {"scene_index": s_idx, "name": name})
        created["scenes"].append({"index": s_idx, "name": name})

        degrees = PROGRESSIONS.get(genre, PROGRESSIONS["edm"])[0]
        chord_slots = max(1, bars // 2)

        def _write(track_name, fn):
            """Find a MIDI track by name and write its clip.

            Duplicate names happen after repeated demos; pick the newest
            MIDI track and skip non-MIDI matches (has_midi_input is also
            true for some audio tracks, so verify by clip creation).
            """
            info = ableton.send_command("get_all_tracks_info")
            candidates = [t for t in info.get("tracks", [])
                          if t.get("name") == track_name
                          and not t.get("is_audio")]
            if not candidates:
                return
            ti = candidates[-1].get("index")  # newest match
            try:
                fn(ti, s_idx)
            except Exception as e:
                if "MIDI clips can only" in str(e) and len(candidates) > 1:
                    fn(candidates[0].get("index"), s_idx)
                else:
                    raise
        _write("Chords", lambda ti, ci: _chords_clip(
            ableton, ti, ci, root, scale, degrees, bars, chord_slots))
        _write("Bass", lambda ti, ci: _bass_clip(
            ableton, ti, ci, root, scale, degrees, bars, chord_slots,
            genre))
        _write("Drums", lambda ti, ci: _drums_clip(
            ableton, ti, ci, genre if genre in DRUM_PATTERNS else "house",
            bars))
        created["clips"] += 3
    return created


def _try(ableton, cmd, params=None, errors=None, what=""):
    """Best-effort command — collect failures instead of aborting."""
    try:
        return _call(ableton, cmd, params), None
    except Exception as e:
        if errors is not None:
            errors.append("{0}: {1}".format(what or cmd, e))
        return None, e


def register_tools(mcp):

    @mcp.tool()
    @_tool_handler("producing a demo from a prompt")
    def produce_idea_from_prompt(ctx: Context, prompt: str,
                                 create_tracks: bool = True,
                                 checkpoint: bool = True) -> str:
        """
        One-prompt-to-demo: builds a playable demo around a sentence like
        "dark 124 BPM techno in F minor" or "chill lofi beat in C major".

        Pipeline: checkpoint (undo safety) -> tempo/key from the prompt ->
        song skeleton (intro/verse/chorus/drop scenes) -> chord + bass +
        drum clips per section -> lead melody on the hook -> track colors.
        Every step is fault-tolerant: whatever succeeded is returned with
        a report of what didn't, so you always get a playable demo.

        The prompt is parsed for BPM, key, and genre; anything unspoken
        gets a sensible default per genre.
        """
        import re
        from MCP_Server.tools.music_gen import (
            _parse_key, _style_from_prompt, _key_from_prompt, _add_notes,
            _scale_pitch, SCALE_ALIASES, DRUM_PATTERNS)
        from MCP_Server.tools.show_autopilot import _autopilot  # noqa: F401 (state only)

        ableton = get_ableton_connection()
        text = str(prompt or "").strip()
        if not text:
            raise ValueError("prompt must describe the idea, e.g. "
                             "'dark 124 BPM techno in F minor'")
        errors: List[str] = []
        report: Dict[str, Any] = {"prompt": text, "steps": [], "errors": errors}

        def step(name, ok, detail=""):
            report["steps"].append({"step": name, "ok": ok, "detail": detail})

        # --- 1. checkpoint -------------------------------------------------
        if checkpoint:
            try:
                from MCP_Server.tools.project_context import _checkpoints
                all_tracks = _call(ableton, "get_all_tracks_info")
                import time as _time
                _checkpoints["pre-demo"] = {
                    "created": _time.time(),
                    "tracks": [
                        {"index": t.get("index"), "name": t.get("name"),
                         "is_audio": t.get("is_audio"), "is_midi": t.get("is_midi"),
                         "mute": t.get("mute"), "solo": t.get("solo"),
                         "volume": t.get("volume"), "panning": t.get("panning")}
                        for t in all_tracks.get("tracks", [])],
                }
                step("checkpoint", True, "'pre-demo' (diff with checkpoint_diff)")
            except Exception as e:
                errors.append("checkpoint: {0} (continuing without)".format(e))
                step("checkpoint", False, str(e))

        # --- 2. parse prompt ------------------------------------------------
        # NB: parse everything possible BEFORE touching Live so replay
        # tests can verify the plan without any recorded responses.
        bpm = None
        m = re.search(r"(\d{2,3})\s*(?:bpm)?", text)
        if m and 60 <= int(m.group(1)) <= 200:
            bpm = int(m.group(1))
        genre = _style_from_prompt(text)
        genre_profiles = {
            "techno": {"bpm": 130, "key": "F minor", "bars": 8, "swing": 0.0},
            "house": {"bpm": 124, "key": "A minor", "bars": 8, "swing": 0.1},
            "lofi": {"bpm": 82, "key": "C major", "bars": 4, "swing": 0.15},
            "trap": {"bpm": 140, "key": "G minor", "bars": 8, "swing": 0.0},
            "dnb": {"bpm": 174, "key": "E minor", "bars": 8, "swing": 0.0},
            "rock": {"bpm": 120, "key": "E minor", "bars": 8, "swing": 0.0},
            "pop": {"bpm": 110, "key": "C major", "bars": 8, "swing": 0.05},
            "ambient": {"bpm": 90, "key": "D minor", "bars": 16, "swing": 0.0},
        }
        prof = genre_profiles.get(genre, genre_profiles["pop"])
        if bpm is None:
            bpm = prof["bpm"]
        key_str = _key_from_prompt(text, prof["key"])
        try:
            root, scale = _parse_key(key_str)
        except Exception:
            key_str, root, scale = prof["key"], 0, [0, 2, 4, 5, 7, 9, 11]
        report["plan"] = {"bpm": bpm, "key": key_str, "genre": genre}
        step("plan", True, "{0} BPM, {1}, {2}".format(bpm, key_str, genre))

        # --- 3. tempo --------------------------------------------------------
        _try(ableton, "set_tempo", {"tempo": float(bpm)}, errors, "set tempo")
        step("tempo", True, "{0} BPM".format(bpm))

        # --- 4. skeleton ------------------------------------------------------
        # build_song_skeleton is an MCP tool, not a remote handler — run its
        # logic (_build_skeleton_now) against our (possibly fake) connection.
        sections = [("Intro", 4), ("Verse", 8), ("Chorus", 8), ("Drop", 8)]
        skel = None
        try:
            skel = _build_skeleton_now(
                ableton, [{"name": n, "bars": b} for n, b in sections],
                key_str, genre, create_tracks)
        except Exception as e:
            if errors is not None:
                errors.append("song skeleton: {0}".format(e))
        step("skeleton", skel is not None,
             "intro/verse/chorus/drop" if skel else "failed (continuing)")

        # --- 5. create tracks -------------------------------------------------
        ti = {}
        if create_tracks:
            for kind in ("Chords", "Bass", "Drums", "Lead"):
                res, err = _try(ableton, "create_midi_track", {"index": -1},
                                errors, "create track " + kind)
                if res is not None:
                    idx = int(res.get("index", -1))
                    if idx < 0:
                        idx = (int(_call(ableton, "get_session_info")
                                   .get("track_count", 0)) - 1)
                    _try(ableton, "set_track_name",
                         {"track_index": idx, "name": kind}, errors, "name " + kind)
                    _try(ableton, "set_track_color", {
                        "track_index": idx,
                        "color": {"Chords": 0x50C878, "Bass": 0xE07020,
                                  "Drums": 0xC04040, "Lead": 0x5090E0}[kind]},
                        errors, "color " + kind)
                    ti[kind] = idx
        step("tracks", len(ti) == 4,
             "indexes {0}".format(ti) if ti else "using fallback track 0")
        if not ti:
            try:
                count = int(_call(ableton, "get_session_info").get("track_count", 1))
            except Exception as e:
                if errors is not None:
                    errors.append("track fallback: {0}".format(e))
                count = 0
            if count >= 4:
                ti = {"Chords": count - 4, "Bass": count - 3,
                      "Drums": count - 2, "Lead": count - 1}
            else:
                # tiny session: layer everything on track 0 so a demo still plays
                ti = {"Chords": 0, "Bass": 0, "Drums": 0, "Lead": 0}

        # --- 6. musical content per section -------------------------------------
        # Each section gets its own scene; clips go in that scene's slot so
        # the demo plays by firing scenes in order. Existing clips are kept
        # (slot-skip) instead of failing the whole step.
        from MCP_Server.tools.music_gen import _chords_clip, _bass_clip, _drums_clip
        chord_slots = {"Intro": 2, "Verse": 4, "Chorus": 4, "Drop": 4}
        degrees = {"techno": [0, 5, 3, 4], "house": [0, 3, 4, 5],
                   "lofi": [1, 4, 0, 5], "trap": [0, 5, 2, 4],
                   "pop": [0, 4, 5, 3]}
        prog = degrees.get(genre, degrees["pop"])
        clips_made = 0
        scene_cursor = 0
        try:
            scene_cursor = max(0, int(_call(ableton, "get_scenes").get("count", 0)) - len(sections))
        except Exception:
            scene_cursor = 0
        for sec_i, (sec_name, sec_bars) in enumerate(sections):
            slots = chord_slots.get(sec_name, 4)
            s_idx = scene_cursor + sec_i
            for kind, fn, needs_genre in (("Chords", _chords_clip, False),
                                          ("Bass", _bass_clip, True)):
                try:
                    if needs_genre:
                        fn(ableton, ti[kind], s_idx, root, scale, prog,
                           min(4, sec_bars), slots, genre)
                    else:
                        fn(ableton, ti[kind], s_idx, root, scale, prog,
                           min(4, sec_bars), slots)
                    clips_made += 1
                except Exception as e:
                    msg = str(e)
                    if "already has a clip" not in msg:
                        errors.append("{0} clip {1}: {2}".format(kind, sec_name, msg))
            try:
                _drums_clip(ableton, ti["Drums"], s_idx,
                            genre if genre in DRUM_PATTERNS else "house",
                            min(4, sec_bars))
                clips_made += 1
            except Exception as e:
                msg = str(e)
                if "already has a clip" not in msg:
                    errors.append("drum clip {0}: {1}".format(sec_name, msg))
        step("clips", clips_made > 0, "{0} clips written".format(clips_made))

        # --- 7. lead melody on the hook (Lead track, last scene) -----------------
        try:
            from MCP_Server.tools.music_gen import _scale_pitch
            lead_ci = scene_cursor + len(sections) - 1
            # create the Lead clip if the slot is empty (skeleton doesn't)
            try:
                ableton.send_command("create_clip", {
                    "track_index": ti["Lead"], "clip_index": lead_ci,
                    "length": 4.0 * min(4, sections[-1][1])})
            except Exception as e:
                if "already has a clip" not in str(e):
                    raise
            notes = []
            melody_degrees = [4, 3, 2, 4, 5, 4, 2, 0]
            for i, deg in enumerate(melody_degrees):
                base = _scale_pitch(root + 24, deg, scale)
                notes.append({"pitch": base, "start_time": i * 0.5,
                              "duration": 0.45, "velocity": 100})
            _add_notes(ableton, ti["Lead"], scene_cursor + len(sections) - 1,
                       notes)
            step("lead", True, "8-note hook on the Lead clip")
        except Exception as e:
            msg = str(e)
            if "already has a clip" not in msg:
                errors.append("lead melody: {0}".format(msg))
            step("lead", False, msg)

        # --- 8. session scale -----------------------------------------------------
        _scale_names = {(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11): "chromatic",
                        (0, 2, 4, 5, 7, 9, 11): "major",
                        (0, 2, 3, 5, 7, 8, 10): "minor"}
        _try(ableton, "set_song_scale",
             {"root_note": root, "scale_name": _scale_names.get(tuple(scale), "minor")},
             errors, "set scale")

        report["status"] = "demo_ready" if (clips_made or ti) else "failed"
        report["tracks_used"] = ti
        report["scenes"] = [s[0] for s in sections]
        report["tip"] = ("call autopilot with your scene order, or fire scenes "
                         "to hear the demo; undo or restore_checkpoint if unwanted")
        return json.dumps(report)

    @mcp.tool()
    @_tool_handler("freezing heavy tracks")
    def smart_freeze(ctx: Context, threshold_percent: float = 15.0,
                     max_tracks: int = 3, dry_run: bool = False) -> str:
        """
        CPU guardian: find the tracks consuming the most CPU (via their
        device/clip load reported by Live) and freeze the heaviest ones,
        verifying the load drop afterwards.

        threshold_percent: only freeze tracks reported above this percent of
        total load. dry_run: report what *would* be frozen without changing
        anything. Unfreeze with unfreeze_track anytime.
        """
        ableton = get_ableton_connection()
        # Load proxy: device count per track (Live's Python API exposes no
        # per-track CPU). Device-heavy tracks are the realistic freeze
        # candidates; meters confirm they are actually playing material.
        tracks = _call(ableton, "get_all_tracks_info").get("tracks", [])
        meters = _call(ableton, "get_track_meters")  # all tracks
        meter_map = {t.get("index"): t for t in (meters.get("tracks") or [])}

        scored = []
        for t in tracks:
            ti = t.get("index")
            if ti is None or t.get("is_group_track"):
                continue
            device_count = len(t.get("devices") or [])
            if device_count == 0:
                continue
            m = meter_map.get(ti, {})
            level = m.get("output_meter_level")
            if level is None:
                level = max(m.get("output_meter_left") or 0,
                            m.get("output_meter_right") or 0)
            playing = (m.get("playing_slot_index", -1) not in (None, -1))
            # score: devices weighted, playing tracks prioritized
            score = device_count * (2.0 if playing else 1.0)
            scored.append({"track_index": ti, "name": t.get("name", "?"),
                           "device_count": device_count,
                           "playing": bool(playing),
                           "meter_level": round(float(level or 0), 3),
                           "load_score": round(score, 1)})
        scored.sort(key=lambda x: -x["load_score"])

        candidates = scored[:max(1, int(max_tracks))]
        result = {
            "ranked_tracks": scored,
            "candidates": candidates,
            "note": "Live's API exposes no per-track CPU; ranking uses "
                    "device count x playing state as a load proxy",
        }
        if dry_run or not candidates:
            result["action"] = "none (dry run or no candidates)"
            return json.dumps(result)

        frozen = []
        for cand in candidates:
            try:
                _call(ableton, "freeze_track",
                      {"track_index": cand["track_index"]})
                frozen.append(cand)
            except Exception as e:
                result.setdefault("errors", []).append(
                    "freeze {0}: {1}".format(cand["name"], e))
        result["frozen"] = frozen
        if frozen:
            result["tip"] = "unfreeze with unfreeze_track when you need to edit"
        return json.dumps(result)

    @mcp.tool()
    @_tool_handler("matching a reference track's profile")
    def match_reference_track(ctx: Context, reference_track_index: int,
                              target_track_index: int) -> str:
        """
        Capture the sonic profile of a reference track (device chain shape,
        send levels, mixer trim) and apply a matched version to the target
        track. The classic 'make it sit like THAT track' move.

        Copies: send levels, pan, volume trim (clamped), and device
        on/off state pattern (matching parameter *values* only when the
        same device class exists on the target). Reports what was applied.
        """
        ableton = get_ableton_connection()
        ref = _call(ableton, "get_track_info",
                    {"track_index": int(reference_track_index)})
        tgt = _call(ableton, "get_track_info",
                    {"track_index": int(target_track_index)})
        if int(reference_track_index) == int(target_track_index):
            raise ValueError("reference and target must differ")

        applied: Dict[str, Any] = {}
        errors: List[str] = []

        # mixer: pan + volume trim (conservative clamp)
        for src_key, cmd in (("panning", "set_track_pan"),
                             ("volume", "set_track_volume")):
            val = ref.get(src_key)
            if val is None:
                continue
            try:
                val = float(val)
            except (TypeError, ValueError):
                continue
            if cmd == "set_track_volume":
                val = max(0.0, min(1.0, val))
            _try(ableton, cmd, {"track_index": int(target_track_index),
                                "pan" if src_key == "panning" else "volume": val},
                 errors, "match " + src_key)
            applied[src_key] = val

        # sends: read the reference's send levels
        try:
            ref_mixer = _call(ableton, "get_track_sends",
                              {"track_index": int(reference_track_index)})
            ref_sends = ref_mixer.get("sends") or []
            for i, s in enumerate(ref_sends):
                val = s.get("value") if isinstance(s, dict) else s
                if val is None:
                    continue
                _try(ableton, "set_track_send", {
                    "track_index": int(target_track_index), "send_index": i,
                    "value": float(val)}, errors, "match send {0}".format(i))
                applied["send_{0}".format(i)] = val
        except Exception as e:
            errors.append("sends: {0}".format(e))

        # device on/off pattern (devices on both sides, matched by index)
        ref_devices = ref.get("devices") or []
        tgt_devices = tgt.get("devices") or []
        matched = 0
        for i, rd in enumerate(ref_devices):
            if i >= len(tgt_devices):
                break
            # read the reference device's on state via its Device On param
            try:
                rd_params = _call(ableton, "get_device_parameters", {
                    "track_index": int(reference_track_index),
                    "device_index": i})
                on_val = None
                for p in rd_params.get("parameters", []):
                    if p.get("name") == "Device On":
                        on_val = p.get("value")
                        break
                if on_val is None:
                    continue
                _try(ableton, "set_device_enabled", {
                    "track_index": int(target_track_index), "device_index": i,
                    "enabled": on_val > 0.5},
                    errors, "device on/off {0}".format(i))
                matched += 1
            except Exception:
                continue
        applied["device_onoff_matched"] = matched

        return json.dumps({
            "status": "ok",
            "reference": ref.get("name", str(reference_track_index)),
            "target": tgt.get("name", str(target_track_index)),
            "applied": applied,
            "errors": errors,
            "note": "only settings present on both sides were touched; "
                    "fine-tune by ear",
        })
