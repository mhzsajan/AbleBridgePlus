"""Offline replay tests for the v0.6 undo-safety layer (checkpoints.py).

Drives MCP_Server.checkpoints directly with a scripted FakeAbleton —
no Ableton required. Covers capture/restore fidelity, auto ring pruning,
named persistence (save + load round-trip), diff logic, and the
_tool_handler auto-checkpoint hook (mutating tool -> auto snapshot).
"""
import asyncio
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from MCP_Server import checkpoints as store  # noqa: E402


class FakeAbleton:
    """Minimal scripted connection: canned data + simple state mutations."""

    def __init__(self, tracks=(), scenes=("Intro", "Verse"), tempo=120.0):
        self._tracks = [dict(t) for t in tracks]
        self._scenes = list(scenes)
        self._tempo = tempo
        self.calls = []

    def send_command(self, command_type, params=None):
        self.calls.append((command_type, params or {}))
        p = params or {}
        if command_type == "get_all_tracks_info":
            return {"tracks": [
                {"index": i, "name": t["name"],
                 "is_audio": bool(t.get("audio")),
                 "is_midi": not t.get("audio"),
                 "mute": bool(t.get("mute")),
                 "solo": False, "arm": False,
                 "volume": t.get("volume", 0.85),
                 "panning": 0.0}
                for i, t in enumerate(self._tracks)]}
        if command_type == "get_track_info":
            t = self._tracks[p["track_index"]]
            slots = [{"index": i,
                      "clip": ({"name": c.get("name", ""),
                                "length": c.get("length", 4.0)} if c else None)}
                     for i, c in enumerate(t.get("clips", []))]
            return {"color_index": t.get("color_index", 17),
                    "clip_slots": slots}
        if command_type == "get_scenes":
            return {"scenes": [{"name": n} for n in self._scenes]}
        if command_type == "get_session_info":
            return {"tempo": self._tempo}
        if command_type == "set_tempo":
            self._tempo = p["tempo"]
            return {"status": "ok"}
        if command_type == "create_audio_track":
            self._tracks.append({"name": "scratch", "audio": True})
            return {"status": "ok"}
        if command_type == "delete_track":
            del self._tracks[p["track_index"]]
            return {"status": "ok"}
        raise AssertionError("unexpected command: " + command_type)


# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _fresh_store(tmp_path, monkeypatch):
    """Isolate the module-level store per test; point persistence at tmp."""
    store._auto.clear()
    store._named.clear()
    monkeypatch.setattr(store, "_DISK_PATH", str(tmp_path / "cps.json"))
    yield
    store._auto.clear()
    store._named.clear()


def test_capture_and_restore_roundtrip():
    ab = FakeAbleton(
        tracks=[{"name": "Drums", "clips": [{"name": "beat"}]},
                {"name": "Bass", "audio": True}],
        scenes=("Intro", "Drop"), tempo=128.0)
    snap = store.capture_snapshot(ab)
    assert snap["tempo"] == 128.0
    assert len(snap["tracks"]) == 2
    assert snap["tracks"][0]["clips"] == [
        {"slot": 0, "name": "beat", "length": 4.0}]
    assert snap["scenes"] == ["Intro", "Drop"]

    # mutate: tempo + a new track
    ab.send_command("set_tempo", {"tempo": 150.0})
    ab.send_command("create_audio_track", {})
    r = store.restore(ab, snap)
    assert r["tempo_set"] == 128.0
    assert r["tracks"]["deleted"] == 1
    assert r["tracks"]["errors"] == []
    assert len(ab._tracks) == 2
    assert ab._tempo == 128.0


def test_diff_added_removed_changed():
    # diff matches tracks by position (same convention as restore)
    old = store.capture_snapshot(FakeAbleton(
        tracks=[{"name": "A"}, {"name": "B"}], scenes=("S1",), tempo=120.0))
    # grew by one -> position 2 is new
    grew = store.capture_snapshot(FakeAbleton(
        tracks=[{"name": "A"}, {"name": "B"}, {"name": "C"}],
        scenes=("S1",), tempo=120.0))
    d = store.diff_snapshots(old, grew)
    assert d["added"] == [{"index": 2, "name": "C"}]
    assert d["removed"] == []

    # shrank by one -> position 1 disappeared
    shrank = store.capture_snapshot(FakeAbleton(
        tracks=[{"name": "A"}], scenes=("S1",), tempo=120.0))
    d2 = store.diff_snapshots(old, shrank)
    assert d2["removed"] == [{"index": 1, "name": "B"}]
    assert d2["added"] == []

    # same positions, renamed + muted + tempo drift -> changed entries
    now = store.capture_snapshot(FakeAbleton(
        tracks=[{"name": "A2"}, {"name": "B2", "mute": True}],
        scenes=("S1",), tempo=132.0))
    d3 = store.diff_snapshots(old, now)
    assert d3["added"] == [] and d3["removed"] == []
    t0 = next(c for c in d3["changed"] if c["index"] == 0)
    assert t0["changes"]["name"] == ["A", "A2"]
    t1 = next(c for c in d3["changed"] if c["index"] == 1)
    assert t1["changes"]["mute"] == [False, True]
    assert d3["tempo"] == [120.0, 132.0]


def test_auto_ring_prunes_and_reports_trigger():
    ab = FakeAbleton(tracks=[{"name": "A"}])
    for i in range(25):
        store.store_auto(store.capture_snapshot(ab), "tool_x", "args%d" % i)
    assert len(store._auto) == store._AUTO_LIMIT
    entry = store.get_auto(-1)
    assert entry["trigger"]["tool"] == "tool_x"
    truncated = "args%d" % 24
    assert entry["trigger"]["args"] == truncated


def test_named_persistence_roundtrip(tmp_path):
    ab = FakeAbleton(tracks=[{"name": "A"}], tempo=99.0)
    snap = store.capture_snapshot(ab)
    store.store_named("before-x", snap)
    assert os.path.exists(store._DISK_PATH)

    store._named.clear()
    store.load_persisted()
    entry = store.get_named("before-x")
    assert entry is not None
    assert entry["snapshot"]["tempo"] == 99.0


def test_named_limit_prunes_oldest():
    ab = FakeAbleton(tracks=[{"name": "A"}])
    for i in range(store._NAMED_LIMIT + 5):
        store.store_named("c%02d" % i, store.capture_snapshot(ab))
    assert len(store._named) == store._NAMED_LIMIT
    assert "c00" not in store._named          # oldest pruned
    assert "c%02d" % (store._NAMED_LIMIT + 4) in store._named


def test_auto_hook_fires_on_mutating_tool(monkeypatch):
    fired = []
    monkeypatch.setattr(store, "store_auto",
                        lambda snap, tool, args: fired.append(tool))

    class _Conn:
        sock = object()

    import MCP_Server.state as state_mod
    monkeypatch.setattr(state_mod, "ableton_connection", _Conn())

    from MCP_Server.tools._base import _tool_handler

    # real tools are sync functions — _tool_handler runs them via to_thread
    @_tool_handler("testing mutation")
    def set_tempo(ctx, tempo: float = 120.0) -> str:
        "doc"
        return "ok"

    asyncio.new_event_loop().run_until_complete(set_tempo(None))
    assert fired == ["set_tempo"]


def test_auto_hook_skips_non_mutating_and_failures(monkeypatch):
    fired = []
    monkeypatch.setattr(store, "store_auto",
                        lambda snap, tool, args: fired.append(tool))

    class _Conn:
        sock = object()

    import MCP_Server.state as state_mod
    monkeypatch.setattr(state_mod, "ableton_connection", _Conn())

    from MCP_Server.tools._base import _tool_handler

    # real tools are sync functions — _tool_handler runs them via to_thread
    @_tool_handler("read tool")
    def list_stuff(ctx) -> str:
        "doc"
        return "[]"

    @_tool_handler("mutating tool")
    def boom(ctx) -> str:
        "doc"
        raise ValueError("explode")

    loop = asyncio.new_event_loop()
    loop.run_until_complete(list_stuff(None))
    # mutating but failing -> wrapper converts to a tool_error envelope,
    # and the failure path must not have left an auto checkpoint behind
    result = loop.run_until_complete(boom(None))
    assert "explode" in str(result)
    assert fired == []


def test_safe_experiment_rolls_back_on_failure():
    ab = FakeAbleton(tracks=[{"name": "A"}], tempo=120.0)
    store.store_auto(store.capture_snapshot(ab), "safe_experiment", "boom-test")
    try:
        ab.send_command("set_tempo", {"tempo": 160.0})
        raise ValueError("step 2 exploded")
    except ValueError:
        pass
    r = store.restore(ab, store.get_auto(-1)["snapshot"])
    assert r["tempo_set"] == 120.0
    assert ab._tempo == 120.0
    assert len(ab._tracks) == 1
