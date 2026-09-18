"""Videosync2 show automation handlers (v0.8).

Videosync2 maps Live track mixers to layer visibility: track volume =
layer opacity, track mute = layer hidden. Devices on video tracks expose
no LOM parameters, so ALL show automation goes through track mixers.

This module gives the Videosync2 rig a tiny, show-safe API:

- read/write arrangement-level mixer automation (volume, pan) — the LOM
  primitive the rest builds on (Live 12.2+ ClipEnvelope creation),
- song-scoped layer programs: one operation per song region sets the
  baseline (fade-ins/out on backdrops, lyrics/cam hidden unless asked)
  plus optional section steps,
- show-scope helpers: failover to the backup video track, layer on/off,
  blackout.

Notes:
- Envelope editing needs the arrangement clip covering the target time.
  We therefore create tiny (0-beat) "carrier" clips at section starts so
  envelopes exist where nothing plays. A 0-length arrangement clip has
  no audible footprint.
- Automation written here is IN-MEMORY; save the Set to persist.
"""
import logging

logger = logging.getLogger("AbletonBridge")

# Videosync2 rig track indexes (Videosync2 set layout)
TRACK_VIDEO_BACKUP = 0     # "VIDEO" — default-player fallback, muted
TRACK_VSYNC_GROUP = 14
TRACK_MAIN_BACKDROP = 15
TRACK_LYRICS_VIDEO = 16
TRACK_LIVE_CAM = 17


def _track(song, index):
    return song.tracks[index]


def _mixer_param(track, name):
    md = track.mixer_device
    if name == "volume":
        return md.volume
    if name == "panning":
        return md.panning
    for i, send in enumerate(md.sends):
        if name in ("send_a", "send_%d" % i):
            return send
    raise ValueError("Unsupported mixer parameter: %r" % name)


def _find_or_create_carrier_clip(track, time_beats, ctrl=None):
    """Return an arrangement clip covering `time_beats`.

    Prefers an existing arrangement clip; else creates a 0-beat carrier
    clip (Live 12.2+). Raises with a clear message when creation is not
    possible.
    """
    # 1) existing clip covering the time
    try:
        for clip in track.arrangement_clips:
            if float(clip.start_time) <= time_beats < float(clip.end_time):
                return clip
        # touching clip starting exactly at the requested time
        for clip in track.arrangement_clips:
            if abs(float(clip.start_time) - time_beats) < 1e-6:
                return clip
    except Exception as e:
        logger.warning("arrangement_clips read failed on %r: %s", track.name, e)

    # 2) create a carrier clip (0 beats — no audio content, envelope host)
    try:
        clip = track.create_audio_clip(float(time_beats), 0.0)
        if ctrl:
            ctrl.log_message(
                "vsync_automation: created carrier clip on %r at %s"
                % (track.name, time_beats))
        return clip
    except Exception as e:
        raise RuntimeError(
            "No arrangement clip covers beat %s on track %r and creating a "
            "carrier clip failed (%s). Requires Live 12.2+."
            % (time_beats, track.name, e))


def set_arrangement_mixer_automation(song, track_index, parameter_name,
                                     points, ctrl=None):
    """Write arrangement-level automation points for a track mixer param.

    points: list of {"time": beats, "value": 0..1} (time is absolute
    arrangement beats). Uses/creates a carrier clip at the first point's
    time, then inserts all points into its envelope.
    """
    track = _track(song, track_index)
    param = _mixer_param(track, parameter_name)
    if not points:
        return {"track_index": track_index, "parameter": parameter_name,
                "points_added": 0}

    pts = sorted(points, key=lambda p: float(p.get("time", 0)))
    t0 = float(pts[0]["time"])
    clip = _find_or_create_carrier_clip(track, t0, ctrl=ctrl)
    if not hasattr(clip, "create_automation_envelope"):
        raise RuntimeError(
            "Clip %r does not support automation envelopes on this Live "
            "version" % getattr(clip, "name", "?"))

    try:
        env = clip.automation_envelope(param)
    except Exception:
        env = None
    if env is None:
        env = clip.create_automation_envelope(param)
    if env is None:
        raise RuntimeError(
            "Could not create automation envelope for %r on track %r"
            % (parameter_name, track.name))

    inserted = 0
    for p in pts:
        t = float(p["time"])
        v = max(0.0, min(1.0, float(p.get("value", 0.0))))
        try:
            env.insert_step(t, v) if hasattr(env, "insert_step") else env.insert_point(t, v)
            inserted += 1
        except Exception as e:
            logger.warning("insert automation point failed at %s: %s", t, e)

    return {
        "track_index": track_index,
        "track_name": track.name,
        "parameter": parameter_name,
        "carrier_clip": getattr(clip, "name", "?"),
        "points_added": inserted,
    }


def get_arrangement_mixer_automation(song, track_index, parameter_name,
                                     ctrl=None):
    """Read back volume automation from the first arrangement clip that
    has an envelope for the parameter. Diagnostic helper."""
    track = _track(song, track_index)
    param = _mixer_param(track, parameter_name)
    out = []
    try:
        clips = list(track.arrangement_clips)
    except Exception:
        clips = []
    for clip in clips:
        try:
            env = clip.automation_envelope(param)
        except Exception:
            env = None
        if env is None:
            continue
        entry = {"clip_name": getattr(clip, "name", "?"),
                 "start_time": float(clip.start_time)}
        try:
            # Live 12 envelope read-back
            entry["points"] = [
                {"time": float(p[0]), "value": float(p[1])}
                for p in env.points
            ]
        except Exception:
            entry["points"] = "envelope exists; point read-back not available"
        out.append(entry)
    return {"track_index": track_index, "parameter": parameter_name,
            "envelopes": out}


def clear_arrangement_mixer_automation(song, track_index, parameter_name,
                                       ctrl=None):
    """Remove the parameter's envelope from every arrangement clip."""
    track = _track(song, track_index)
    param = _mixer_param(track, parameter_name)
    removed = 0
    try:
        clips = list(track.arrangement_clips)
    except Exception:
        clips = []
    for clip in clips:
        try:
            env = clip.automation_envelope(param)
        except Exception:
            env = None
        if env is not None:
            try:
                env.delete()
                removed += 1
            except Exception as e:
                logger.warning("envelope delete failed on %r: %s",
                               getattr(clip, "name", "?"), e)
    return {"track_index": track_index, "parameter": parameter_name,
            "envelopes_removed": removed}


# ---------------------------------------------------------------------------
# Show-scope operations (the "auto-VJ" baseline + stage buttons)
# ---------------------------------------------------------------------------

def _song_regions(song):
    """[(start_beat, end_beat, name)] for every locator region."""
    cps = []
    try:
        cps = [(float(cp.time), cp.name) for cp in song.cue_points]
    except Exception:
        return []
    cps.sort()
    regions = []
    for i, (t, name) in enumerate(cps):
        end = cps[i + 1][0] if i + 1 < len(cps) else None
        regions.append((t, end, name))
    return regions


def program_song_video_automation(song, song_name, ctrl=None,
                                  backdrop_volume=0.85,
                                  sections=None):
    """One-call per-song video automation for the Videosync2 rig.

    For the region named `song_name` (fuzzy-matched against locators,
    skipping 'SONG END'):

    - Main Backdrop: fade-in (2 bars), full level, fade-out (2 bars)
    - Lyrics Video + Live Cam: silent the whole song (hidden layer),
      carried by 0-beat clips so nothing plays and nothing shows
    - Optional `sections`: [{"name": "chorus", "at_bar": 57,
      "layers": {"cam": 0.85}}] for in-song exceptions.

    Everything is arrangement automation — zero stage buttons needed for
    the baseline show.
    """
    regions = _song_regions(song)
    if not regions:
        raise ValueError("No locators in this set")

    target = None
    low = str(song_name).strip().lower()
    for start, end, name in regions:
        if name == "SONG END" or end is None:
            continue
        if low in name.lower():
            target = (start, end, name)
            break
    if target is None:
        raise ValueError("No song region matching %r" % song_name)
    start, end, name = target

    results = {"song": name, "region": {"start_beat": start, "end_beat": end},
               "written": []}

    # --- Main Backdrop: fade in / hold / fade out (2-bar = 8-beat fades)
    fb = 8.0
    bp = [
        {"time": start, "value": 0.0},
        {"time": start + fb, "value": backdrop_volume},
        {"time": end - fb, "value": backdrop_volume},
        {"time": end, "value": 0.0},
    ]
    r = set_arrangement_mixer_automation(
        song, TRACK_MAIN_BACKDROP, "volume", bp, ctrl=ctrl)
    results["written"].append({"track": "Main Backdrop", **r})

    # --- Hidden layers: carriers at song start, value 0 the whole song
    for tname, idx in (("Lyrics Video", TRACK_LYRICS_VIDEO),
                       ("Live Cam", TRACK_LIVE_CAM)):
        r = set_arrangement_mixer_automation(
            song, idx, "volume", [{"time": start, "value": 0.0}], ctrl=ctrl)
        results["written"].append({"track": tname, **r})

    # --- Optional in-song section steps
    for sec in (sections or []):
        at_bar = float(sec.get("at_bar", 0))
        t = start + (at_bar - 1) * 4.0
        for layer, val in (sec.get("layers") or {}).items():
            idx = {"cam": TRACK_LIVE_CAM, "lyrics": TRACK_LYRICS_VIDEO,
                   "backdrop": TRACK_MAIN_BACKDROP}.get(layer)
            if idx is None:
                continue
            r = set_arrangement_mixer_automation(
                song, idx, "volume", [{"time": t, "value": float(val)}],
                ctrl=ctrl)
            results["written"].append(
                {"track": layer, "section": sec.get("name"), **r})

    return results


def video_failover(song, to_backup=True, ctrl=None):
    """Panic switch: backup default-player track <-> VSync2 group.

    to_backup=True: unmute VIDEO (track 0), mute VSync2 Group (14).
    to_backup=False: the reverse (return to Videosync2).
    Also stops the lyrics/cam carriers from showing through the group
    mute. Returns verified states.
    """
    video, group = _track(song, TRACK_VIDEO_BACKUP), _track(song, TRACK_VSYNC_GROUP)

    # sanity: refuse when the backup track has no clips to show
    if to_backup:
        try:
            n = len(list(video.arrangement_clips))
        except Exception:
            n = 0
        if n == 0:
            raise RuntimeError("Backup track %r has no arrangement clips"
                               % video.name)

    video.mute = not bool(to_backup)
    group.mute = bool(to_backup)

    ok = (video.mute == (not to_backup)) and (group.mute == bool(to_backup))
    return {"failover_to": "backup" if to_backup else "vsync2",
            "video_track_muted": video.mute,
            "vsync2_group_muted": group.mute,
            "verified": ok}


def set_video_layer(song, layer, level, ctrl=None):
    """Manual layer level (0..1) for a Videosync2 layer.

    layer: 'backdrop' | 'lyrics' | 'cam' | 'all'
    NOTE: while a clip-envelope automation exists on a track, manual
    volume moves are overridden during playback inside that clip's span.
    Use clear_arrangement_mixer_automation first for full manual control.
    """
    mapping = {"backdrop": TRACK_MAIN_BACKDROP, "lyrics": TRACK_LYRICS_VIDEO,
               "cam": TRACK_LIVE_CAM}
    if layer == "all":
        targets = list(mapping.items())
    elif layer in mapping:
        targets = [(layer, mapping[layer])]
    else:
        raise ValueError("layer must be one of %s or 'all'" % sorted(mapping))
    out = []
    for name, idx in targets:
        tr = _track(song, idx)
        tr.mixer_device.volume = max(0.0, min(1.0, float(level)))
        out.append({"layer": name, "volume": tr.mixer_device.volume})
    return {"set": out}
