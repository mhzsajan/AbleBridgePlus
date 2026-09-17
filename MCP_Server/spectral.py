"""Spectral engine for AbleBridgePlus (v0.7 "Ears v2").

Real FFT in pure Python (iterative radix-2 Cooley–Tukey) plus the timbre
feature set an AI needs to reason about sound: spectral centroid (brightness),
roll-off, flatness (tonal vs noisy), zero-crossing rate, per-band energies
and the loudest peak frequency.

No numpy — Live-adjacent tooling stays dependency-light. A 4096-point FFT
costs ~50k butterflies; analysis of a 10–15 s clip at the DSP sample rate
runs in a couple of seconds, well inside tool timeouts.

All magnitudes are linear-averaged across frames; band energies are reported
in dB relative to the loudest band (same convention as mix_matching).
"""
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Engine constants
_FFT_SIZE = 4096
_MAX_ANALYZE_SECONDS = 15.0

# Analysis bands (Hz): sub, low, low-mid, mid, high-mid, high
_SPECTRAL_BANDS = [
    ("sub_20_60", 20.0, 60.0),
    ("low_60_120", 60.0, 120.0),
    ("lowmid_120_400", 120.0, 400.0),
    ("mid_400_2000", 400.0, 2000.0),
    ("highmid_2000_6000", 2000.0, 6000.0),
    ("high_6000_16000", 6000.0, 16000.0),
]


# ---------------------------------------------------------------------------
# Core FFT
# ---------------------------------------------------------------------------


def fft(magnitudes: List[float]) -> List[complex]:
    """Iterative radix-2 Cooley–Tukey FFT. len(x) must be a power of two.

    Pure Python, in-place on a complex copy. Returns the DFT of x.
    """
    n = len(magnitudes)
    if n == 0 or (n & (n - 1)) != 0:
        raise ValueError("fft size must be a power of two, got %d" % n)
    a = [complex(v, 0.0) for v in magnitudes]

    # bit-reversal permutation
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j |= bit
        if i < j:
            a[i], a[j] = a[j], a[i]

    # butterfly passes
    length = 2
    while length <= n:
        half = length >> 1
        ang = -2.0 * math.pi / length
        wlen = complex(math.cos(ang), math.sin(ang))
        for start in range(0, n, length):
            w = 1.0 + 0.0j
            for k in range(half):
                u = a[start + k]
                v = a[start + k + half] * w
                a[start + k] = u + v
                a[start + k + half] = u - v
                w *= wlen
        length <<= 1
    return a


def _hann_window(n: int) -> List[float]:
    return [0.5 * (1.0 - math.cos(2.0 * math.pi * i / (n - 1))) for i in range(n)]


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------


def _frame_magnitudes(samples: List[float], rate: int,
                      fft_size: int = _FFT_SIZE) -> List[List[float]]:
    """Windowed magnitude spectra of successive frames (linear)."""
    if len(samples) < fft_size:
        # zero-pad short samples up to one frame
        samples = samples + [0.0] * (fft_size - len(samples))
    window = _hann_window(fft_size)
    spectra: List[List[float]] = []
    # non-overlapping frames, capped so a long file can't stall the tool
    max_frames = max(1, int(_MAX_ANALYZE_SECONDS * rate) // fft_size)
    for start in range(0, len(samples) - fft_size + 1, fft_size):
        if len(spectra) >= max_frames:
            break
        frame = [s * w for s, w in zip(samples[start:start + fft_size], window)]
        spec = fft(frame)
        mags = [abs(c) for c in spec[: fft_size // 2]]  # keep positive freqs
        spectra.append(mags)
    return spectra


def _avg_spectrum(spectra: List[List[float]]) -> List[float]:
    n = len(spectra[0])
    acc = [0.0] * n
    for spec in spectra:
        for i, m in enumerate(spec):
            acc[i] += m
    k = float(len(spectra))
    return [v / k for v in acc]


def _spectral_centroid(mags: List[float], rate: int, fft_size: int) -> float:
    num = 0.0
    den = 0.0
    bin_hz = rate / fft_size
    for i, m in enumerate(mags):
        f = i * bin_hz
        num += f * m
        den += m
    return (num / den) if den > 1e-12 else 0.0


def _spectral_rolloff(mags: List[float], rate: int, fft_size: int,
                      threshold: float = 0.85) -> float:
    total = sum(mags)
    if total <= 1e-12:
        return 0.0
    cum = 0.0
    bin_hz = rate / fft_size
    for i, m in enumerate(mags):
        cum += m
        if cum >= threshold * total:
            return i * bin_hz
    return (len(mags) - 1) * bin_hz


def _spectral_flatness(mags: List[float]) -> float:
    """Gini-ish tonal vs noise measure: 0 = pure tone, 1 = white noise.

    Uses power bins; log-domain geometric mean keeps it numerically safe.
    """
    power = [max(m * m, 1e-20) for m in mags]
    log_sum = sum(math.log(p) for p in power)
    geo = math.exp(log_sum / len(power))
    ari = sum(power) / len(power)
    return round(geo / ari, 4) if ari > 0 else 0.0


def _zero_crossing_rate(samples: List[float]) -> float:
    if len(samples) < 2:
        return 0.0
    crossings = 0
    for i in range(1, len(samples)):
        if (samples[i - 1] >= 0) != (samples[i] >= 0):
            crossings += 1
    return round(crossings / (len(samples) - 1), 4)


def _band_energies(mags: List[float], rate: int, fft_size: int) -> Dict[str, float]:
    """Mean magnitude per band, normalized to dB relative to the loudest band."""
    bin_hz = rate / fft_size
    acc: Dict[str, float] = {}
    counts: Dict[str, int] = {}
    for name, lo, hi in _SPECTRAL_BANDS:
        s = 0.0
        c = 0
        for i, m in enumerate(mags):
            if lo <= i * bin_hz < hi:
                s += m
                c += 1
        acc[name] = s / c if c else 0.0
        counts[name] = c
    peak = max(acc.values()) if acc else 0.0
    if peak <= 1e-12:
        return {name: -70.0 for name in acc}
    return {name: round(20.0 * math.log10(max(v, 1e-9) / peak), 1)
            for name, v in acc.items()}


def _peak_frequency(mags: List[float], rate: int, fft_size: int) -> float:
    if not mags:
        return 0.0
    bin_hz = rate / fft_size
    idx = max(range(len(mags)), key=lambda i: mags[i])
    return round(idx * bin_hz, 1)


# ---------------------------------------------------------------------------
# Public analysis entry points
# ---------------------------------------------------------------------------


def analyze_timbre(samples: List[float], rate: int,
                   source: str = "signal") -> Dict[str, Any]:
    """Full timbre fingerprint of a mono sample buffer.

    Returns spectral features averaged over frames plus band balance.
    """
    if not samples:
        raise ValueError("no audio samples to analyze")
    spectra = _frame_magnitudes(samples, rate)
    if not spectra:
        raise ValueError("sample too short for spectral analysis "
                         "(need at least one %d-sample frame)" % _FFT_SIZE)
    avg = _avg_spectrum(spectra)

    # loudness snapshot (same convention as mix_matching._loudness_profile)
    sq = sum(x * x for x in samples) / len(samples)
    peak = max(abs(x) for x in samples)
    rms_db = round(20.0 * math.log10(max(math.sqrt(sq), 1e-9)), 1)
    peak_db = round(20.0 * math.log10(max(peak, 1e-9)), 1)

    return {
        "source": source,
        "fft": {"size": _FFT_SIZE, "window": "hann",
                "frames_averaged": len(spectra),
                "bin_hz": round(rate / _FFT_SIZE, 2)},
        "spectral_centroid_hz": round(_spectral_centroid(avg, rate, _FFT_SIZE), 1),
        "spectral_rolloff_hz": round(_spectral_rolloff(avg, rate, _FFT_SIZE), 1),
        "spectral_flatness": _spectral_flatness(avg),
        "zero_crossing_rate": _zero_crossing_rate(samples),
        "peak_frequency_hz": _peak_frequency(avg, rate, _FFT_SIZE),
        "band_balance_db": _band_energies(avg, rate, _FFT_SIZE),
        "loudness": {"rms_dbfs": rms_db, "peak_dbfs": peak_db,
                     "crest_factor_db": round(peak_db - rms_db, 1)},
        "note": ("flatness: 0 = pure tone, 1 = white noise; centroid/rolloff in Hz; "
                 "band_balance_db relative to the loudest band"),
    }


def compare_timbre(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two timbre fingerprints (e.g. a sample vs a clip).

    Cosine similarity over the band-balance vectors (scale-invariant shape
    match) plus absolute centroid/flatness deltas with plain-language hints.
    """
    bands_a = a.get("band_balance_db", {})
    bands_b = b.get("band_balance_db", {})
    keys = [k for k in bands_a if k in bands_b]
    if not keys:
        raise ValueError("fingerprints have no bands in common")
    va = [bands_a[k] for k in keys]
    vb = [bands_b[k] for k in keys]
    dot = sum(x * y for x, y in zip(va, vb))
    na = math.sqrt(sum(x * x for x in va)) or 1e-12
    nb = math.sqrt(sum(y * y for y in vb)) or 1e-12
    similarity = round(dot / (na * nb), 3)

    centroid_delta = round(a.get("spectral_centroid_hz", 0)
                           - b.get("spectral_centroid_hz", 0), 1)
    flatness_delta = round(a.get("spectral_flatness", 0)
                           - b.get("spectral_flatness", 0), 3)
    diffs = {k: round(bands_a[k] - bands_b[k], 1) for k in keys}
    biggest = max(diffs, key=lambda k: abs(diffs[k])) if diffs else None

    hints: List[str] = []
    if similarity >= 0.98:
        hints.append("band shapes are near-identical — same tonal character")
    elif similarity >= 0.9:
        hints.append("close overall shape with small band differences")
    else:
        hints.append("clearly different tonal shapes")
    if centroid_delta > 500:
        hints.append("'%s' is brighter (centroid %.0f Hz higher)"
                     % (a.get("source", "A"), centroid_delta))
    elif centroid_delta < -500:
        hints.append("'%s' is darker (centroid %.0f Hz lower)"
                     % (a.get("source", "A"), abs(centroid_delta)))
    if biggest and abs(diffs[biggest]) >= 3:
        hints.append("largest band gap: %s at %+0.1f dB" % (biggest, diffs[biggest]))

    return {
        "band_cosine_similarity": similarity,
        "centroid_delta_hz": centroid_delta,
        "flatness_delta": flatness_delta,
        "band_deltas_db": diffs,
        "verdict_hints": hints,
    }
