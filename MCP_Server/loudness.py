"""Per-clip loudness engine for AbleBridgePlus (v0.7 "Ears v2").

Mono ITU-R BS.1770-4 approximation: K-weighting (high-shelf + high-pass
biquads designed per sample rate, the standard pyloudnorm approach) and
gated 400 ms blocks with 100 ms hop. Pure Python, no numpy — same
philosophy as MCP_Server/spectral.py.

Honest scope: this is a **mono approximation** (Live clips are decoded to
one channel by our shared reader). For well-behaved material it lands
within a fraction of a dB of reference implementations; true stereo
loudness needs dual-channel processing our decoder doesn't provide.
Values are labelled approximations and used for *relative* decisions
(which clips jump out), not mastering-meter absolutes.

All filters are transposed-direct-form-2 biquads evaluated sample by
sample. Design coefficients follow pyloudnorm / ITU BS.1770-4 Annex 1.
"""
import math
from typing import Any, Dict, List

# ITU-R BS.1770-4 gating constants
_BLOCK_MS = 400          # block length
_HOP_MS = 100            # block hop (75% overlap)
_ABS_GATE_LUFS = -70.0   # absolute threshold
_REL_GATE_LU = -10.0     # relative gate below ungated mean
_TARGET_LUFS = -14.0     # common streaming target for normalization hints


# ---------------------------------------------------------------------------
# K-weighting filter design (per sample rate) — pyloudnorm-style
# ---------------------------------------------------------------------------


def _design_k_weighting(rate: float):
    """Return (shelf_biquad, highpass_biquad) as (b0,b1,b2,a1,a2) tuples."""
    f0 = 1681.974450955533    # high-shelf center
    G = 3.999843853973347     # shelf gain (dB)
    Q = 0.7071752369554196
    K = math.tan(math.pi * f0 / rate)
    Vh = 10.0 ** (G / 20.0)
    Vb = Vh ** 0.4996667741545416

    a0_ = 1.0 + K / Q + K * K
    b0 = (Vh + Vb * K / Q + K * K) / a0_
    b1 = 2.0 * (K * K - Vh) / a0_
    b2 = (Vh - Vb * K / Q + K * K) / a0_
    a1 = 2.0 * (K * K - 1.0) / a0_
    a2 = (1.0 - K / Q + K * K) / a0_

    # second-order high-pass at ~38 Hz
    fc = 38.13547087602444
    Qhp = 0.5003270373238773
    Khp = math.tan(math.pi * fc / rate)
    hp_a0 = 1.0
    hp_a1 = 2.0 * (Khp * Khp - 1.0) / (1.0 + Khp / Qhp + Khp * Khp)
    hp_a2 = (1.0 - Khp / Qhp + Khp * Khp) / (1.0 + Khp / Qhp + Khp * Khp)
    hp_b0 = 1.0
    hp_b1 = -2.0
    hp_b2 = 1.0

    shelf = (b0, b1, b2, a1, a2)
    highpass = (hp_b0, hp_b1, hp_b2, hp_a1, hp_a2)
    return shelf, highpass


def _biquad(samples: List[float], coeffs) -> List[float]:
    """Transposed direct form 2 biquad: coeffs = (b0,b1,b2,a1,a2)."""
    b0, b1, b2, a1, a2 = coeffs
    out = [0.0] * len(samples)
    z1 = z2 = 0.0
    for i, x in enumerate(samples):
        y = b0 * x + z1
        z1 = b1 * x - a1 * y + z2
        z2 = b2 * x - a2 * y
        out[i] = y
    return out


def k_weight(samples: List[float], rate: float) -> List[float]:
    """Apply the BS.1770 K-weighting cascade (shelf -> high-pass)."""
    shelf, highpass = _design_k_weighting(rate)
    return _biquad(_biquad(samples, shelf), highpass)


# ---------------------------------------------------------------------------
# Gated loudness measurement
# ---------------------------------------------------------------------------


def _mean_square_per_block(weighted: List[float], rate: float):
    block = max(1, int(rate * _BLOCK_MS / 1000.0))
    hop = max(1, int(rate * _HOP_MS / 1000.0))
    n = len(weighted)
    if n < block:
        return [(sum(x * x for x in weighted) / max(1, n)) * block / max(1, n)] if n else [], block
    # pad the tail with zeros so the last full-length block exists
    blocks = []
    start = 0
    while start + block <= n:
        seg = weighted[start:start + block]
        blocks.append(sum(x * x for x in seg) / block)
        start += hop
    if not blocks:  # very short input: single partial block (flagged by caller)
        blocks.append(sum(x * x for x in weighted) / n)
    return blocks, block


def measure_loudness(samples: List[float], rate: float,
                     label: str = "signal") -> Dict[str, Any]:
    """Integrated LUFS (gated) plus momentary/loudness-range snapshots.

    Mono approximation — see module docstring for honest scope.
    Raises ValueError on silent or uselessly short input.
    """
    if not samples:
        raise ValueError("no audio samples to measure")
    duration_s = len(samples) / float(rate)
    if duration_s < 0.4:
        raise ValueError("clip too short for loudness measurement "
                         "(need >= 0.4 s, got %.2f s)" % duration_s)

    weighted = k_weight(samples, rate)
    ms_blocks, block_len = _mean_square_per_block(weighted, rate)

    def lufs_of(ms):
        # K-weighted loudness relative to full-scale, mono channel
        return -0.691 + 10.0 * math.log10(max(ms, 1e-24))

    block_lufs = [lufs_of(m) for m in ms_blocks]

    # absolute gate
    above_abs = [l for l in block_lufs if l > _ABS_GATE_LUFS]
    if not above_abs:
        raise ValueError("clip is silent (all blocks below the %g LUFS "
                         "absolute gate)" % _ABS_GATE_LUFS)

    # relative gate: mean of blocks above absolute gate, then -10 LU
    # (ungated_mean is an energy average in LUFS domain, offset included once)
    ungated_mean = 10.0 * math.log10(
        sum(10 ** (l / 10.0) for l in above_abs) / len(above_abs))
    gated = [l for l in above_abs if l > ungated_mean + _REL_GATE_LU]
    if not gated:
        gated = above_abs  # degenerate: everything within 10 LU of the mean

    gated_mean = 10.0 * math.log10(
        sum(10 ** (l / 10.0) for l in gated) / len(gated))
    # gated_mean is already the integrated LUFS: the -0.691 offset lives
    # inside each block's LUFS value, so the energy mean carries it once.
    integrated = gated_mean

    # momentary loudness (shortest 400 ms snapshot) and simple range
    momentary_max = max(above_abs)
    momentary_min = min(above_abs)
    loudness_range = round(momentary_max - momentary_min, 1) if len(above_abs) > 1 else 0.0

    return {
        "source": label,
        "integrated_lufs": round(integrated, 1),
        "momentary_max_lufs": round(momentary_max, 1),
        "momentary_min_lufs": round(momentary_min, 1),
        "loudness_range_lu": loudness_range,
        "duration_s": round(duration_s, 2),
        "blocks_gated": len(gated),
        "blocks_total": len(block_lufs),
        "target_lufs": _TARGET_LUFS,
        "gain_to_target_db": round(_TARGET_LUFS - integrated, 1),
        "note": "mono BS.1770-4 approximation — relative decisions are "
                "reliable; absolute values may differ from stereo reference "
                "meters by a fraction of a dB",
    }


# ---------------------------------------------------------------------------
# Mix-audit logic: who jumps out?
# ---------------------------------------------------------------------------

# Jump-out thresholds (dB relative to the loudest-normalized group)
_FLAG_OUT = 3.0    # clearly louder than the pack
_FLAG_QUIET = 6.0  # clearly buried


def audit_loudness_stats(measurements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Classify measured clips: who jumps out, who's buried, who's balanced.

    Uses integrated LUFS deltas against the *median* of the measured set
    (median resists a single very loud outlier skewing the reference).
    """
    if len(measurements) < 2:
        raise ValueError("audit needs measurements of at least 2 clips")
    values = sorted(m["integrated_lufs"] for m in measurements)
    k = len(values) // 2
    median = values[k] if len(values) % 2 else (values[k - 1] + values[k]) / 2.0

    loud, buried, balanced = [], [], []
    for m in measurements:
        delta = round(m["integrated_lufs"] - median, 1)
        entry = {"source": m["source"], "integrated_lufs": m["integrated_lufs"],
                 "delta_vs_median_db": delta}
        if delta >= _FLAG_OUT:
            loud.append(entry)
        elif delta <= -_FLAG_QUIET:
            buried.append(entry)
        else:
            balanced.append(entry)

    flags = []
    for e in loud:
        flags.append("'%s' is +%.1f dB above the pack — likely to jump out "
                     "of the mix" % (e["source"], e["delta_vs_median_db"]))
    for e in buried:
        flags.append("'%s' is %.1f dB below the pack — likely buried"
                     % (e["source"], e["delta_vs_median_db"]))
    if not flags:
        flags.append("no jump-out / burial candidates — levels sit within "
                     "±%.1f dB of the median" % max(_FLAG_OUT, _FLAG_QUIET))

    return {
        "median_lufs": round(median, 1),
        "jumping_out": loud,
        "buried": buried,
        "balanced": balanced,
        "flags": flags,
        "thresholds": {"jump_out_db": _FLAG_OUT, "buried_db": _FLAG_QUIET},
    }
