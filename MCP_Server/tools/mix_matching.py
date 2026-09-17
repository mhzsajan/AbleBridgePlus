"""Whole-mix reference matching for AbleBridgePlus (v0.6 theme 3).

Server-side DSP on a reference audio file: full tonal balance (6 bands,
relative dB), loudness profile, key and BPM — reusing the audio_intelligence
DSP core. Live-side, the master output meters are sampled over time so the
AI can compare loudness behaviour against the reference.

Honest scope note: Live's API exposes only broadband master meters (no
per-band spectrum), so tonal-gap comparison is *reference-vs-reference-class
knowledge* + live loudness. `analyze_reference_mix` reports the reference's
fingerprint in numbers an AI can reason about; `match_reference_mix` adds
the live master-meter sampling and produces concrete, checkpoint-safe fix
suggestions. This is the roadmap's "your mix is 3 dB light below 100 Hz"
report, with the broadband caveat stated plainly.
"""
import json
import logging
import math
import os
import time
from typing import Any, Dict, List

from mcp.server.fastmcp import Context

from MCP_Server.tools._base import _tool_handler
from MCP_Server.connections.ableton import get_ableton_connection
from MCP_Server.tools.audio_intelligence import (
    _read_audio_mono,
    _detect_key,
    _detect_bpm,
    _chroma,
)

logger = logging.getLogger(__name__)

# Analysis bands (Hz): sub, low, low-mid, mid, high-mid, high
_BANDS = [
    ("sub_20_60", 20.0, 60.0),
    ("low_60_120", 60.0, 120.0),
    ("lowmid_120_400", 120.0, 400.0),
    ("mid_400_2000", 400.0, 2000.0),
    ("highmid_2000_6000", 2000.0, 6000.0),
    ("high_6000_16000", 6000.0, 16000.0),
]


# ---------------------------------------------------------------------------
# DSP: band energies of the reference file (Goertzel probes across each band)
# ---------------------------------------------------------------------------


def _band_energies(samples, rate) -> Dict[str, float]:
    """Average Goertzel magnitude per band across windows of the sample."""
    def mag(freq):
        # Goertzel magnitude at one frequency (from audio_intelligence core)
        n = len(samples)
        k = freq * n / rate
        wr = 2.0 * math.pi * k / n
        coeff = 2.0 * math.cos(wr)
        s_prev = s_prev2 = 0.0
        for x in samples:
            s = x + coeff * s_prev - s_prev2
            s_prev2 = s_prev
            s_prev = s
        return math.sqrt(s_prev2 * s_prev2 + s_prev * s_prev - coeff * s_prev * s_prev2)

    out = {}
    step = max(rate, len(samples) // 8)  # 8 probe windows across the file
    probes = range(0, max(1, len(samples) - rate), step)
    for name, lo, hi in _BANDS:
        # 8 log-spaced probe frequencies inside the band
        freqs = [lo * (hi / lo) ** (i / 7.0) for i in range(8)]
        acc = 0.0
        count = 0
        for start in probes:
            window = samples[start:start + rate]  # ~1 s window
            if len(window) < rate // 2:
                continue
            for f in freqs:
                acc += mag(f)
                count += 1
        out[name] = (acc / count) if count else 0.0
    return out


def _to_relative_db(energies: Dict[str, float]) -> Dict[str, float]:
    """Normalize band magnitudes to dB relative to the loudest band.

    Relative balance is what transfers between masters of different
    absolute loudness — the number an AI can actually act on.
    """
    mags = {k: max(v, 1e-9) for k, v in energies.items()}
    peak = max(mags.values())
    return {k: round(20.0 * math.log10(v / peak), 1) for k, v in mags.items()}


def _loudness_profile(samples, rate) -> Dict[str, Any]:
    """Rough broadband loudness behaviour: RMS + crest factor."""
    if not samples:
        return {}
    n = len(samples)
    sq = 0.0
    peak = 0.0
    for x in samples:
        sq += x * x
        ax = abs(x)
        if ax > peak:
            peak = ax
    rms = math.sqrt(sq / n) if n else 0.0
    rms_db = round(20.0 * math.log10(max(rms, 1e-9)), 1)
    peak_db = round(20.0 * math.log10(max(peak, 1e-9)), 1)
    crest = round(peak_db - rms_db, 1)
    return {"rms_dbfs": rms_db, "peak_dbfs": peak_db, "crest_factor_db": crest}


def analyze_reference_file(path: str) -> Dict[str, Any]:
    """Full server-side fingerprint of a reference audio file."""
    if not path or not path.strip():
        raise ValueError("reference_path is required")
    path = path.strip()
    if not os.path.isfile(path):
        raise ValueError("reference file not found on disk: " + path)
    samples, rate = _read_audio_mono(path)
    if not samples:
        raise ValueError(
            "unsupported or unreadable audio file (wav/aiff supported; "
            "mp3/flac/ogg are not — convert the reference to wav first)")
    bands = _to_relative_db(_band_energies(samples, rate))
    loud = _loudness_profile(samples, rate)
    key = _detect_key(_chroma(samples, rate))
    bpm = _detect_bpm(samples, rate)
    return {
        "reference_path": path,
        "tonal_balance_db": bands,
        "loudness": loud,
        "key_estimate": key,
        "bpm_estimate": bpm,
        "analyzed_seconds": round(len(samples) / rate, 1),
        "note": "band values are dB relative to the loudest band — the "
                "shape of the spectrum, not absolute EQ",
    }


# ---------------------------------------------------------------------------
# Live-side: master meter sampling over a playback window
# ---------------------------------------------------------------------------


def _linear_to_db(v: float) -> float:
    """Live meters are linear 0..1; convert to dBFS with a -70 dB floor."""
    return round(20.0 * math.log10(max(float(v), 10 ** (-70 / 20))), 1)


def sample_master_meters(seconds: float = 10.0, interval: float = 0.25,
                         max_samples: int = 120) -> Dict[str, Any]:
    """Sample the master output meters for ~seconds while Live plays.

    Returns per-sample dBFS plus aggregate stats. Raises if Live is not
    playing or if the master carries no signal at all (muted tracks,
    silent audio device) — silence would make the comparison garbage.
    """
    conn = get_ableton_connection()

    def meters():
        # send_command returns the result payload directly; failures raise
        return conn.send_command("get_master_meters")

    transport = conn.send_command("get_song_transport")
    playing = transport.get("is_playing")
    if not playing:
        raise ValueError("Live is not playing — start playback first so the "
                         "master meters carry real signal")

    samples: List[Dict[str, Any]] = []
    deadline = time.time() + min(float(seconds), 60.0)
    while time.time() < deadline and len(samples) < max_samples:
        m = meters()
        left = m.get("output_meter_left")
        right = m.get("output_meter_right")
        level = m.get("output_meter_level")
        linear = None
        for candidate in (level, left, right):
            if candidate is not None:
                linear = max(linear, float(candidate)) if linear is not None else float(candidate)
        if linear is not None:
            samples.append({"t": round(time.time(), 2),
                            "db": _linear_to_db(linear)})
        time.sleep(max(0.05, float(interval)))

    if not samples:
        raise RuntimeError("no meter samples collected — is anything audible?")

    floor = -70.0
    active = [s["db"] for s in samples if s["db"] > floor]
    if not active:
        raise ValueError(
            "master is silent (all samples at the -70 dB floor) — a track may "
            "be muted, the scene empty, or the audio output device is not "
            "routing; play something audible and re-run")

    dbs = active
    avg = sum(dbs) / len(dbs)
    peak = max(s["db"] for s in samples)
    return {
        "duration_s": round(samples[-1]["t"] - samples[0]["t"], 1),
        "sample_count": len(samples),
        "avg_db": round(avg, 1),
        "peak_db": round(peak, 1),
        "min_active_db": round(min(dbs), 1),
        "silent_samples": len(samples) - len(active),
        "samples": samples,
    }


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def register_tools(mcp):
    @mcp.tool()
    @_tool_handler("analyzing a reference mix")
    def analyze_reference_mix(ctx: Context, reference_path: str) -> str:
        """
        Analyze a reference audio file for whole-mix matching: 6-band tonal
        balance (dB relative to the loudest band), loudness profile
        (RMS / peak / crest), key and BPM estimates.

        This is the server-side half of reference matching — run it on the
        song you want yours to sit next to. Pair with `match_reference_mix`
        to also sample Live's master meters and get fix suggestions.
        WAV/AIFF only (convert mp3/flac references to wav first).
        """
        result = analyze_reference_file(reference_path)
        return json.dumps(result, indent=2)

    @mcp.tool()
    @_tool_handler("matching your mix to a reference")
    def match_reference_mix(ctx: Context, reference_path: str,
                            sample_seconds: float = 10.0) -> str:
        """
        Whole-mix reference comparison: analyzes the reference file's tonal
        balance and loudness, then samples Live's master output meters for
        ~sample_seconds during playback and reports how your mix's loudness
        behaviour differs, with concrete checkpoint-safe fix candidates.

        Honest scope: Live exposes broadband master meters only — the
        tonal comparison uses the reference's band shape as an AI-readable
        target, while the live side contributes real loudness/crest numbers.
        Requires Live to be playing. Automatic checkpoints make any fix you
        apply reversible via rollback.
        """
        ref = analyze_reference_file(reference_path)
        try:
            live = sample_master_meters(sample_seconds)
        except ValueError:
            raise
        except Exception as e:
            ref["live_sampling"] = {"error": str(e),
                                    "hint": "fix the Live connection and re-run"}
            return json.dumps(ref, indent=2)

        # Gap reasoning in numbers an AI can act on
        ref_rms = ref.get("loudness", {}).get("rms_dbfs")
        ref_crest = ref.get("loudness", {}).get("crest_factor_db")
        live_avg = live.get("avg_db")
        live_crest = round(live.get("peak_db", 0) - live.get("avg_db", 0), 1)
        gaps: List[str] = []
        if ref_rms is not None and live_avg is not None:
            diff = round(live_avg - ref_rms, 1)
            if diff <= -3:
                gaps.append("your mix plays ~%.1f dB quieter on average than the "
                            "reference — consider master gain/limiting" % abs(diff))
            elif diff >= 3:
                gaps.append("your mix plays ~%.1f dB hotter than the reference — "
                            "check for over-compression before turning down" % diff)
        if ref_crest is not None and live_crest:
            cdiff = round(live_crest - ref_crest, 1)
            if cdiff <= -3:
                gaps.append("crest factor %.1f dB lower than the reference — "
                            "your mix may be over-compressed (drums losing punch)" % abs(cdiff))
            elif cdiff >= 3:
                gaps.append("crest factor %.1f dB higher than the reference — "
                            "more dynamic but likely quieter overall; check glue" % cdiff)

        report = {
            "reference": ref,
            "live_master": {k: v for k, v in live.items() if k != "samples"},
            "gaps": gaps,
            "candidate_fixes": [
                "roll back anytime — automatic checkpoints captured every mutation",
                "loudness gap: raise master gain or add gentle limiting on the master chain",
                "crest gap (over-compressed): ease compressor ratios/release on buses",
                "band gaps: compare reference tonal_balance_db against your EQ choices "
                "per bus (sub_20_60 for weight, high_6000_16000 for air)",
            ],
            "scope_note": "per-band comparison of the LIVE signal is not possible "
                          "with Live's broadband meters; use analyze_reference_mix "
                          "numbers alongside per-track meter reads for EQ decisions",
        }
        return json.dumps(report, indent=2)
