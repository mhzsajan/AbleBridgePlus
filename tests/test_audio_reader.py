"""Regression tests for the sample-file reader (audio_intelligence).

Sparked by the Core Library layering study: 86 real samples were
unreadable because modern packs ship WAVE_FORMAT_EXTENSIBLE (0xFFFE)
wav files that stdlib `wave` refuses. These tests synthesize the exact
formats that failed and lock the fix in.
"""
import math
import struct
import sys
import wave

import pytest

sys.path.insert(0, ".")

from MCP_Server.tools.audio_intelligence import _read_audio_mono


def _write_riff(path, fmt_body, frames, riff_size=None):
    with open(path, "wb") as f:
        data_size = len(frames)
        riff = riff_size if riff_size is not None else 36 + data_size
        f.write(b"RIFF")
        f.write(struct.pack("<I", riff))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write(struct.pack("<I", len(fmt_body)))
        f.write(fmt_body)
        f.write(b"data")
        f.write(struct.pack("<I", data_size))
        f.write(frames)


def _guid_bytes(data1):
    # KSDATAFORMAT_SUBTYPE GUID: 4-byte data1 LE, 2-byte data2, 2-byte data3,
    # 8-byte data4. PCM=0x00000001, IEEE float=0x00000003.
    return (struct.pack("<IHH", data1, 0, 0x0010)
            + bytes([0x80, 0, 0, 0xAA, 0, 0x38, 0x9B, 0x71]))


def _pcm_guid_bytes():
    return _guid_bytes(1)


def _float_guid_bytes():
    return _guid_bytes(3)


def _sine_values(seconds, rate, freq=440.0, amp=0.5):
    n = int(seconds * rate)
    return [amp * math.sin(2 * math.pi * freq * i / rate) for i in range(n)]


def test_extensible_24bit_stereo(tmp_path):
    """A WAVE_FORMAT_EXTENSIBLE 24-bit stereo file must decode (was: None)."""
    rate, seconds = 8000, 1.0
    vals = _sine_values(seconds, rate)
    frames = bytearray()
    for v in vals:
        x = int(v * 8388607.0)
        b = struct.pack("<i", x)[:3]  # little-endian LOW 3 bytes
        frames += b + b               # stereo duplicate
    cb = struct.pack("<HHI", 22, 24, 3)          # cbSize, valid bits, mask
    fmt = (struct.pack("<HHIIHH", 0xFFFE, 2, rate, rate * 6, 6, 24)
           + cb + _pcm_guid_bytes())
    assert len(fmt) == 40
    p = tmp_path / "ext24.wav"
    _write_riff(str(p), fmt, bytes(frames))
    samples, out_rate = _read_audio_mono(str(p))
    assert samples and out_rate == rate
    rms = math.sqrt(sum(x * x for x in samples) / len(samples))
    assert 0.2 < rms < 0.6  # a 0.5 sine decimated should stay in that band


def test_extensible_16bit_stereo(tmp_path):
    rate = 8000
    vals = _sine_values(1.0, rate)
    frames = b"".join(struct.pack("<hh", int(v * 32767), int(v * 32767))
                      for v in vals)
    cb = struct.pack("<HHI", 22, 16, 3)
    fmt = (struct.pack("<HHIIHH", 0xFFFE, 2, rate, rate * 4, 4, 16)
           + cb + _pcm_guid_bytes())
    p = tmp_path / "ext16.wav"
    _write_riff(str(p), fmt, frames)
    samples, out_rate = _read_audio_mono(str(p))
    assert samples and out_rate == rate


def test_ieee_float32_mono(tmp_path):
    rate = 8000
    vals = _sine_values(1.0, rate)
    frames = b"".join(struct.pack("<f", v) for v in vals)
    fmt = struct.pack("<HHIIHH", 3, 1, rate, rate * 4, 4, 32)
    p = tmp_path / "float32.wav"
    _write_riff(str(p), fmt, frames)
    samples, out_rate = _read_audio_mono(str(p))
    assert samples and out_rate == rate
    rms = math.sqrt(sum(x * x for x in samples) / len(samples))
    assert 0.2 < rms < 0.6


def test_plain_pcm_still_works(tmp_path):
    """Standard 16-bit PCM via stdlib wave must be unaffected."""
    rate = 8000
    vals = _sine_values(1.0, rate)
    p = tmp_path / "plain.wav"
    with wave.open(str(p), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<h", int(v * 32767))
                               for v in vals))
    samples, out_rate = _read_audio_mono(str(p))
    assert samples and out_rate == rate


def test_non_pcm_extensible_is_rejected(tmp_path):
    """Extensible container with a non-PCM subformat must still return None."""
    rate = 8000
    # subformat data1 = 2 (MS ADPCM) — neither PCM(1) nor float(3)
    guid = struct.pack("<IHH", 2, 0, 0) + bytes(8)
    fmt = (struct.pack("<HHIIHH", 0xFFFE, 2, rate, rate * 4, 4, 16)
           + struct.pack("<HHI", 22, 16, 3) + guid)
    assert len(fmt) == 40
    p = tmp_path / "weird.wav"
    _write_riff(str(p), fmt, b"\x00" * 512)
    samples, _ = _read_audio_mono(str(p))
    assert samples is None
