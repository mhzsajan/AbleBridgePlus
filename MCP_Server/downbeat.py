"""Downbeat-aware BPM refinement for AbleBridgePlus (v0.7 "Ears v2").

The onset-autocorrelation tempo estimate lands within ~1.5% of the true
tempo but almost never on it — 121.6 instead of 120.0. This module snaps
it using onset-pattern matching:

1. Build an onset-strength envelope from the sample (rectified
   derivative of the block RMS — the same envelope _detect_bpm uses).
2. Snap the raw estimate to plausible *musical* tempi (a table of common
   production tempos, plus the raw value itself as a fallback).
3. Score every candidate tempo by phase-aligned grid energy: for each
   candidate period, scan all phases and sum the onset strength on the
   beat grid, half-grid (eighths) and quarter-grid (sixteenths). Real
   music puts energy on grid lines; a 1.3% tempo error drifts off them
   after a couple of bars and scores visibly worse.
4. Pick the best-scoring candidate, tie-breaking toward the raw
   estimate (this module snaps, it does not re-decide the tempo octave).

Returns the refined BPM, the downbeat offset (seconds into the analyzed
audio where beat 1 of a bar sits, assuming 4/4), and a confidence score.

Pure Python, no numpy — same philosophy as MCP_Server/spectral.py.
Note: offsets are relative to the start of the audio you pass in; the
shared reader analyzes the middle 30 s of long files, so at tool level
the offset is relative to that segment.
"""
import math

_ENVELOPE_BLOCK = 128          # same block size as _detect_bpm
_MIN_BPM, _MAX_BPM = 70.0, 180.0

# Common production tempos (plus everything in between is snapped to the
# nearest of these within the candidate window).
_MUSICAL_TEMPI = [
    70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 128,
    130, 132, 135, 140, 145, 150, 155, 160, 165, 170, 175, 180,
]

_CANDIDATE_WINDOW = 1.6        # candidates within raw/1.6 .. raw*1.6
_TIE_TOLERANCE = 0.97          # candidates scoring >= 97% of best tie
_OCTAVE_GUARD = 0.04           # "different tempo" means >4% apart


def _fold_to_range(bpm):
    """Fold a tempo into the 70-180 range by doubling/halving."""
    bpm = float(bpm)
    while bpm < _MIN_BPM:
        bpm *= 2.0
    while bpm > _MAX_BPM:
        bpm /= 2.0
    return bpm


def _onset_envelope(samples):
    """Rectified derivative of the block-RMS envelope (mean-subtracted).

    Returns (onset, env_peak) — the peak envelope level is used by the
    caller to gate tiny systematic ripple (a pure sine's block-RMS
    varies slightly with the partial cycle at window edges, which must
    not be mistaken for musical onsets).
    """
    block = _ENVELOPE_BLOCK
    env = []
    for i in range(0, len(samples) - block + 1, block):
        acc = 0.0
        for j in range(block):
            acc += samples[i + j] * samples[i + j]
        env.append(math.sqrt(acc / block))
    if len(env) < 12:
        return [], 0.0
    onset = [max(0.0, env[i] - env[i - 1]) for i in range(1, len(env))]
    mean = sum(onset) / len(onset)
    return [o - mean for o in onset], max(env)


def _grid_score(onset, period, phase):
    """Mean onset energy on the beat/half/quarter grid for one phase."""
    n = len(onset)

    def _mean(start, step):
        acc = 0.0
        cnt = 0
        idx = start
        while idx < n:
            acc += onset[int(idx)]
            cnt += 1
            idx += step
        return acc / cnt if cnt else 0.0

    beats = _mean(phase, period)
    eighths = 0.5 * (_mean(phase + period * 0.5, period) or 0.0)
    sixteenths = 0.25 * (
        _mean(phase + period * 0.25, period) +
        _mean(phase + period * 0.75, period)) / 2.0
    return beats + eighths + sixteenths


def _score_candidate(onset, bps, bpm):
    """Best phase-aligned grid score for one candidate tempo."""
    period = 60.0 * bps / bpm
    n_phases = max(4, int(round(period)))
    best = (-1e18, 0.0)
    all_scores = []
    for phase in range(n_phases):
        s = _grid_score(onset, period, float(phase))
        all_scores.append(s)
        if s > best[0]:
            best = (s, float(phase))
    scores = sorted(all_scores)
    median = scores[len(scores) // 2]
    sharpness = 0.0
    denom = max(abs(best[0]), 1e-9)
    if abs(median) > 1e-12:
        sharpness = max(0.0, min(1.0, (best[0] - median) / denom))
    return {"bpm": bpm, "score": best[0], "phase": best[1],
            "sharpness": sharpness}


def refine_bpm(samples, rate, raw_bpm):
    """Snap a raw autocorrelation BPM estimate to the musical grid.

    Returns a dict with the refined bpm, downbeat offset (seconds into
    `samples` where beat 1 of a 4/4 bar sits), confidence and diagnostics.
    Raises ValueError if no raw estimate is supplied.
    """
    if raw_bpm is None:
        raise ValueError("refine_bpm needs a raw autocorrelation estimate")
    raw = _fold_to_range(raw_bpm)
    result = {
        "method": "onset-grid",
        "raw_bpm": round(raw, 2),
        "bpm": round(raw, 2),
        "refined": False,
        "confidence": 0.0,
        "downbeat_offset_seconds": 0.0,
        "bar_beats": 4,
    }

    onset, env_peak = _onset_envelope(samples)
    if not onset:
        result["reason"] = "audio too short to build an onset envelope"
        return result
    peak = max(onset) if onset else 0.0
    if peak < max(1e-5, 0.02 * env_peak):
        result["reason"] = "no meaningful onsets (steady or silent audio)"
        return result

    bps = rate / _ENVELOPE_BLOCK
    raw_c = _score_candidate(onset, bps, raw)
    raw_c["musical"] = False
    candidates = {round(raw, 1): raw_c}
    for t in _MUSICAL_TEMPI:
        t = float(_fold_to_range(t))
        if raw * (1.0 / _CANDIDATE_WINDOW) <= t <= raw * _CANDIDATE_WINDOW:
            c = _score_candidate(onset, bps, t)
            c["musical"] = True
            candidates[round(t, 1)] = c
    cand_list = list(candidates.values())
    cand_list.sort(key=lambda c: c["score"], reverse=True)
    best = cand_list[0]

    # Prefer a musical tempo sitting within ~25 cents (1.4%) of the raw
    # estimate. At that distance autocorrelation error and the true tempo
    # are indistinguishable, and the module's premise is that real
    # productions sit on musical tempi (found live: 89.9 vs 90.0, where
    # the raw candidate's own grid score can edge out the musical one and
    # a pure score tie-break stays on the raw value forever).
    musical_near = [c for c in cand_list
                    if c.get("musical")
                    and 0.05 < abs(c["bpm"] - raw) <= 0.0145 * raw]
    if musical_near:
        chosen = min(musical_near, key=lambda c: abs(c["bpm"] - raw))
    else:
        # tie-break: among near-best scorers, stay closest to the raw
        # estimate. The raw candidate always ties itself perfectly, so
        # exclude it from the near-tie pool when a musical candidate ties.
        pool = [c for c in cand_list
                if c["score"] >= _TIE_TOLERANCE * best["score"]]
        musical_pool = [c for c in pool if abs(c["bpm"] - raw) > 0.05]
        chosen = min(musical_pool or pool, key=lambda c: abs(c["bpm"] - raw))

    # confidence: margin over a genuinely different tempo + phase sharpness
    others = [c for c in cand_list
              if abs(c["bpm"] - chosen["bpm"]) > _OCTAVE_GUARD * chosen["bpm"]]
    margin = 0.0
    if others and best["score"] > 0:
        second = others[0]["score"]
        margin = max(0.0, min(1.0, (chosen["score"] - second) / best["score"] * 6.0))
    confidence = max(0.0, min(1.0, 0.5 * margin + 0.5 * chosen["sharpness"]))

    delta_cents = None
    if abs(chosen["bpm"] - raw) > 0.05:
        delta_cents = round(1200.0 * math.log2(chosen["bpm"] / raw), 1)

    result.update({
        "bpm": round(chosen["bpm"], 2),
        "refined": True,
        "confidence": round(confidence, 2),
        "downbeat_offset_seconds": round(chosen["phase"] / bps, 4),
        "snap_delta_cents": delta_cents,
        "candidates_scored": len(cand_list),
    })
    return result
