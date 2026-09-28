"""Offline tests for v0.6.x: MCP resources/prompts and mix matching DSP.

No Ableton connection required — prompts/resources are tested with the
connection monkeypatched, DSP helpers run on synthetic data.
"""
import json
import math
import sys
from unittest import mock

import pytest

sys.path.insert(0, ".")

from MCP_Server.tools import resources_prompts as rp
from MCP_Server.tools import mix_matching as mm


# ---------------------------------------------------------------------------
# Prompts (theme 2)
# ---------------------------------------------------------------------------


def test_list_prompts_has_all_four():
    names = {p["name"] for p in rp.list_prompts()}
    assert {"mix-review", "song-doctor", "arrange-my-ideas",
            "match-my-reference"} <= names


def test_prompt_build_shape():
    out = rp.get_prompt("song-doctor", {"complaint": "no energy"})
    assert out["messages"][0]["role"] == "user"
    text = out["messages"][0]["content"]["text"]
    assert "song doctor" in text.lower()
    assert "no energy" in text


def test_prompt_requires_required_argument():
    with pytest.raises(ValueError):
        rp.get_prompt("match-my-reference", {})


def test_prompt_rejects_unknown_argument():
    with pytest.raises(ValueError):
        rp.get_prompt("mix-review", {"bogus": "x"})


def test_prompt_unknown_name():
    with pytest.raises(ValueError):
        rp.get_prompt("nope", {})


def test_prompt_hydrates_snapshot_when_live(monkeypatch):
    monkeypatch.setattr(rp, "_try_hydrate", lambda: '{"tempo": 128}')
    text = rp.get_prompt("mix-review", {})["messages"][0]["content"]["text"]
    assert "128" in text


def test_prompt_offline_note(monkeypatch):
    monkeypatch.setattr(rp, "_try_hydrate", lambda: "")
    text = rp.get_prompt("mix-review", {})["messages"][0]["content"]["text"]
    assert "offline" in text.lower()


# ---------------------------------------------------------------------------
# Resources (theme 2)
# ---------------------------------------------------------------------------


def test_list_resources_every_entry_has_a_uri():
    """MCP's Resource type requires `uri`.

    A `uriTemplate` descriptor used to be returned inside the plain `resources`
    array, producing a schema-invalid resource with no `uri` at all; strict
    clients (which type `uri` as required) saw `undefined`.
    """
    entries = rp.list_resources()
    for entry in entries:
        assert "uri" in entry, f"resource without uri: {entry}"
        assert "uriTemplate" not in entry, f"template in resources array: {entry}"


def test_track_template_is_served_as_a_template():
    """Templates belong to resources/templates/list, not resources/list."""
    uris = [r.get("uri") for r in rp.list_resources()]
    assert "ableton://session/summary" in uris
    assert "ableton://track/0" in uris

    templates = [r.get("uriTemplate") for r in rp.list_resource_templates()]
    assert "ableton://track/{index}" in templates
    for tpl in rp.list_resource_templates():
        assert "name" in tpl
        assert "uriTemplate" in tpl


class _FakeConn:
    def __init__(self, result):
        self._result = result

    def send_command(self, cmd, params=None):
        return {"status": "success", "result": self._result}


def test_read_resource_session_summary(monkeypatch):
    conn = _FakeConn({"tempo": 120.0, "scene_count": 2})
    monkeypatch.setattr(rp, "_get_conn", lambda: conn)
    monkeypatch.setattr(rp, "_call", lambda c, cmd, p=None: c._result)
    out = rp.read_resource("ableton://session/summary")
    data = json.loads(out["contents"][0]["text"])
    assert data["tempo"] == 120.0


def test_read_resource_unknown_uri():
    with pytest.raises(ValueError):
        rp.read_resource("ableton://nope")


def test_read_resource_track_bad_index(monkeypatch):
    with pytest.raises(ValueError):
        rp.read_resource("ableton://track/abc")


def test_read_resource_journal_missing_file(monkeypatch):
    monkeypatch.setattr(rp, "_journal_path",
                        lambda: "C:/definitely/not/here/journal.jsonl")
    out = rp.read_resource("ableton://journal")
    data = json.loads(out["contents"][0]["text"])
    assert data["count"] == 0


# ---------------------------------------------------------------------------
# Mix matching DSP (theme 3)
# ---------------------------------------------------------------------------


def _sine(freq, seconds, rate=4410, amp=0.5):
    n = int(seconds * rate)
    return [amp * math.sin(2 * math.pi * freq * i / rate) for i in range(n)]


def test_band_energies_peak_in_right_band():
    # 100 Hz sine: energy should concentrate in low_60_120, tiny elsewhere
    samples = _sine(100.0, 4.0)
    energies = mm._band_energies(samples, 4410)
    low = energies["low_60_120"]
    others = [v for k, v in energies.items() if k != "low_60_120"]
    assert max(others) < low


def test_relative_db_normalizes_peak_to_zero():
    samples = _sine(100.0, 4.0)
    rel = mm._to_relative_db(mm._band_energies(samples, 4410))
    peak = max(rel.values())
    assert peak == 0.0
    assert all(v <= 0.0 for v in rel.values())


def test_loudness_profile_sine():
    samples = _sine(220.0, 3.0, amp=0.25)
    prof = mm._loudness_profile(samples, 4410)
    assert -16 < prof["rms_dbfs"] < -14  # sine RMS = amp/sqrt(2) ≈ 0.177 → −15 dB
    assert prof["peak_dbfs"] < 0
    assert prof["crest_factor_db"] > 0


def test_analyze_reference_file_missing():
    with pytest.raises(ValueError):
        mm.analyze_reference_file("")
    with pytest.raises(ValueError):
        mm.analyze_reference_file("C:/not/a/real/file.wav")


def test_sample_master_meters_requires_playback(monkeypatch):
    conn = _FakeConn({"playing": False})

    class _C:
        def __init__(self):
            self.sock = object()

    monkeypatch.setattr(
        mm, "get_ableton_connection",
        lambda: mock.MagicMock(sock=_C(), send_command=conn.send_command))
    with pytest.raises(ValueError):
        mm.sample_master_meters(seconds=0.2, interval=0.05)


def test_tools_registered():
    registered = []

    class _Reg:
        def tool(self):
            def deco(fn):
                registered.append(fn.__name__)
                return fn
            return deco

    mm.register_tools(_Reg())
    assert "analyze_reference_mix" in registered
    assert "match_reference_mix" in registered
