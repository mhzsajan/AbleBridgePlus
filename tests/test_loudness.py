"""Offline tests for the v0.7 loudness engine (BS.1770-4 approximation).

Canonical levels are checked against the well-known reference: a 997 Hz
sine at 0.5 amplitude in a stereo pair measures about -20.5 LUFS through
a BS.1770 meter; mono halves that (the -3.01 dB channel sum), which the
tests encode. Gating behaviour is checked with quiet-tail signals.
"""
import math
import sys

import pytest

sys.path.insert(0, ".")

from MCP_Server.loudness import (
    k_weight,
    measure_loudness,
    audit_loudness_stats,
)
from MCP_Server.tools import loudness_analysis as la

RATE = 11025  # engine test rate (matches _LOUDNESS_RATE)


def _sine(freq, seconds, rate=RATE, amp=0.5):
    n = int(seconds * rate)
    return [amp * math.sin(2 * math.pi * freq * i / rate) for i in range(n)]


# ---------------------------------------------------------------------------
# K-weighting
# ---------------------------------------------------------------------------


def test_k_weight_preserves_length_and_is_finite():
    x = _sine(1000.0, 1.0)
    y = k_weight(x, RATE)
    assert len(y) == len(x)
    assert all(math.isfinite(v) for v in y)


def test_k_weight_shelf_boosts_highs():
    # a 5 kHz sine must come out with more energy than a 100 Hz sine of
    # equal input amplitude (shelf +3.99 dB, highpass barely touches 5k)
    low = _sine(100.0, 1.0)
    high = _sine(5000.0, 1.0)
    e = lambda s: sum(v * v for v in s) / len(s)
    e_low_in, e_low_out = e(low), e(k_weight(low, RATE))
    e_high_in, e_high_out = e(high), e(k_weight(high, RATE))
    gain_low = 10 * math.log10(e_low_out / e_low_in)
    gain_high = 10 * math.log10(e_high_out / e_high_in)
    assert gain_high > gain_low + 2.0


# ---------------------------------------------------------------------------
# Gated loudness
# ---------------------------------------------------------------------------


def test_sine_997hz_canonical_level():
    # 997 Hz sine, amp 0.5 (peak -6.02 dBFS), MONO: ms = (0.5/sqrt(2))^2
    # → -0.691 + 10*log10(0.125) = -9.72; the BS.1770 pre-filter is
    # +0.68 dB at 1 kHz by design → expect ≈ -9.0 ± 0.4
    # (the famous -20.5 LUFS reference is a stereo -23 dBFS tone)
    fp = measure_loudness(_sine(997.0, 2.0), RATE, label="canon")
    assert -9.4 < fp["integrated_lufs"] < -8.6


def test_louder_signal_measures_higher():
    a = measure_loudness(_sine(997.0, 2.0, amp=0.5), RATE)
    b = measure_loudness(_sine(997.0, 2.0, amp=1.0), RATE)
    assert b["integrated_lufs"] > a["integrated_lufs"] + 5.0  # 2x amp = +6 dB


def test_gain_to_target_is_consistent():
    fp = measure_loudness(_sine(997.0, 2.0), RATE)
    expected = round(fp["target_lufs"] - fp["integrated_lufs"], 1)
    assert fp["gain_to_target_db"] == expected


def test_relative_gate_ignores_quiet_tail():
    # 4 s of sine followed by 4 s at 1/32 amplitude (=-30 dB): the quiet
    # tail must be gated, so integrated stays close to the loud part's
    # level (within ~0.5 dB), NOT the energy average (which would be ~-3)
    loud = _sine(997.0, 4.0, amp=0.5)
    quiet = _sine(997.0, 4.0, amp=0.5 / 32.0)
    fp = measure_loudness(loud + quiet, RATE, label="tail")
    ref = measure_loudness(loud, RATE)
    assert abs(fp["integrated_lufs"] - ref["integrated_lufs"]) < 0.7


def test_silent_input_raises():
    with pytest.raises(ValueError):
        measure_loudness([0.0] * RATE * 2, RATE)
    with pytest.raises(ValueError):
        measure_loudness([], RATE)


def test_too_short_raises():
    with pytest.raises(ValueError):
        measure_loudness(_sine(997.0, 0.2), RATE)


# ---------------------------------------------------------------------------
# Audit classification
# ---------------------------------------------------------------------------


def _m(name, lufs):
    return {"source": name, "integrated_lufs": lufs}


def test_audit_flags_jump_out_and_buried():
    ms = [_m("kick", -10.0), _m("bass", -11.0), _m("pad", -12.0),
          _m("hat", -18.0), _m("lead", -4.0)]
    out = audit_loudness_stats(ms)
    # sorted [-18, -12, -11, -10, -4] → median is the middle: -11
    assert out["median_lufs"] == -11.0
    names_out = [e["source"] for e in out["jumping_out"]]
    names_bur = [e["source"] for e in out["buried"]]
    assert "lead" in names_out        # +8 dB over median
    assert "hat" in names_bur         # -6 dB under median
    assert "kick" in [e["source"] for e in out["balanced"]]
    assert any("jump out" in f for f in out["flags"])


def test_audit_median_resists_outlier():
    # one extreme clip must not drag the median: 5 clips, one at -1 LUFS
    ms = [_m("a", -14.0), _m("b", -14.0), _m("c", -14.0),
          _m("d", -14.0), _m("loud", -1.0)]
    out = audit_loudness_stats(ms)
    assert out["median_lufs"] == -14.0
    assert [e["source"] for e in out["jumping_out"]] == ["loud"]


def test_audit_all_balanced_message():
    ms = [_m("a", -14.0), _m("b", -14.5), _m("c", -15.0)]
    out = audit_loudness_stats(ms)
    assert out["jumping_out"] == [] and out["buried"] == []
    assert any("no jump-out" in f for f in out["flags"])


def test_audit_needs_two_measurements():
    with pytest.raises(ValueError):
        audit_loudness_stats([_m("solo", -14.0)])


# ---------------------------------------------------------------------------
# Tool surface
# ---------------------------------------------------------------------------


def test_tools_registered():
    registered = []

    class _Reg:
        def tool(self):
            def deco(fn):
                registered.append(fn.__name__)
                return fn
            return deco

    la.register_tools(_Reg())
    assert {"measure_clip_loudness", "audit_mix_loudness"} <= set(registered)


def test_measure_path_rejects_missing(tmp_path):
    with pytest.raises(ValueError):
        la._measure_path(str(tmp_path / "nope.wav"), label="x")
