"""ASCII grid notation <-> MIDI notes for AbleBridgePlus.

Drum grid (GM drum-map label rows, only rows with hits are shown):
    |1e&a2e&a3e&a4e&a|
  CR|x---------------|
  KK|o---o--o-o--o-o-|

Melodic grid (note-name rows, e.g. G4, C#3, sorted high to low):
    |1e&a2e&a3e&a4e&a|
  G4|----o-------o---|
  C4|o-------o-------|

One character per 16th note (0.25 beats in 4/4). Hit characters:
    X = velocity 127   x = 100   O = 85   o = 70   * = 50
Everything else counts as empty.
"""
from __future__ import annotations

# GM drum-map labels -> pitch
_DRUM_MAP = {
    "KK": 36, "BD": 36, "KICK": 36,
    "SN": 38, "SD": 38, "SNARE": 38,
    "HC": 42, "CH": 42, "HH": 42,
    "OH": 46, "OHH": 46,
    "PH": 44, "PHH": 44,
    "TT": 45, "TOM": 45,
    "LT": 43, "FT": 41, "LB": 41,
    "CP": 39, "CLP": 39, "CLAP": 39,
    "CB": 56,
    "RD": 51, "RIDE": 51,
    "CR": 49, "CRASH": 49, "CC": 49,
    "CY": 57, "CHINA": 52,
}
_PITCH_TO_DRUM_LABEL = {}
for _label, _pitch in _DRUM_MAP.items():
    # First (canonical) label wins
    if _pitch not in _PITCH_TO_DRUM_LABEL:
        _PITCH_TO_DRUM_LABEL[_pitch] = _label

_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_NAME_TO_SEMITONE = {n: i for i, n in enumerate(_NOTE_NAMES)}

# Row display order for drums (top to bottom of the grid)
_DRUM_ROW_ORDER = [
    ("CR", 49), ("RD", 51), ("OH", 46), ("HC", 42), ("PH", 44),
    ("TT", 45), ("CP", 39), ("SN", 38), ("KK", 36), ("LT", 43), ("FT", 41), ("CB", 56),
]
# Pitches considered "drum region" -> always render as drum grid
_DRUM_REGION = set(range(35, 60)) | {61}

_STEPS_PER_BAR = 16            # 16th notes per 4/4 bar
_BEATS_PER_STEP = 0.25
_HIT_VELOCITY = {"X": 127, "x": 100, "O": 85, "o": 70, "*": 50}


def _pitch_to_name(pitch: int) -> str:
    return "{0}{1}".format(_NOTE_NAMES[pitch % 12], pitch // 12 - 1)


def _name_to_pitch(label: str):
    """Parse a note-name label like C4, G#3, Db2 -> MIDI pitch (or None)."""
    label = label.strip()
    if not label:
        return None
    semitone = _NAME_TO_SEMITONE.get(label[0].upper())
    if semitone is None:
        return None
    rest = label[1:]
    if rest.startswith("#"):
        semitone += 1
        rest = rest[1:]
    elif rest.startswith("b"):
        semitone -= 1
        rest = rest[1:]
    try:
        octave = int(rest)
    except ValueError:
        return None
    return semitone + (octave + 1) * 12


def _quantize_step(start: float) -> int:
    return max(0, int(round(float(start) / _BEATS_PER_STEP)))


def notes_to_grid(notes) -> str:
    """Render a list of note dicts ({pitch, start, duration, velocity}) as ASCII grid."""
    notes = list(notes or [])
    if not notes:
        return "(no notes)"

    pitches = set()
    total_steps = 0
    for n in notes:
        try:
            pitches.add(int(n["pitch"]))
        except (KeyError, TypeError, ValueError):
            continue
        total_steps = max(total_steps, _quantize_step(n.get("start", 0.0)) + 1)
    if not pitches:
        return "(no notes)"

    # Round total length up to whole bars
    n_bars = max(1, (total_steps + _STEPS_PER_BAR - 1) // _STEPS_PER_BAR)
    n_steps = n_bars * _STEPS_PER_BAR

    # Drum grid if every pitch sits in the drum region, else melodic rows
    is_drum = pitches.issubset(_DRUM_REGION)
    if is_drum:
        rows = [(label, pitch) for label, pitch in _DRUM_ROW_ORDER if pitch in pitches]
    else:
        rows = [(_pitch_to_name(p), p) for p in sorted(pitches, reverse=True)]

    # step -> {pitch: hit_char} (highest velocity wins if pitches collide on a step)
    hits = {}
    for n in notes:
        try:
            pitch = int(n["pitch"])
        except (KeyError, TypeError, ValueError):
            continue
        step = _quantize_step(n.get("start", 0.0))
        vel = n.get("velocity", 100)
        try:
            vel = int(vel)
        except (TypeError, ValueError):
            vel = 100
        ch = min(_HIT_VELOCITY, key=lambda c: abs(_HIT_VELOCITY[c] - vel))
        cell = hits.setdefault(step, {})
        if pitch not in cell or abs(_HIT_VELOCITY[cell[pitch]] - vel) > abs(_HIT_VELOCITY[ch] - vel):
            cell[pitch] = ch

    # Header: bar numbers over each bar block
    header = "    |"
    for bar in range(n_bars):
        header += str(bar + 1).ljust(_STEPS_PER_BAR) + "|"

    lines = [header.rstrip()]
    label_w = max(len(label) for label, _ in rows)
    for label, pitch in rows:
        line = label.rjust(label_w) + "|"
        for bar in range(n_bars):
            for s in range(_STEPS_PER_BAR):
                line += hits.get(bar * _STEPS_PER_BAR + s, {}).get(pitch, "-")
            line += "|"
        lines.append(line)
    return "\n".join(lines)


def parse_grid(grid: str):
    """Parse ASCII grid text back into note dicts.

    Returns a list of {pitch, start, duration, velocity}. start/duration in beats
    (16th-note grid). Unknown rows are skipped.
    """
    notes = []
    for raw in str(grid).splitlines():
        line = raw.rstrip()
        if "|" not in line:
            continue
        label, _, body = line.partition("|")
        label = label.strip()
        if not label or label.isdigit():
            continue  # header/bar-number row
        pitch = _DRUM_MAP.get(label.upper())
        if pitch is None:
            pitch = _name_to_pitch(label)
        if pitch is None:
            continue
        step = 0
        for ch in body:
            if ch == "|":
                continue  # bar separators don't advance the clock
            if ch in _HIT_VELOCITY:
                notes.append({
                    "pitch": pitch,
                    "start": round(step * _BEATS_PER_STEP, 4),
                    "duration": _BEATS_PER_STEP,
                    "velocity": _HIT_VELOCITY[ch],
                })
            step += 1
    return notes
