"""Offline tests for the v0.7 spectral engine (Ears v2).

No Ableton connection needed: FFT correctness is checked against a naive
DFT, and feature behaviour against synthetic signals (sines, noise, mixes).
"""
import math
import random
import sys

import pytest

sys.path.insert(0, ".")

from MCP_Server.spectral import (
    fft,
    analyze_timbre,
    compare_timbre as compare,
    _spectral_flatness,
    _frame_magnitudes,
    _hann_window,
)

RATE = 4410  # DSP rate from audio_intelligence


def naive_dft(x):
    """O(n^2) reference DFT for correctness checking."""
    n = len(x)
    return [sum(x[k] * complex(math.cos(-2 * math.pi * j * k / n),
                               math.sin(-2 * math.pi * j * k / n))
                for k in range(n))
            for j in range(n)]


def _sine(freq, seconds, rate=RATE, amp=0.5):
    n = int(seconds * rate)
    return [amp * math.sin(2 * math.pi * freq * i / rate) for i in range(n)]


# ---------------------------------------------------------------------------
# FFT core
# ---------------------------------------------------------------------------


def test_fft_matches_naive_dft():
    random.seed(7)
    x = [random.uniform(-1, 1) for _ in range(16)]
    got = fft(x)
    want = naive_dft(x)
    for g, w in zip(got, want):
        assert abs(g.real - w.real) < 1e-9
        assert abs(g.imag - w.imag) < 1e-9


def test_fft_rejects_non_power_of_two():
    with pytest.raises(ValueError):
        fft([0.0] * 10)


def test_hann_window_symmetric():
    w = _hann_window(8)
    for i in range(4):
        assert abs(w[i] - w[7 - i]) < 1e-12
    assert w[0] == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Feature behaviour on synthetic signals
# ---------------------------------------------------------------------------


def test_sine_peaks_at_right_frequency():
    fp = analyze_timbre(_sine(440.0, 2.0), RATE, source="a440")
    bin_hz = RATE / 4096
    # within one bin of 440 Hz
    assert abs(fp["peak_frequency_hz"] - 440.0) <= bin_hz * 1.5


def test_sine_centroid_near_frequency():
    fp = analyze_timbre(_sine(440.0, 2.0), RATE, source="a440")
    # Hann sidelobes pull the centroid slightly, but it must stay low hundreds
    assert 400 < fp["spectral_centroid_hz"] < 600


def test_sine_is_tonal_noise_is_noisy():
    tonal = _spectral_flatness(
        _frame_magnitudes(_sine(220.0, 2.0), RATE)[0])
    random.seed(1)
    noise = [random.uniform(-0.5, 0.5) for _ in range(RATE * 2)]
    noisy = _spectral_flatness(_frame_magnitudes(noise, RATE)[0])
    assert tonal < 0.2
    assert noisy > tonal * 3


def test_band_balance_concentrates_correctly():
    fp = analyze_timbre(_sine(100.0, 2.0), RATE, source="low100")
    assert max(fp["band_balance_db"], key=fp["band_balance_db"].get) == "low_60_120"


def test_loudness_of_known_sine():
    fp = analyze_timbre(_sine(220.0, 2.0, amp=0.25), RATE, source="s")
    # sine RMS = amp / sqrt(2) ≈ 0.177 → ≈ -15 dBFS
    assert -16 < fp["loudness"]["rms_dbfs"] < -14
    assert fp["loudness"]["peak_dbfs"] < 0


def test_zero_crossing_rate_of_sine():
    fp = analyze_timbre(_sine(440.0, 1.0), RATE, source="zcr")
    # ideal ZCR for a sine = 2*f/rate
    assert abs(fp["zero_crossing_rate"] - 2 * 440.0 / RATE) < 0.02


def test_short_sample_is_padded_not_crashing():
    fp = analyze_timbre(_sine(440.0, 0.3), RATE, source="short")
    assert fp["peak_frequency_hz"] > 0


def test_empty_samples_raise():
    with pytest.raises(ValueError):
        analyze_timbre([], RATE)


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------


def test_compare_identical_signals_high_similarity():
    a = analyze_timbre(_sine(440.0, 2.0), RATE, source="a")
    b = analyze_timbre(_sine(440.0, 2.0), RATE, source="b")
    out = compare(a, b)
    assert out["band_cosine_similarity"] >= 0.99
    assert any("near-identical" in h for h in out["verdict_hints"])


def test_compare_tone_vs_noise_lower_similarity():
    random.seed(3)
    tone = analyze_timbre(_sine(440.0, 2.0), RATE, source="tone")
    noise = analyze_timbre([random.uniform(-0.5, 0.5)
                            for _ in range(RATE * 2)], RATE, source="noise")
    out = compare(tone, noise)
    assert out["band_cosine_similarity"] < 0.9
    assert out["verdict_hints"]  # always produces hints


def test_compare_missing_bands_raise():
    with pytest.raises(ValueError):
        compare({"band_balance_db": {}}, {"band_balance_db": {}})


# ---------------------------------------------------------------------------
# Tool registration & input validation
# ---------------------------------------------------------------------------


def test_tools_registered():
    from MCP_Server.tools import spectral_analysis as sa
    registered = []

    class _Reg:
        def tool(self):
            def deco(fn):
                registered.append(fn.__name__)
                return fn
            return deco

    sa.register_tools(_Reg())
    assert {"analyze_clip_timbre", "analyze_sample_timbre",
            "compare_timbre"} <= set(registered)


def test_sample_tool_rejects_missing_file():
    from MCP_Server.tools.spectral_analysis import _fingerprint_file
    with pytest.raises(ValueError):
        _fingerprint_file("C:/not/a/real/sample.wav", source="x")
    with pytest.raises(ValueError):
        _fingerprint_file("", source="x")
