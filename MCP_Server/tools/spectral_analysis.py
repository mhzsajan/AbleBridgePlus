"""Spectral analysis tools for AbleBridgePlus (v0.7 "Ears v2").

Per-clip timbre awareness: the AI can now describe HOW something sounds,
not just what key it's in. Built on the pure-Python spectral engine
(MCP_Server/spectral.py, iterative Cooley–Tukey FFT, no numpy).

Tools:
- analyze_clip_timbre: full spectral fingerprint of an audio clip in the set
  (centroid, roll-off, flatness, ZCR, band balance, loudness).
- analyze_sample_timbre: same fingerprint for a file on disk.
- compare_timbre: sample vs clip — cosine similarity over band shape,
  centroid/flatness deltas, plain-language verdict hints.

Honest scope: analysis is server-side DSP on the decoded sample file, at
the file's rate decimated to the DSP rate — identical to how
audio_intelligence reads audio. Live's API cannot stream the live master
signal, so 'what is playing right now' is out of scope by design.
"""
import json
import logging
import os
from typing import Any, Dict

from mcp.server.fastmcp import Context

from MCP_Server.tools._base import _tool_handler
from MCP_Server.connections.ableton import get_ableton_connection
from MCP_Server.validation import _validate_index
from MCP_Server.spectral import analyze_timbre, compare_timbre as _compare
from MCP_Server.tools.audio_intelligence import _read_audio_mono

logger = logging.getLogger(__name__)


def _fingerprint_file(path: str, source: str) -> Dict[str, Any]:
    if not path or not str(path).strip():
        raise ValueError("audio file path is required")
    path = str(path).strip()
    if not os.path.isfile(path):
        raise ValueError("audio file not found on disk: " + path)
    samples, rate = _read_audio_mono(path)
    if not samples:
        raise ValueError(
            "unsupported or unreadable audio file (wav/aiff supported; "
            "mp3/flac/ogg are not — convert first)")
    return analyze_timbre(samples, rate, source=source)


def register_tools(mcp):
    @mcp.tool()
    @_tool_handler("analyzing clip timbre")
    def analyze_clip_timbre(ctx: Context, track_index: int, clip_index: int) -> str:
        """
        Full timbre fingerprint of an AUDIO clip in the set: spectral
        centroid (brightness), roll-off, flatness (tonal vs noisy), zero
        crossing rate, 6-band balance, peak frequency and loudness.

        Use it to describe how a clip sounds ("dark sub-heavy bass",
        "bright airy hat"), choose fitting samples, or spot timbral
        clashes before they hit the mix. Live's warp metadata adds the
        clip's warp mode for context. WAV/AIFF clips only.
        """
        _validate_index(track_index, "track_index")
        _validate_index(clip_index, "clip_index")
        ableton = get_ableton_connection()

        # validate + gather context (read-only)
        try:
            info = ableton.send_command("get_audio_clip_info", {
                "track_index": track_index, "clip_index": clip_index})
            clip_name = info.get("name") or "audio clip"
        except Exception as e:
            raise ValueError("no audio clip at track %d slot %d (%s)"
                             % (track_index, clip_index, e))

        fp = ableton.send_command("get_clip_file_path", {
            "track_index": track_index, "clip_index": clip_index})
        path = fp.get("file_path")
        if not path:
            raise ValueError("clip has no sample file path (it may be a "
                             "recorded/unsaved clip)")

        result = _fingerprint_file(path, source=clip_name)
        result["clip"] = {"track_index": track_index, "clip_index": clip_index,
                          "warping": info.get("warping"),
                          "warp_mode": info.get("warp_mode"),
                          "length_beats": info.get("length")}
        return json.dumps(result, indent=2)

    @mcp.tool()
    @_tool_handler("analyzing sample timbre")
    def analyze_sample_timbre(ctx: Context, sample_path: str) -> str:
        """
        Timbre fingerprint for any audio file on disk (the same analysis
        as analyze_clip_timbre): spectral centroid, roll-off, flatness,
        zero crossing rate, 6-band balance, peak frequency, loudness.

        Use it on candidate samples before loading them ("is this kick
        sub-heavy or punchy-mid?"), on stems, or on exported renders.
        WAV/AIFF only.
        """
        return json.dumps(_fingerprint_file(sample_path, source=sample_path), indent=2)

    @mcp.tool()
    @_tool_handler("comparing timbre")
    def compare_timbre(ctx: Context, sample_path: str,
                       track_index: int, clip_index: int) -> str:
        """
        Compare a sample file against an audio clip in the set: cosine
        similarity over the 6-band shape (scale-invariant), centroid and
        flatness deltas, the largest band gap, and plain-language verdict
        hints ("clearly different tonal shapes", "sample is brighter").

        The layering/blending question answerer: "will this sample sit
        with that clip?" before either is loaded. WAV/AIFF only.
        """
        _validate_index(track_index, "track_index")
        _validate_index(clip_index, "clip_index")
        sample_fp = _fingerprint_file(sample_path, source=sample_path)

        ableton = get_ableton_connection()
        try:
            info = ableton.send_command("get_audio_clip_info", {
                "track_index": track_index, "clip_index": clip_index})
            clip_name = info.get("name") or "clip"
        except Exception as e:
            raise ValueError("no audio clip at track %d slot %d (%s)"
                             % (track_index, clip_index, e))
        fp = ableton.send_command("get_clip_file_path", {
            "track_index": track_index, "clip_index": clip_index})
        path = fp.get("file_path")
        if not path:
            raise ValueError("clip has no sample file path")
        clip_fp = _fingerprint_file(path, source=clip_name)

        verdict = _compare(sample_fp, clip_fp)
        return json.dumps({
            "sample": {k: sample_fp[k] for k in
                       ("source", "spectral_centroid_hz", "spectral_flatness",
                        "band_balance_db")},
            "clip": {k: clip_fp[k] for k in
                     ("source", "spectral_centroid_hz", "spectral_flatness",
                      "band_balance_db")},
            "comparison": verdict,
        }, indent=2)
