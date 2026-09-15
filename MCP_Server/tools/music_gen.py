"""
AI Music Toolkit for AbleBridgePlus.

Purpose-built generators so an AI assistant can produce real musical
content in one call instead of hand-placing notes: prompt-to-clip
basslines, chord progressions, matching basslines, drum patterns and a
full song skeleton (scenes + clips across tracks).

All pitch math uses MIDI note numbers (Live default octave display: 60 = C3).
Bass lines land in the 36-48 range, chords around 55-67, drums use the
General MIDI map (kick 36, snare 38, closed hat 42, open hat 46).
"""
import json
import logging
import re
from typing import Any, Dict, List

from mcp.server.fastmcp import Context

from MCP_Server.tools._base import _tool_handler
from MCP_Server.connections.ableton import get_ableton_connection

logger = logging.getLogger("MCP_Server.music_gen")

# ---------------------------------------------------------------------------
# Music theory core
# ---------------------------------------------------------------------------

NOTE_OFFSETS = {"C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3, "E": 4,
                "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8, "AB": 8,
                "A": 9, "A#": 10, "BB": 10, "B": 11}

SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],          # natural minor / aeolian
    "harmonic minor": [0, 2, 3, 5, 7, 8, 11],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "pentatonic minor": [0, 3, 5, 7, 10],
    "pentatonic major": [0, 2, 4, 7, 9],
    "blues": [0, 3, 5, 6, 7, 10],
}

SCALE_ALIASES = {"maj": "major", "min": "minor", "m": "minor",
                 "aeolian": "minor", "nat minor": "minor"}

# scale-degree progressions (1-based degrees of the chosen scale)
PROGRESSIONS = {
    "pop": [[1, 5, 6, 4], [6, 4, 1, 5], [1, 4, 6, 5]],
    "edm": [[6, 4, 1, 5], [1, 5, 6, 4], [4, 5, 6, 6]],
    "rock": [[1, 7, 4, 1], [1, 4, 5, 4], [1, 5, 4, 5]],
    "blues": [[1, 4, 5, 4], [1, 1, 4, 4]],
    "jazz": [[2, 5, 1, 6], [2, 5, 1, 1], [3, 6, 2, 5]],
    "lofi": [[1, 6, 2, 5], [1, 4, 2, 5]],
    "cinematic": [[1, 6, 3, 7], [1, 4, 1, 5]],
}

# bass rhythm styles: list of (step, degree_jump, duration_in_steps, octave)
# step grid: 16 steps per bar (16th notes); degree_jump 0=root, 4=fifth, 7=octave
BASS_STYLES = {
    "acid": [(i, [0, 0, 7, 12][i % 4] if i % 4 == 3 or i % 8 == 6 else 0,
              1, 0) for i in range(16) if i not in (7,)],
    "house": [(i, 0, 1, 0) for i in range(2, 16, 4)],        # offbeat 8ths
    "techno": [(i, 0 if i % 8 else 12, 1, 0) for i in range(16)],
    "rock": [(i, 7 if i % 4 == 2 else 0, 2, 0) for i in range(0, 16, 2)],
    "pop": [(0, 0, 6, 0), (8, 0, 4, 0), (14, 7, 2, 0)],
    "dnb": [(0, 0, 3, 0), (10, 7, 2, 0)],
    "lofi": [(0, 0, 6, 0), (10, 0, 4, 0)],
}

BASS_ROOT_PITCH = 36   # C2
CHORD_BASE_PITCH = 60  # C4

# General MIDI drum map
DRUM = {"kick": 36, "snare": 38, "clap": 39, "closed_hat": 42,
        "open_hat": 46, "ride": 51, "crash": 49, "tom": 45}

# per style: {drum: [steps]}, velocities per drum
DRUM_PATTERNS = {
    "house": {"kick": [0, 4, 8, 12], "clap": [4, 12],
              "open_hat": [2, 6, 10, 14],
              "closed_hat": [0, 1, 3, 4, 5, 7, 8, 9, 11, 12, 13, 15]},
    "techno": {"kick": [0, 4, 8, 12], "clap": [4, 12],
               "open_hat": [2, 6, 10, 14],
               "closed_hat": [1, 3, 5, 7, 9, 11, 13, 15]},
    "trap": {"kick": [0, 6, 10], "snare": [8],
             "closed_hat": list(range(16))},
    "dnb": {"kick": [0, 10], "snare": [4, 12],
            "closed_hat": [0, 2, 4, 6, 8, 10, 12, 14],
            "open_hat": [7]},
    "rock": {"kick": [0, 8, 10], "snare": [4, 12],
             "closed_hat": [0, 2, 4, 6, 8, 10, 12, 14]},
    "pop": {"kick": [0, 8], "snare": [4, 12],
            "closed_hat": [0, 2, 4, 6, 8, 10, 12, 14]},
    "lofi": {"kick": [0, 7], "snare": [4, 12],
             "closed_hat": [2, 6, 10, 14]},
}
DRUM_VELOCITY = {"kick": 108, "snare": 100, "clap": 96,
                 "closed_hat": 58, "open_hat": 72, "ride": 60, "crash": 90}


def _scale_pitch(base: int, degree_index: int, scale: List[int]) -> int:
    """Pitch for a scale-degree index (can exceed one octave)."""
    n = len(scale)
    octave, step = divmod(degree_index, n)
    return base + scale[step] + 12 * octave


def _parse_key(key: str) -> (int, List[int]):
    """'F# minor' / 'Eb maj' / 'A' -> (root_offset, scale intervals)."""
    m = re.match(r'^\s*([A-G])(#|b)?\s*(.*)$', key.strip(), re.I)
    if not m:
        raise ValueError("Cannot parse key '{0}'. Use e.g. 'F# minor'.".format(key))
    root = NOTE_OFFSETS.get((m.group(1) + (m.group(2) or '')).upper())
    if root is None:
        raise ValueError("Bad note name in key '{0}'".format(key))
    rest = (m.group(3) or '').strip().lower()
    scale_name = SCALE_ALIASES.get(rest, rest if rest in SCALES else "minor")
    if rest and rest not in SCALES and rest not in SCALE_ALIASES:
        scale_name = "minor" if "minor" in rest else ("major" if "maj" in rest else scale_name)
    return root, SCALES[scale_name]


def _style_from_prompt(prompt: str) -> str:
    p = prompt.lower()
    for style in ("acid", "house", "techno", "rock", "pop", "dnb",
                  "drum and bass", "drum & bass", "lofi", "lo-fi",
                  "trap", "jazz", "edm"):
        if style in p:
            return {"drum and bass": "dnb", "drum & bass": "dnb",
                    "lo-fi": "lofi", "lofi": "lofi"}.get(style, style)
    return "house"


def _key_from_prompt(prompt: str, default: str) -> str:
    m = re.search(r'\bin ([A-G](?:#|b)?)\s*(maj(?:or)?|min(?:or)?|m|dorian|'
                  r'phrygian|mixolydian|lydian|harmonic minor|blues)?',
                  prompt, re.I)
    if m:
        note = m.group(1)
        qual = (m.group(2) or '').lower()
        qual = {"maj": "major", "major": "major", "min": "minor",
                "minor": "minor", "m": "minor"}.get(qual, qual)
        return "{0} {1}".format(note, qual).strip()
    return default


def _add_notes(ableton, track_index: int, clip_index: int,
               notes: List[Dict[str, Any]]) -> Dict[str, Any]:
    return ableton.send_command("add_notes_to_clip", {
        "track_index": track_index, "clip_index": clip_index,
        "notes": notes,
    })


def register_tools(mcp):

    @mcp.tool()
    @_tool_handler("generating clip from prompt")
    def generate_clip_from_prompt(ctx: Context, track_index: int,
                                  clip_index: int, prompt: str,
                                  bars: int = 4,
                                  key: str = "A minor") -> str:
        """
        Generate a bassline clip from a text prompt, e.g. "acid bassline
        in F# minor, dark and hypnotic" or "rolling house bassline".
        Understands styles (acid/house/techno/rock/pop/dnb/lofi), key
        (in F# minor, in C major) and mood words (dark = lower octave,
        bright = higher, chill = softer velocities). Creates the clip
        (4 bars by default) and writes in-key notes.
        """
        if not (1 <= bars <= 16):
            raise ValueError("bars must be 1-16")
        ableton = get_ableton_connection()
        style = _style_from_prompt(prompt)
        key = _key_from_prompt(prompt, key)
        root, scale = _parse_key(key)
        p = prompt.lower()
        octave = -12 if "dark" in p or "deep" in p or "sub" in p else \
                 (12 if "bright" in p or "high" in p else 0)
        vel = 80 if ("chill" in p or "soft" in p) else \
              (112 if "aggressive" in p or "hard" in p else 96)

        pattern = BASS_STYLES.get(style, BASS_STYLES["house"])
        notes = []
        for bar in range(bars):
            for step, jump, dur, _oct in pattern:
                deg_index = (bar * 2 + (0 if step < 8 else 1))
                pitch = _scale_pitch(BASS_ROOT_PITCH + root + octave,
                                     deg_index, scale) + jump
                if pitch < 24 or pitch > 96:
                    pitch = BASS_ROOT_PITCH + root + octave
                notes.append({"pitch": pitch,
                              "start_time": bar * 4.0 + step * 0.25,
                              "duration": dur * 0.25,
                              "velocity": max(40, min(127,
                                              vel + (6 if step % 4 == 0 else -4)))})
        ableton.send_command("create_clip", {"track_index": track_index,
                                             "clip_index": clip_index,
                                             "length": bars * 4.0})
        _add_notes(ableton, track_index, clip_index, notes)
        import json as _json
        return _json.dumps({
            "status": "clip_generated", "style": style, "key": key,
            "bars": bars, "notes_written": len(notes),
            "track_index": track_index, "clip_index": clip_index,
        })

    @mcp.tool()
    @_tool_handler("building chord progression")
    def build_chord_progression(ctx: Context, track_index: int,
                                clip_index: int, key: str = "C major",
                                progression: str = "pop", bars: int = 8,
                                add_sevenths: bool = False) -> str:
        """
        Write a chord-progression clip: choose a genre flavour (pop, edm,
        rock, blues, jazz, lofi, cinematic) or pass your own degrees like
        "1 5 6 4". Two bars per chord by default (bars = total). Uses the
        given key/scale so everything stays in key. Optional 7ths for
        jazz/lofi colour.
        """
        if not (4 <= bars <= 32):
            raise ValueError("bars must be 4-32")
        ableton = get_ableton_connection()
        root, scale = _parse_key(key)
        if progression in PROGRESSIONS:
            degrees = PROGRESSIONS[progression][0]
        else:
            try:
                degrees = [int(d) for d in progression.replace('-', ' ').split()]
            except ValueError:
                raise ValueError("progression must be a genre name (pop, jazz, "
                                 "lofi, ...) or degrees like '1 5 6 4'")
        bars_per_chord = 2
        notes = []
        chord_slots = bars // bars_per_chord
        degrees_repeated = (degrees * (chord_slots // len(degrees) + 1))[:chord_slots]
        for i, deg in enumerate(degrees_repeated):
            base_idx = deg - 1
            intervals = [0, 2, 4] + ([6] if add_sevenths else [])
            for bar in range(bars_per_chord):
                start_beat = (i * bars_per_chord + bar) * 4.0
                for iv in intervals:
                    pitch = _scale_pitch(CHORD_BASE_PITCH + root,
                                         base_idx + iv, scale)
                    notes.append({"pitch": pitch, "start_time": start_beat,
                                  "duration": 3.5, "velocity": 78})
        ableton.send_command("create_clip", {"track_index": track_index,
                                             "clip_index": clip_index,
                                             "length": bars * 4.0})
        _add_notes(ableton, track_index, clip_index, notes)
        import json as _json
        return _json.dumps({
            "status": "progression_written", "key": key,
            "degrees": degrees, "bars": bars,
            "sevenths": add_sevenths, "notes_written": len(notes),
            "track_index": track_index, "clip_index": clip_index,
        })

    @mcp.tool()
    @_tool_handler("building matching bassline")
    def build_bassline_for_progression(ctx: Context, track_index: int,
                                       clip_index: int, key: str,
                                       degrees: str, bars: int = 8,
                                       style: str = "house") -> str:
        """
        Write a bassline clip that follows a chord progression: pass the
        same key and degrees used for build_chord_progression (e.g. key
        "A minor", degrees "6 4 1 5"). Each chord root is held/played on
        the chosen rhythmic style (house offbeat, techno rolling, pop).
        Put chords and this bassline on different tracks so they play
        together.
        """
        ableton = get_ableton_connection()
        root, scale = _parse_key(key)
        try:
            deg_list = [int(d) for d in degrees.replace('-', ' ').split()]
        except ValueError:
            raise ValueError("degrees must be like '6 4 1 5'")
        bars_per_chord = 2
        pattern = BASS_STYLES.get(style, BASS_STYLES["house"])
        notes = []
        chord_slots = bars // bars_per_chord
        for i in range(chord_slots):
            deg = deg_list[i % len(deg_list)] - 1
            for bar in range(bars_per_chord):
                for step, jump, dur, _oct in pattern:
                    pitch = _scale_pitch(BASS_ROOT_PITCH + root,
                                         deg, scale) + (jump if jump != 12 else 12)
                    notes.append({"pitch": pitch,
                                  "start_time": (i * bars_per_chord + bar) * 4.0
                                                + step * 0.25,
                                  "duration": dur * 0.25, "velocity": 100})
        ableton.send_command("create_clip", {"track_index": track_index,
                                             "clip_index": clip_index,
                                             "length": bars * 4.0})
        _add_notes(ableton, track_index, clip_index, notes)
        import json as _json
        return _json.dumps({"status": "bassline_written", "key": key,
                            "degrees": deg_list, "style": style,
                            "bars": bars, "notes_written": len(notes)})

    @mcp.tool()
    @_tool_handler("generating drum pattern")
    def generate_advanced_drum_pattern(ctx: Context, track_index: int,
                                       clip_index: int, style: str = "house",
                                       bars: int = 4, add_fills: bool = True,
                                       humanize: bool = True) -> str:
        """
        Generate a drum clip (General MIDI map: kick/snare/hats) in a
        chosen style: house, techno, trap, dnb, rock, pop, lofi. Four bars
        by default with an end-of-phrase fill, and light humanization
        (velocity + micro-timing) unless humanize=false. Requires a track
        with a drum instrument (e.g. Drum Rack) loaded.
        """
        if style not in DRUM_PATTERNS:
            raise ValueError("style must be one of: " + ", ".join(DRUM_PATTERNS))
        if not (1 <= bars <= 16):
            raise ValueError("bars must be 1-16")
        ableton = get_ableton_connection()
        pattern = DRUM_PATTERNS[style]
        notes = []
        for bar in range(bars):
            is_last = bar == bars - 1
            for drum, steps in pattern.items():
                for step in steps:
                    vel = DRUM_VELOCITY.get(drum, 90)
                    tshift = 0.0
                    if humanize:
                        vel += (-10 if (step % 4 and drum in
                                        ("closed_hat", "open_hat")) else 4)
                        tshift = (0.01 if step % 2 else -0.008)
                    if is_last and add_fills and bar > 0 and \
                       drum == "snare" and step >= 12:
                        vel += 6 + (step - 12) * 4   # rising fill
                    notes.append({"pitch": DRUM[drum],
                                  "start_time": bar * 4.0 + step * 0.25 + tshift,
                                  "duration": 0.22,
                                  "velocity": max(30, min(127, vel))})
        ableton.send_command("create_clip", {"track_index": track_index,
                                             "clip_index": clip_index,
                                             "length": bars * 4.0})
        _add_notes(ableton, track_index, clip_index, notes)
        import json as _json
        return _json.dumps({"status": "drums_written", "style": style,
                            "bars": bars, "fills": add_fills,
                            "humanize": humanize,
                            "notes_written": len(notes)})

    @mcp.tool()
    @_tool_handler("building song skeleton")
    def build_song_skeleton(ctx: Context, sections: str,
                            key: str = "A minor",
                            genre: str = "edm",
                            create_tracks: bool = True) -> str:
        """
        Build a whole song arrangement skeleton: creates Chords, Bass and
        Drums MIDI tracks (if needed), then for each section makes a named
        scene with in-key chord/bass/drum clips. sections is JSON like:
        [{"name":"Intro","bars":4},{"name":"Verse","bars":8},
         {"name":"Chorus","bars":8},{"name":"Drop","bars":8}]
        Genre picks the chord flavour and drum style. Returns everything
        it created so the AI (or you) can refine from there.
        """
        import json as _json
        try:
            section_list = _json.loads(sections)
        except json.JSONDecodeError:
            raise ValueError("sections must be JSON, e.g. "
                             '[{"name":"Verse","bars":8}]')
        if not section_list or len(section_list) > 12:
            raise ValueError("1-12 sections required")

        ableton = get_ableton_connection()
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

        scene_index = 0
        for sec in section_list[:12]:
            name = str(sec.get("name", "Section"))[:24]
            bars = max(2, min(16, int(sec.get("bars", 8))))
            ableton.send_command("create_scene", {"index": -1})
            scene_idx = sec.get("scene_index")
            del scene_idx  # scenes are appended; index resolved below
            scenes_now = ableton.send_command("get_scenes")
            s_idx = len(scenes_now.get("scenes", [])) - 1
            ableton.send_command("set_scene_name",
                                 {"scene_index": s_idx, "name": name})
            created["scenes"].append({"index": s_idx, "name": name})

            degrees = PROGRESSIONS.get(genre, PROGRESSIONS["edm"])[0]
            chord_slots = max(1, bars // 2)

            def _write(track_name, fn):
                info = ableton.send_command("get_all_tracks_info")
                for t in info.get("tracks", []):
                    if t.get("name") == track_name:
                        fn(t["index"], s_idx)
                        return
            _write("Chords", lambda ti, ci: _chords_clip(
                ableton, ti, ci, root, scale, degrees, bars, chord_slots))
            _write("Bass", lambda ti, ci: _bass_clip(
                ableton, ti, ci, root, scale, degrees, bars, chord_slots,
                genre))
            _write("Drums", lambda ti, ci: _drums_clip(
                ableton, ti, ci, genre if genre in DRUM_PATTERNS else "house",
                bars))
            created["clips"] += 3

        import json as _json
        return _json.dumps({"status": "skeleton_built", "key": key,
                            "genre": genre, **created})


def _chords_clip(ableton, ti, ci, root, scale, degrees, bars, chord_slots):
    ableton.send_command("create_clip", {"track_index": ti,
                                         "clip_index": ci, "length": bars * 4.0})
    notes = []
    for i in range(chord_slots):
        deg = degrees[i % len(degrees)] - 1
        for bar in range(2 if bars - i * 2 >= 2 else 1):
            start = (i * 2 + bar) * 4.0
            for iv in (0, 2, 4):
                notes.append({"pitch": _scale_pitch(CHORD_BASE_PITCH + root,
                                                    deg + iv, scale),
                              "start_time": start, "duration": 3.5,
                              "velocity": 76})
    _add_notes(ableton, ti, ci, notes)


def _bass_clip(ableton, ti, ci, root, scale, degrees, bars, chord_slots, genre):
    ableton.send_command("create_clip", {"track_index": ti,
                                         "clip_index": ci, "length": bars * 4.0})
    style = {"house": "house", "techno": "techno", "lofi": "lofi",
             "jazz": "pop"}.get(genre, "house")
    pattern = BASS_STYLES.get(style, BASS_STYLES["house"])
    notes = []
    for i in range(chord_slots):
        deg = degrees[i % len(degrees)] - 1
        for bar in range(2 if bars - i * 2 >= 2 else 1):
            for step, jump, dur, _oct in pattern:
                notes.append({"pitch": _scale_pitch(BASS_ROOT_PITCH + root,
                                                    deg, scale) + jump,
                              "start_time": (i * 2 + bar) * 4.0 + step * 0.25,
                              "duration": dur * 0.25, "velocity": 98})
    _add_notes(ableton, ti, ci, notes)


def _drums_clip(ableton, ti, ci, style, bars):
    ableton.send_command("create_clip", {"track_index": ti,
                                         "clip_index": ci, "length": bars * 4.0})
    pattern = DRUM_PATTERNS[style]
    notes = []
    for bar in range(bars):
        for drum, steps in pattern.items():
            for step in steps:
                notes.append({"pitch": DRUM[drum],
                              "start_time": bar * 4.0 + step * 0.25,
                              "duration": 0.22,
                              "velocity": DRUM_VELOCITY.get(drum, 90)})
    _add_notes(ableton, ti, ci, notes)
