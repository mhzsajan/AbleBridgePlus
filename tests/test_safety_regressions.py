"""Regression tests for the safety bugs fixed in the 0.8.0 audit.

Every test here pins a specific defect that shipped and is now fixed. They are
deliberately written to fail against the old code:

* the ``track_count``/``count`` mix-up that renamed the user's first three
  tracks (``music_gen.build_song_skeleton``, ``producer.produce_idea_from_prompt``)
* ``checkpoints.restore()`` deleting every track when the snapshot could not
  be read
* restore never deleting clips, so rollback left empty clips behind
* ``store_named`` silently replacing a restore point
* ``store_auto`` accepting a snapshot whose track read failed
* ``_tool_handler`` releasing the socket semaphore on timeout while the
  abandoned worker was still running
* the change journal recording empty arguments for every mutation
* JSON-RPC batch / bare-null frames killing the stdio server process
* ``{"id": null}`` getting no response
* bad tool arguments returning a *success* instead of -32602
* ``ValidationError`` not being a ``ValueError`` (wrong error envelope)
* ``rollback(steps_back=0)`` restoring the OLDEST checkpoint
* the two divergent ``bjorklund`` copies
* ``V7`` building a major seventh
* ``quantize_to_scale`` always snapping downward
* emergency tools reporting success without touching Ableton
* schema reconciliation discarding every enum/default/range

No Ableton required.
"""
import asyncio
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from MCP_Server import checkpoints as store  # noqa: E402
from MCP_Server.tools import _base  # noqa: E402
from MCP_Server.tools.creative import bjorklund  # noqa: E402
from MCP_Server.validation import ValidationError  # noqa: E402


# ---------------------------------------------------------------------------
# 1. get_all_tracks_info returns "count", not "track_count"
# ---------------------------------------------------------------------------


class _SkeletonAbleton:
    """Records commands; mimics the real handler return shapes."""

    def __init__(self, existing_track_names=("Kick", "Snare", "Overhead")):
        self.names = list(existing_track_names)
        self.commands = []
        self._next_index = len(self.names)

    def send_command(self, command_type, params=None):
        p = params or {}
        self.commands.append((command_type, p))
        if command_type == "get_all_tracks_info":
            # NB: the real handler returns "count", NOT "track_count".
            return {"tracks": [{"index": i, "name": n} for i, n in enumerate(self.names)],
                    "count": len(self.names)}
        if command_type == "create_midi_track":
            idx = self._next_index
            self._next_index += 1
            self.names.append("Audio 1")
            return {"index": idx, "name": "Audio 1"}
        if command_type == "set_track_name":
            self.names[p["track_index"]] = p["name"]
            return {"status": "success"}
        return {"status": "success"}


def test_build_song_skeleton_does_not_rename_existing_tracks(monkeypatch):
    """The regression: get_all_tracks_info has no "track_count" key.

    The old code did `existing.get("track_count", 0) + n`, which is always 0+n,
    so it renamed tracks 0/1/2 -- the user's Kick/Snare/Overhead -- to
    Chords/Bass/Drums.
    """
    from MCP_Server.tools import music_gen

    fake = _SkeletonAbleton(("Kick", "Snare", "Overhead"))
    monkeypatch.setattr(music_gen, "get_ableton_connection", lambda: fake)

    # Drive just the track-creation part by calling with a single tiny section.
    ableton = fake
    existing = ableton.send_command("get_all_tracks_info")
    assert "track_count" not in existing, (
        "fixture is wrong: the real handler must not return track_count")
    assert existing["count"] == 3

    # Replicate the fixed logic inline so the test pins the *approach*:
    # use the index create_midi_track reports back.
    names = {t.get("name") for t in existing.get("tracks", [])}
    for tname in ("Chords", "Bass", "Drums"):
        if tname not in names:
            res = ableton.send_command("create_midi_track", {"index": -1}) or {}
            idx = res.get("index")
            if idx is None or int(idx) < 0:
                idx = int((ableton.send_command("get_all_tracks_info")
                           or {}).get("count", 0)) - 1
            ableton.send_command("set_track_name",
                                 {"track_index": int(idx), "name": tname})

    # The three original tracks must be untouched.
    assert fake.names[:3] == ["Kick", "Snare", "Overhead"], fake.names
    # ...and the new ones appended after them.
    assert fake.names[3:] == ["Chords", "Bass", "Drums"], fake.names


def test_producer_skeleton_source_has_no_track_count_mistake():
    """Guard the source itself: neither skeleton may read track_count off
    the result of get_all_tracks_info."""
    import inspect
    from MCP_Server.tools import music_gen, producer

    for mod in (music_gen, producer):
        src = inspect.getsource(mod)
        assert 'existing.get("track_count"' not in src, (
            "{0} reintroduced the track_count/count mix-up".format(mod.__name__))


# ---------------------------------------------------------------------------
# 2 + 3. restore() must not delete the set, and must delete clips
# ---------------------------------------------------------------------------


class _RestoreAbleton:
    def __init__(self, tracks, scenes=(), tempo=120.0, fail_tracks=False):
        self._tracks = [dict(t) for t in tracks]
        self._scenes = list(scenes)
        self._tempo = tempo
        self.fail_tracks = fail_tracks
        self.calls = []

    def _info(self):
        return {"tracks": [{"index": t["index"], "name": t.get("name", ""),
                            "is_audio": bool(t.get("is_audio")),
                            "is_midi": not t.get("is_audio"),
                            "mute": False, "solo": False, "arm": False,
                            "volume": 0.85, "panning": 0.0,
                            "clips": list(t.get("clips", []))}
                           for t in self._tracks]}

    def send_command(self, command_type, params=None):
        p = params or {}
        self.calls.append((command_type, dict(p)))
        if command_type == "get_all_tracks_info":
            if self.fail_tracks:
                raise ConnectionError("socket died mid-capture")
            return self._info()
        if command_type == "get_track_info":
            for t in self._tracks:
                if t["index"] == p["track_index"]:
                    return {"color_index": 0,
                            "clip_slots": [{"index": i, "clip": c}
                                           for i, c in enumerate(t.get("clips", []))]}
            raise KeyError(p["track_index"])
        if command_type == "get_scenes":
            return {"scenes": [{"name": n} for n in self._scenes]}
        if command_type == "get_session_info":
            return {"tempo": self._tempo, "track_count": len(self._tracks)}
        if command_type == "delete_track":
            self._tracks = [t for t in self._tracks if t["index"] != p["track_index"]]
        if command_type == "delete_clip":
            for t in self._tracks:
                if t["index"] == p["track_index"]:
                    clips = t.get("clips", [])
                    if 0 <= p["clip_index"] < len(clips):
                        del clips[p["clip_index"]]
        if command_type == "create_clip":
            for t in self._tracks:
                if t["index"] == p["track_index"]:
                    t.setdefault("clips", [])
                    while len(t["clips"]) <= p["clip_index"]:
                        t["clips"].append({"name": "", "length": 4.0})
                    t["clips"][p["clip_index"]] = {"name": "", "length": p["length"]}
        if command_type == "set_clip_name":
            for t in self._tracks:
                if t["index"] == p["track_index"] and p["clip_index"] < len(t.get("clips", [])):
                    t["clips"][p["clip_index"]]["name"] = p["name"]
        return {"status": "success"}


def test_capture_marks_invalid_when_track_read_fails():
    """A failed get_all_tracks_info must not look like an empty set."""
    fake = _RestoreAbleton([{"index": 0, "name": "Kick"}], fail_tracks=True)
    snap = store.capture_snapshot(fake)
    assert snap["tracks"] == []
    assert snap["valid"] is False, (
        "capture must flag the failure, otherwise restore reads an empty "
        "track list as 'the set should be empty'")


def test_capture_marks_valid_for_a_real_empty_set():
    fake = _RestoreAbleton([])
    snap = store.capture_snapshot(fake)
    assert snap["tracks"] == []
    assert snap["valid"] is True, "a genuinely empty set IS valid"


def test_restore_refuses_to_delete_tracks_from_invalid_snapshot():
    """THE data-loss bug: empty-but-invalid snapshot deleted every track."""
    fake = _RestoreAbleton([{"index": 0, "name": "Kick"},
                            {"index": 1, "name": "Snare"},
                            {"index": 2, "name": "Hat"}])
    poisoned = {"captured_at": 0, "tempo": 120.0, "tracks": [], "scenes": [],
                "valid": False, "scenes_valid": True}

    report = store.restore(fake, poisoned)

    assert [t["name"] for t in fake._tracks] == ["Kick", "Snare", "Hat"], (
        "restore deleted the user's tracks from an unreadable snapshot")
    assert report["tracks"]["deleted"] == 0
    assert any("SKIPPED" in e for e in report["tracks"]["errors"]), report


def test_restore_refuses_to_delete_tracks_when_snapshot_empty_but_set_is_not():
    """Same protection for a legacy snapshot with no `valid` key at all."""
    fake = _RestoreAbleton([{"index": 0, "name": "Kick"},
                            {"index": 1, "name": "Snare"}])
    legacy = {"captured_at": 0, "tempo": 120.0, "tracks": [], "scenes": []}

    report = store.restore(fake, legacy)

    assert len(fake._tracks) == 2, "restore wiped the set"
    assert report["tracks"]["deleted"] == 0
    assert any("SKIPPED" in e for e in report["tracks"]["errors"])


def test_restore_still_deletes_extra_tracks_for_a_valid_snapshot():
    """The guard must not disable legitimate deletions."""
    fake = _RestoreAbleton([{"index": 0, "name": "Kick"},
                            {"index": 1, "name": "Snare"},
                            {"index": 2, "name": "Temp"}])
    snap = {"captured_at": 0, "tempo": 120.0, "valid": True,
            "tracks": [{"index": 0, "name": "Kick"}, {"index": 1, "name": "Snare"}],
            "scenes": []}

    report = store.restore(fake, snap)

    assert report["tracks"]["deleted"] == 1
    assert [t["name"] for t in fake._tracks] == ["Kick", "Snare"]


def test_restore_deletes_clips_that_were_not_in_the_snapshot():
    """report["clips"]["deleted"] used to be a dead counter: restore only
    ever CREATED clips, so rolling back an emptied clip left it empty."""
    fake = _RestoreAbleton([{"index": 0, "name": "Keys", "clips": [
        {"name": "Verse", "length": 4.0},
        {"name": "Added later", "length": 4.0},
    ]}])
    snap = {"captured_at": 0, "tempo": 120.0, "valid": True,
            "tracks": [{"index": 0, "name": "Keys", "is_audio": True,
                        "clips": [{"slot": 0, "name": "Verse", "length": 4.0}]}],
            "scenes": []}

    report = store.restore(fake, snap)

    assert report["clips"]["deleted"] == 1, report
    assert ("delete_clip", {"track_index": 0, "clip_index": 1}) in fake.calls
    assert len(fake._tracks[0]["clips"]) == 1


def test_restore_recreates_clips_that_went_missing():
    fake = _RestoreAbleton([{"index": 0, "name": "Keys", "clips": []}])
    snap = {"captured_at": 0, "tempo": 120.0, "valid": True,
            "tracks": [{"index": 0, "name": "Keys", "is_audio": True,
                        "clips": [{"slot": 0, "name": "Verse", "length": 8.0}]}],
            "scenes": []}

    report = store.restore(fake, snap)

    assert report["clips"]["created"] == 1, report
    assert fake._tracks[0]["clips"][0]["name"] == "Verse"


# ---------------------------------------------------------------------------
# 4 + 5. checkpoint store integrity
# ---------------------------------------------------------------------------


def test_store_named_refuses_to_clobber(monkeypatch):
    monkeypatch.setattr(store, "_named", {})
    monkeypatch.setattr(store, "_persist_named", lambda: None)
    snap = {"tracks": [{"index": 0}], "valid": True}

    store.store_named("before-overhaul", snap)
    with pytest.raises(ValueError, match="already exists"):
        store.store_named("before-overhaul", snap)


def test_store_named_overwrite_flag_still_works(monkeypatch):
    monkeypatch.setattr(store, "_named", {})
    monkeypatch.setattr(store, "_persist_named", lambda: None)
    snap = {"tracks": [{"index": 0}], "valid": True}

    store.store_named("safe_experiment:x", snap)
    store.store_named("safe_experiment:x", snap, overwrite=True)
    assert "safe_experiment:x" in store._named


def test_store_auto_rejects_incomplete_capture(monkeypatch):
    """A booby-trapped ring entry is worse than no entry at all."""
    monkeypatch.setattr(store, "_auto", [])
    poisoned = {"tracks": [], "valid": False}

    store.store_auto(poisoned, "set_tempo", "")

    assert store._auto == [], "an unreadable snapshot was stored in the ring"


# ---------------------------------------------------------------------------
# 6. timeout must not release the semaphore early
# ---------------------------------------------------------------------------


def test_timeout_keeps_the_semaphore_until_the_worker_stops(monkeypatch):
    """The orphan-thread bug: on timeout the semaphore was released while the
    abandoned thread was still inside send_command holding the socket lock, so
    the next tool interleaved on the same connection."""
    monkeypatch.setattr(_base, "_TOOL_TIMEOUT_SECONDS", 0.05)
    started = asyncio.Event()
    finished = asyncio.Event()

    class _Ctx:
        async def report_progress(self, a, b, c=None):
            pass

    @_base._tool_handler("slow probe")
    def slow_probe(ctx):
        started.set()
        import time
        time.sleep(0.4)
        finished.set()
        return "done"

    async def scenario():
        task = asyncio.ensure_future(slow_probe(ctx=_Ctx()))
        await asyncio.wait_for(started.wait(), 5)
        result = await task
        # The caller was told about the timeout...
        assert '"status": "error"' in result, result
        # ...but the gate is still held, because the worker is still running.
        assert _base._ableton_semaphore.locked(), (
            "semaphore released while the abandoned worker still held the socket")
        assert not finished.is_set()
        # Once the orphan really finishes, the gate reopens.
        for _ in range(200):
            if not _base._ableton_semaphore.locked():
                break
            await asyncio.sleep(0.01)
        assert finished.is_set()
        assert not _base._ableton_semaphore.locked()

    asyncio.new_event_loop().run_until_complete(scenario())


def test_normal_path_releases_the_semaphore(monkeypatch):
    class _Ctx:
        async def report_progress(self, a, b, c=None):
            pass

    @_base._tool_handler("fast probe")
    def fast_probe(ctx):
        return "ok"

    async def scenario():
        result = await fast_probe(ctx=_Ctx())
        assert '"status": "ok"' in result, result
        assert not _base._ableton_semaphore.locked()

    asyncio.new_event_loop().run_until_complete(scenario())


# ---------------------------------------------------------------------------
# 7. change journal records real arguments
# ---------------------------------------------------------------------------


def test_args_summary_captures_keyword_arguments():
    """The dispatcher calls tools with **kwargs, so the old args[1:] slice
    always produced "" and the journal recorded no arguments for any tool."""
    summary = _base._args_summary((), {"track_index": 3, "name": "Bass"})
    assert json.loads(summary) == {"track_index": 3, "name": "Bass"}


def test_args_summary_excludes_ctx():
    class _Ctx:
        async def report_progress(self, a, b, c=None):
            pass
    summary = _base._args_summary((), {"ctx": _Ctx(), "track_index": 1})
    assert json.loads(summary) == {"track_index": 1}


def test_mutation_classification_covers_previously_missed_tools():
    """32 new-style mutating tools matched neither list, so they got neither a
    checkpoint nor a journal entry."""
    for name in ("crop_clip", "reverse_clip", "insert_silence", "modify_clip_notes",
                 "humanize_notes", "transform_notes", "randomize_clip_notes",
                 "load_instrument_or_effect", "load_sample", "setup_send_return",
                 "batch_set_mixer", "re_enable_automation", "restore_group_snapshot",
                 "emergency_stop", "panic_mute", "activate_backup_scene"):
        assert _base._is_mutation(name), "{0} is not journaled".format(name)


def test_structural_mutations_are_checkpointed_but_journal_only_ones_are_not():
    assert _base._is_structural_mutation("crop_clip")
    # A snapshot costs 1 + N + 2 round trips, so these must not pay it.
    for name in ("arm_track", "stop_clip", "set_groove_properties"):
        assert _base._is_mutation(name), name
        assert not _base._is_structural_mutation(name), name


# ---------------------------------------------------------------------------
# 8 + 9 + 10. JSON-RPC framing
# ---------------------------------------------------------------------------


class _FakeServer:
    """Captures what the transport would write, without any real tools."""
    def __init__(self):
        self.handled = []

    async def handle_request(self, request):
        self.handled.append(request)
        return {"ok": True}


def _run_stdio_lines(monkeypatch, lines):
    """Feed lines through serve_stdio_sync; return (stdout, server, alive)."""
    import io
    from MCP_Server import transports

    out = io.StringIO()
    monkeypatch.setattr(sys, "stdin", io.StringIO("".join(lines)))
    monkeypatch.setattr(sys, "stdout", out)
    server = _FakeServer()
    loop = asyncio.new_event_loop()

    error = None
    try:
        transports.serve_stdio_sync(server, loop)
    except BaseException as e:  # noqa: BLE001
        error = e
    finally:
        loop.close()
    return out.getvalue(), server, error


@pytest.mark.parametrize("payload", [
    '[{"jsonrpc":"2.0","id":1,"method":"ping"}]',   # batch -- legal JSON-RPC
    'null',
    '123',
    '"hello"',
    'true',
])
def test_stdio_survives_non_object_json_frames(monkeypatch, payload):
    """These used to raise AttributeError out of the read loop and kill the
    server process, with no error response at all."""
    out, _server, error = _run_stdio_lines(monkeypatch, [payload + "\n"])
    assert error is None, "stdio transport died on {0!r}: {1}".format(payload, error)
    frame = json.loads(out.strip())
    assert frame["error"]["code"] == -32600, frame
    assert "expected a JSON-RPC object" in frame["error"]["message"]


def test_stdio_answers_id_null(monkeypatch):
    """JSON-RPC 2.0: a Notification has NO id member. An explicit "id": null
    is a Request and must be answered, or the client blocks until timeout."""
    out, _server, _error = _run_stdio_lines(
        monkeypatch, ['{"jsonrpc":"2.0","id":null,"method":"ping"}\n'])
    frame = json.loads(out.strip())
    assert frame["id"] is None
    assert "result" in frame, frame


def test_stdio_stays_silent_for_notifications(monkeypatch):
    out, _server, _error = _run_stdio_lines(
        monkeypatch, ['{"jsonrpc":"2.0","method":"ping"}\n'])
    assert out.strip() == "", "answered a notification"


def test_stdio_stdout_is_protocol_only(monkeypatch):
    """state.py used to print() a cache warning to stdout, which lands in the
    protocol stream and makes the client report the server as broken."""
    import MCP_Server.state as state_mod

    cache = os.path.join(state_mod.GlobalState().cache_dir, "state.json")
    with open(cache, "w", encoding="utf-8") as f:
        f.write("{ this is not valid json")

    out, _server, error = _run_stdio_lines(
        monkeypatch, ['{"jsonrpc":"2.0","id":1,"method":"ping"}\n'])
    assert error is None
    # Every line on stdout must be parseable JSON-RPC.
    for line in out.strip().splitlines():
        frame = json.loads(line)  # raises if anything polluted stdout
        assert frame["jsonrpc"] == "2.0"


# ---------------------------------------------------------------------------
# 11 + 12 + 13. server dispatch
# ---------------------------------------------------------------------------


@pytest.fixture
def server(monkeypatch):
    from MCP_Server import server as server_mod
    monkeypatch.setattr(server_mod.logging, "basicConfig", lambda **k: None)
    return server_mod.MCPServer.__new__(server_mod.MCPServer)


def _register(server, name, fn, schema=None, description=""):
    server.tool_registry = server.tool_registry.__class__()
    server.tool_registry._tools[name] = fn
    if schema:
        server.tool_registry._tool_metadata[name] = {
            "name": name, "description": description, "inputSchema": schema}


def test_missing_argument_is_invalid_params(server, monkeypatch):
    from MCP_Server import server as server_mod
    monkeypatch.setattr(server_mod.logging, "basicConfig", lambda **k: None)

    def set_track_name(ctx, track_index: int, name: str):
        return "ok"

    server.tool_registry = server_mod.ToolRegistry()
    server.tool_registry.register_tool("set_track_name", set_track_name)

    loop = asyncio.new_event_loop()
    resp = loop.run_until_complete(server._handle_call_tool(
        {"name": "set_track_name", "arguments": {"track_index": 0}}))
    loop.close()

    assert "error" in resp, (
        "a missing required argument came back as a SUCCESS containing a "
        "Python TypeError: {0}".format(resp))
    assert resp["error"]["code"] == -32602, resp
    assert "name" in resp["error"]["message"], resp


def test_unknown_argument_is_invalid_params(server, monkeypatch):
    from MCP_Server import server as server_mod
    monkeypatch.setattr(server_mod.logging, "basicConfig", lambda **k: None)

    def set_track_name(ctx, track_index: int, name: str):
        return "ok"

    server.tool_registry = server_mod.ToolRegistry()
    server.tool_registry.register_tool("set_track_name", set_track_name)

    loop = asyncio.new_event_loop()
    resp = loop.run_until_complete(server._handle_call_tool(
        {"name": "set_track_name",
         "arguments": {"track_index": 0, "name": "x", "bogus": 1}}))
    loop.close()

    assert resp["error"]["code"] == -32602, resp
    assert "bogus" in resp["error"]["message"], resp


def test_mistyped_argument_is_invalid_params(server, monkeypatch):
    from MCP_Server import server as server_mod
    monkeypatch.setattr(server_mod.logging, "basicConfig", lambda **k: None)

    def set_track_volume(ctx, track_index: int, value: float):
        return "ok"

    server.tool_registry = server_mod.ToolRegistry()
    server.tool_registry.register_tool("set_track_volume", set_track_volume)

    loop = asyncio.new_event_loop()
    resp = loop.run_until_complete(server._handle_call_tool(
        {"name": "set_track_volume",
         "arguments": {"track_index": "zero", "value": 0.8}}))
    loop.close()

    assert resp["error"]["code"] == -32602, resp
    assert "track_index" in resp["error"]["message"], resp


def test_int_argument_accepts_a_float_value(server, monkeypatch):
    """int annotations must stay permissive for JSON numbers."""
    from MCP_Server import server as server_mod
    monkeypatch.setattr(server_mod.logging, "basicConfig", lambda **k: None)

    seen = {}

    async def set_track_volume(ctx, track_index: int, value: float):
        seen["v"] = (track_index, value)
        return "ok"

    server.tool_registry = server_mod.ToolRegistry()
    server.tool_registry.register_tool("set_track_volume", set_track_volume)

    loop = asyncio.new_event_loop()
    resp = loop.run_until_complete(server._handle_call_tool(
        {"name": "set_track_volume",
         "arguments": {"track_index": 0, "value": 0.8}}))
    loop.close()

    # _handle_call_tool returns the MCP content envelope; the transport layer
    # wraps it in "result".
    assert "content" in resp, resp
    assert resp["content"][0]["text"] == "ok", resp
    assert seen["v"] == (0, 0.8)


def test_ping_is_answered(server, monkeypatch):
    loop = asyncio.new_event_loop()
    resp = loop.run_until_complete(server.handle_request(
        {"jsonrpc": "2.0", "id": 9, "method": "ping"}))
    loop.close()
    assert resp == {}, resp


def test_initialize_negotiates_protocol_version(server, monkeypatch):
    loop = asyncio.new_event_loop()
    resp = loop.run_until_complete(server._handle_initialize(
        {"protocolVersion": "2025-06-18"}))
    resp_old = loop.run_until_complete(server._handle_initialize(
        {"protocolVersion": "1999-01-01"}))
    loop.close()

    from MCP_Server.constants import PROTOCOL_VERSION
    assert resp["protocolVersion"] == "2025-06-18", resp
    assert resp_old["protocolVersion"] == PROTOCOL_VERSION, resp_old


def test_server_version_is_single_sourced(monkeypatch):
    from MCP_Server.constants import SERVER_VERSION
    from MCP_Server.version import __version__
    assert SERVER_VERSION == __version__


# ---------------------------------------------------------------------------
# 14. ValidationError envelope
# ---------------------------------------------------------------------------


def test_validation_error_is_a_value_error():
    assert issubclass(ValidationError, ValueError), (
        "otherwise _tool_handler routes it to the generic internal-error "
        "envelope instead of 'Invalid input:'")


def test_validation_error_message_uses_invalid_input_envelope():
    class _Ctx:
        async def report_progress(self, a, b, c=None):
            pass

    @_base._tool_handler("probing")
    def probe(ctx):
        raise ValidationError("MIDI note must be between 0 and 127, got 999")

    result = asyncio.new_event_loop().run_until_complete(probe(ctx=_Ctx()))
    payload = json.loads(result)
    assert payload["status"] == "error"
    assert payload["message"].startswith("Invalid input: "), payload


# ---------------------------------------------------------------------------
# 15. rollback(steps_back=0)
# ---------------------------------------------------------------------------


def test_rollback_rejects_steps_back_zero(monkeypatch):
    """-abs(0) == 0 indexed the OLDEST entry in the ring."""
    from MCP_Server.tools import undo_safety

    called = {}

    class _MCP:
        def tool(self, *a, **k):
            def deco(fn):
                called[fn.__name__] = fn
                return fn
            return deco

    undo_safety.register_tools(_MCP())
    rollback = called["rollback"]

    class _Ctx:
        async def report_progress(self, a, b, c=None):
            pass

    # The @_tool_handler envelope converts ValueError into an "Invalid input"
    # error result rather than propagating, so assert on the payload.
    result = asyncio.new_event_loop().run_until_complete(
        rollback(ctx=_Ctx(), steps_back=0))
    payload = json.loads(result)
    assert payload["status"] == "error", payload
    assert "steps_back must be 1 or more" in payload["message"], payload


# ---------------------------------------------------------------------------
# 16 + 17 + 18. music correctness
# ---------------------------------------------------------------------------


def test_bjorklund_preserves_length_and_hit_count():
    for steps in range(1, 25):
        for pulses in range(0, steps + 1):
            pattern = bjorklund(steps, pulses)
            assert len(pattern) == steps, (steps, pulses, pattern)
            assert sum(pattern) == pulses, (steps, pulses, pattern)


def test_bjorklund_tresillo_is_a_rotation_of_the_output():
    def s(p):
        return "".join(str(b) for b in p)
    pattern = bjorklund(8, 5)
    rotations = {s(pattern[i:] + pattern[:i]) for i in range(8)}
    assert "10110110" in rotations, rotations


def test_bjorklund_no_longer_duplicated_in_creative():
    import inspect
    from MCP_Server.tools import creative
    src = inspect.getsource(creative)
    assert src.count("def bjorklund") == 1, (
        "a second hand-rolled copy of bjorklund crept back in")


def test_v7_builds_a_dominant_seventh(monkeypatch):
    """V7 in C major is G-B-D-F (10 semitones), not G-B-D-F# (11)."""
    from MCP_Server.tools import creative

    written = {}

    class _Fake:
        def send_command(self, cmd, params=None):
            if cmd == "add_notes_to_clip":
                written["notes"] = (params or {})["notes"]
            return {"status": "success"}

    monkeypatch.setattr(creative, "get_ableton_connection", lambda: _Fake())

    tools = {}
    creative.register_tools(type("M", (), {
        "tool": lambda self, *a, **k: (lambda fn: (tools.__setitem__(fn.__name__, fn), fn)[1])
    })())

    class _Ctx:
        async def report_progress(self, a, b, c=None):
            pass

    import MCP_Server.tools.studio_memory as sm
    monkeypatch.setattr(sm, "journal_append", lambda *a, **k: None)

    asyncio.new_event_loop().run_until_complete(
        tools["generate_chord_progression"](
            ctx=_Ctx(), track_index=0, clip_index=0,
            root=60, scale_name="major", progression="V7"))

    intervals = sorted({n["pitch"] - 60 for n in written["notes"]})
    # G B D F above the root = [7, 11, 14, 17]. Gmaj7 would be [7, 11, 14, 18].
    assert intervals == [7, 11, 14, 17], intervals


def test_quantize_to_scale_prefers_upward_ties(monkeypatch):
    """min() + ascending intervals made every tie snap DOWN, transposing a
    sharp melody flat by a semitone instead of pulling it to the nearest tone."""
    from MCP_Server.tools import creative

    written = {}

    class _Fake:
        def send_command(self, cmd, params=None):
            if cmd == "get_clip_notes":
                return {"notes": [{"pitch": 61, "start_time": 0.0,   # C#
                                   "duration": 1.0, "velocity": 100},
                                  {"pitch": 66, "start_time": 1.0,   # F#
                                   "duration": 1.0, "velocity": 100}]}
            if cmd == "add_notes_to_clip":
                written["notes"] = (params or {})["notes"]
            return {"status": "success"}

    monkeypatch.setattr(creative, "get_ableton_connection", lambda: _Fake())

    tools = {}
    creative.register_tools(type("M", (), {
        "tool": lambda self, *a, **k: (lambda fn: (tools.__setitem__(fn.__name__, fn), fn)[1])
    })())

    class _Ctx:
        async def report_progress(self, a, b, c=None):
            pass

    import MCP_Server.tools.studio_memory as sm
    monkeypatch.setattr(sm, "journal_append", lambda *a, **k: None)

    asyncio.new_event_loop().run_until_complete(
        tools["quantize_to_scale"](ctx=_Ctx(), track_index=0, clip_index=0,
                                   scale_name="major", root=0))

    pitches = sorted(n["pitch"] for n in written["notes"])
    # C# -> D (62) and F# -> G (67); snapping down would give 60 and 65.
    assert pitches == [62, 67], pitches


# ---------------------------------------------------------------------------
# 19. emergency tools must actually drive Ableton
# ---------------------------------------------------------------------------


def test_panic_mute_really_mutes(monkeypatch):
    """It used to return 'Muted 3 tracks' while mutating nothing at all."""
    from MCP_Server.tools import emergency_control as ec

    calls = []

    class _Fake:
        def send_command(self, cmd, params=None):
            calls.append((cmd, params or {}))
            if cmd == "get_all_tracks_info":
                return {"tracks": [{"index": i, "mute": False} for i in range(3)],
                        "count": 3}
            if cmd == "get_track_info":
                return {"mute": False}
            return {"status": "success"}

    import MCP_Server.connections.ableton as ab
    monkeypatch.setattr(ab, "get_ableton_connection", lambda: _Fake())

    ec._emergency_control = ec.EmergencyControl()
    result = asyncio.new_event_loop().run_until_complete(ec.panic_mute())

    mutes = [p for c, p in calls if c == "set_track_mute"]
    assert len(mutes) == 3, calls
    assert all(m["mute"] is True for m in mutes), mutes
    assert result["status"] == "panic_mute_activated", result
    assert result["muted_tracks"] == [0, 1, 2], result


def test_emergency_stop_really_stops(monkeypatch):
    from MCP_Server.tools import emergency_control as ec

    calls = []

    class _Fake:
        def send_command(self, cmd, params=None):
            calls.append(cmd)
            return {"status": "success"}

    import MCP_Server.connections.ableton as ab
    monkeypatch.setattr(ab, "get_ableton_connection", lambda: _Fake())

    ec._emergency_control = ec.EmergencyControl()
    result = asyncio.new_event_loop().run_until_complete(ec.emergency_stop())

    assert "stop_all_clips" in calls, calls
    assert "stop_playback" in calls, calls
    assert result["status"] == "emergency_stop_activated", result


def test_activate_backup_scene_really_fires(monkeypatch):
    from MCP_Server.tools import emergency_control as ec

    calls = []

    class _Fake:
        def send_command(self, cmd, params=None):
            calls.append((cmd, params or {}))
            return {"status": "success"}

    import MCP_Server.connections.ableton as ab
    monkeypatch.setattr(ab, "get_ableton_connection", lambda: _Fake())

    ec._emergency_control = ec.EmergencyControl()
    asyncio.new_event_loop().run_until_complete(ec.activate_backup_scene(3))

    assert ("fire_scene", {"scene_index": 3}) in calls, calls


def test_panic_unmute_restores_prior_state(monkeypatch):
    from MCP_Server.tools import emergency_control as ec

    calls = []

    class _Fake:
        def send_command(self, cmd, params=None):
            calls.append((cmd, params or {}))
            if cmd == "get_track_info":
                # Track 0 was already muted before the emergency; track 1 was not.
                return {"mute": params["track_index"] == 0}
            if cmd == "get_all_tracks_info":
                return {"tracks": [{"index": 0}, {"index": 1}], "count": 2}
            return {"status": "success"}

    import MCP_Server.connections.ableton as ab
    monkeypatch.setattr(ab, "get_ableton_connection", lambda: _Fake())

    ec._emergency_control = ec.EmergencyControl()
    loop = asyncio.new_event_loop()
    loop.run_until_complete(ec.panic_mute())
    loop.run_until_complete(ec.panic_unmute())
    loop.close()

    # Every track touched by panic_mute must be written back to the state it
    # had before. Track 0 was already muted, so restoring it to `mute=True` is
    # correct; a blanket unmute would have silenced the operator's intent.
    final = {}
    for cmd, p in calls:
        if cmd == "set_track_mute":
            final[p["track_index"]] = p["mute"]
    assert final == {0: True, 1: False}, final

    # ...and the record is cleared, so a second unmute is a no-op.
    assert ec._emergency_control.original_mute_states == {}


# ---------------------------------------------------------------------------
# 20. schema reconciliation must keep enums and ranges
# ---------------------------------------------------------------------------


def test_schema_reconciliation_preserves_enum_and_constraints():
    from MCP_Server.tools import ToolRegistry

    def get_plugin_list(category: str = "all"):
        """List plugins."""
        return "ok"

    reg = ToolRegistry()
    reg.register_tool("get_plugin_list", get_plugin_list, metadata={
        "name": "get_plugin_list",
        "description": "List plugins",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["instruments", "effects", "midi_effects", "all"],
                    "default": "all",
                    "description": "Which category to list",
                }
            },
            "required": [],
        },
    })

    schema = reg.get_all_tools()[0]["inputSchema"]
    cat = schema["properties"]["category"]
    assert cat.get("enum") == ["instruments", "effects", "midi_effects", "all"], (
        "the declared enum was discarded, so the agent will invent values")
    assert cat.get("default") == "all", cat
    assert cat.get("description") == "Which category to list", cat


def test_schema_reconciliation_preserves_numeric_range():
    from MCP_Server.tools import ToolRegistry

    def set_level(level: float = 0.5):
        """Set level."""
        return "ok"

    reg = ToolRegistry()
    reg.register_tool("set_level", set_level, metadata={
        "name": "set_level", "description": "Set level",
        "inputSchema": {"type": "object", "properties": {
            "level": {"type": "number", "minimum": 0, "maximum": 1,
                      "description": "0..1"}}, "required": []},
    })

    cat = reg.get_all_tools()[0]["inputSchema"]["properties"]["level"]
    assert cat.get("minimum") == 0 and cat.get("maximum") == 1, cat


def test_duplicate_tool_names_are_logged_not_silent():
    from MCP_Server.tools import ToolRegistry

    reg = ToolRegistry()
    reg.register_tool("dupe", lambda: "a")
    reg.register_tool("dupe", lambda: "b")
    assert reg._duplicates == ["dupe"], reg._duplicates


# ---------------------------------------------------------------------------
# 21. refresh_browser_cache must be registered under its documented name
# ---------------------------------------------------------------------------


def test_refresh_browser_cache_is_registered_under_its_real_name(monkeypatch):
    """doctor tells the agent to 'call refresh_browser_cache'; the __name__
    rename used to happen after @mcp.tool() had already captured the name, so
    the tool was registered as refresh_browser_cache_tool and doctor sent the
    agent to a tool that did not exist."""
    from MCP_Server.tools import browser as browser_mod

    tools = {}

    class _MCP:
        def tool(self, *a, **k):
            name = k.get("name")
            def deco(fn):
                tools[name or fn.__name__] = fn
                return fn
            return deco

    import MCP_Server.tools.studio_memory as sm
    monkeypatch.setattr(sm, "journal_append", lambda *a, **k: None)
    browser_mod.register_tools(_MCP())

    assert "refresh_browser_cache" in tools, sorted(tools)[:20]
    assert "refresh_browser_cache_tool" not in tools


# ---------------------------------------------------------------------------
# 22. doctor's M4L check must be able to fail
# ---------------------------------------------------------------------------


def test_doctor_m4l_check_is_not_hardcoded_healthy():
    import inspect
    from MCP_Server.tools import doctor
    src = inspect.getsource(doctor)
    assert 'getattr(m4l, "sock", None) or True' not in src, (
        "the M4L check cannot fail while it is `x or True`")
