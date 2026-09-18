"""Offline tests for the v0.7 downbeat-aware BPM refinement engine.

Test signals are synthesized with clicks on an exact 120 BPM grid (and
75/100 BPM variants) plus noise, then the raw autocorrelation estimate is
deliberately perturbed (~1.5% error, like the real detector) to check
that the grid scorer snaps back to the exact value — while a constant
tempo and a raw estimate that is already musical must survive unchanged.
"""
import math
import random
import sys

import pytest

sys.path.insert(0, ".")

from MCP_Server.downbeat import _fold_to_range, refine_bpm

RATE = 11025  # test rate


def _clicks(bpm, seconds, rate=RATE, amp=0.6, seed=42):
    """Quarter-note click grid + gentle noise, rendered as floats."""
    rnd = random.Random(seed)
    n = int(seconds * rate)
    samples = [0.0] * n
    period = 60.0 / bpm * rate
    t = 0.0
    while t < n:
        start = int(t)
        decay = int(0.06 * rate)
        for i in range(min(decay, n - start)):
            env = math.exp(-i / (0.012 * rate))
            samples[start + i] += amp * env * math.sin(
                2 * math.pi * 1000.0 * i / rate)
        t += period
    for i in range(n):
        samples[i] += 0.02 * (rnd.random() * 2 - 1)
    return samples


def _perturb(bpm, frac=0.015):
    return bpm * (1.0 + frac)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def test_fold_to_range_doubles_and_halves():
    assert _fold_to_range(40.0) == pytest.approx(80.0)
    assert _fold_to_range(300.0) == pytest.approx(150.0)  # one fold, then in-range
    assert _fold_to_range(120.0) == pytest.approx(120.0)


def test_requires_raw_estimate():
    with pytest.raises(ValueError):
        refine_bpm([0.0] * 44100, RATE, None)


# ---------------------------------------------------------------------------
# snapping behaviour
# ---------------------------------------------------------------------------


def test_click_track_120_snaps_from_1p5_percent_error():
    samples = _clicks(120.0, 14.0)
    raw = _perturb(120.0)  # 121.8 — the classic autocorrelation miss
    r = refine_bpm(samples, RATE, raw)
    assert r["refined"] is True
    assert r["bpm"] == pytest.approx(120.0, abs=0.2)
    assert r["confidence"] > 0.3
    # downbeat phase must sit on a click (within a quarter of the period)
    period_sec = 60.0 / 120.0
    assert r["downbeat_offset_seconds"] < period_sec


def test_click_track_100_snaps():
    samples = _clicks(100.0, 15.0)
    raw = _perturb(100.0, 0.012)
    r = refine_bpm(samples, RATE, raw)
    assert r["bpm"] == pytest.approx(100.0, abs=0.25)


def test_click_track_75_snaps_upward():
    samples = _clicks(75.0, 20.0)
    raw = _perturb(75.0, -0.014)  # 73.95
    r = refine_bpm(samples, RATE, raw)
    assert r["bpm"] == pytest.approx(75.0, abs=0.3)


# ---------------------------------------------------------------------------
# conservativeness
# ---------------------------------------------------------------------------


def test_constant_tone_is_not_refined():
    # no onsets -> honest no-op with a reason, raw value kept
    n = int(8.0 * RATE)
    samples = [0.4 * math.sin(2 * math.pi * 440.0 * i / RATE) for i in range(n)]
    r = refine_bpm(samples, RATE, 120.3)
    assert r["refined"] is False
    assert r["bpm"] == 120.3
    assert "reason" in r


def test_already_musical_raw_survives():
    # raw lands exactly on the true grid tempo: tie-break keeps it
    samples = _clicks(120.0, 14.0)
    r = refine_bpm(samples, RATE, 120.0)
    assert r["bpm"] == pytest.approx(120.0, abs=0.2)
    # and the second-run stays put too (idempotent for exact inputs)
    r2 = refine_bpm(samples, RATE, r["bpm"])
    assert r2["bpm"] == pytest.approx(120.0, abs=0.2)


def test_near_tie_snaps_to_musical_tempo():
    # Regression: a raw estimate just under a musical tempo (89.9 vs 90.0)
    # used to keep the raw candidate because the tie-break pool always
    # contained the raw candidate at distance 0 — the snap could never fire
    # on a near-tie. Found live on 'Akeem Groove 120 bpm.wav'.
    samples = _clicks(90.0, 14.0)
    r = refine_bpm(samples, RATE, 89.9)
    assert r["bpm"] == pytest.approx(90.0, abs=0.2)
    assert r["snap_delta_cents"] is not None


def test_too_short_audio_is_honest_noop():
    r = refine_bpm([0.1, -0.1] * 200, RATE, 120.0)
    assert r["refined"] is False
    assert "reason" in r


# ---------------------------------------------------------------------------
# registration
# ---------------------------------------------------------------------------


def test_tools_registered():
    from MCP_Server.tools import audio_intelligence as ai
    registered = []

    class _Reg:
        def tool(self, *a, **k):
            def deco(fn):
                registered.append(fn.__name__)
                return fn
            return deco

    ai.register_tools(_Reg())
    assert "analyze_audio_key_bpm" in registered
