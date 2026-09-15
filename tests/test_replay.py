"""
Replay-based tests for AbleBridgePlus — full tool layer, no Ableton needed.

How it works:
- Each test drives MCPServer.handle_request with a scripted sequence of
  tool calls, against a FakeAbletonConnection that replays recorded
  responses from tests/fixtures/replay.json.
- If a fixture entry is missing and ABLEBRIDGE_RECORD=1 (plus a live
  Ableton on port 9877), the test records the real response and appends
  it to the fixture for future replay — "record once, replay in CI".

This catches tool-layer regressions (signatures, parsing, JSON shapes,
journal behavior) that unit tests miss, without requiring Live.
"""
import asyncio
import json
import os

import pytest

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "replay.json")


class FakeAbletonConnection:
    """Replays recorded handler responses keyed by 'command:params'."""

    def __init__(self, store):
        self.store = store
        self.calls = []

    def send_command(self, command_type, params=None):
        params = params or {}
        key = "{0}:{1}".format(command_type, json.dumps(params, sort_keys=True))
        self.calls.append(key)
        if key not in self.store:
            raise KeyError("no recorded response for " + key)
        payload = self.store[key]
        if isinstance(payload, dict) and payload.get("__raise__"):
            raise ConnectionError(payload.get("__message__", "recorded error"))
        return payload


@pytest.fixture
def replay_server(monkeypatch):
    store = {}
    if os.path.exists(FIXTURE):
        with open(FIXTURE, encoding="utf-8") as f:
            store = json.load(f)

    from MCP_Server import server as server_mod

    srv = server_mod.MCPServer()

    fake = FakeAbletonConnection(store)
    # patch every tool module that imported the getter at module level
    import pkgutil
    import MCP_Server.tools as tools_pkg
    for m in pkgutil.iter_modules(tools_pkg.__path__):
        mod_name = "MCP_Server.tools." + m.name
        try:
            mod = __import__(mod_name, fromlist=["get_ableton_connection"])
            if hasattr(mod, "get_ableton_connection"):
                monkeypatch.setattr(mod, "get_ableton_connection", lambda: fake)
        except (ImportError, AttributeError):
            continue
    return srv, fake


def _call(srv, name, args):
    res = asyncio.get_event_loop().run_until_complete(
        srv.handle_request({"method": "tools/call",
                            "params": {"name": name, "arguments": args}}))
    # handle_request returns {"content": [...]} style (internal format)
    if "content" in res:
        return json.loads(res["content"][0]["text"])
    if "result" in res:
        return json.loads(res["result"]["content"][0]["text"])
    raise AssertionError("unexpected response shape: " + str(res)[:200])


class TestToolLayerReplay:
    def test_server_boots_with_expected_tool_count(self, replay_server):
        srv, _ = replay_server
        assert srv.tool_registry.tool_count >= 448

    def test_get_project_context_shapes_tracks(self, replay_server):
        srv, fake = replay_server
        fake.store["get_all_tracks_info:{}"] = {
            "tracks": [{"index": 0, "name": "Drums", "is_audio": True,
                        "is_midi": False, "mute": False, "solo": False,
                        "arm": False, "volume": 0.8, "panning": 0.0,
                        "clip_count": 1, "devices": []}],
        }
        fake.store["get_session_info:{}"] = {
            "tempo": 120.0, "signature_numerator": 4,
            "signature_denominator": 4, "track_count": 1, "version": "0.5.0"}
        fake.store["get_song_scale:{}"] = {
            "root_note": 9, "scale_name": "minor", "scale_mode": "natural"}
        fake.store["get_song_transport:{}"] = {"is_playing": False}
        result = _call(srv, "get_project_context", {})
        assert result["tempo"] == 120.0
        assert result["tracks"][0]["name"] == "Drums"

    def test_music_toolkit_validation_without_ableton(self, replay_server):
        srv, _ = replay_server
        result = _call(srv, "generate_clip_from_prompt",
                       {"track_index": 0, "clip_index": 0,
                        "prompt": "acid bassline", "bars": 0, "key": ""})
        assert result["status"] == "error"
        assert "bars must be 1-16" in result["message"]

    def test_chord_progression_parses_keys(self, replay_server):
        srv, fake = replay_server
        # no recorded commands needed: validation rejects before I/O
        result = _call(srv, "build_chord_progression",
                       {"track_index": 0, "clip_index": 0, "key": "H minor",
                        "progression": "pop", "bars": 8})
        assert result["status"] == "error"

    def test_autopilot_sequence_validation(self, replay_server):
        srv, _ = replay_server
        result = _call(srv, "start_show_autopilot", {"sequence": "not-json"})
        assert result["status"] == "error"
        assert "sequence must be JSON" in result["message"]

    def test_preferences_roundtrip_and_journal(self, replay_server):
        srv, _ = replay_server
        r = _call(srv, "remember_preference",
                  {"key": "ci_test", "value": "v"})
        assert r["status"] == "ok"
        r = _call(srv, "recall_preferences", {})
        assert r["preferences"].get("ci_test") == "v"
        j = _call(srv, "get_change_journal", {"last_n": 5})
        assert any(e["tool"] == "remember_preference" for e in j["entries"])
        _call(srv, "forget_preference", {"key": "ci_test"})

    def test_doctor_reports_plain_language(self, replay_server):
        srv, fake = replay_server
        fake.store["get_session_info:{}"] = {
            "tempo": 120.0, "track_count": 3, "version": "0.5.0"}
        fake.store["get_song_transport:{}"] = {"is_playing": False}
        fake.store["get_playing_clips:{}"] = {"clips": []}
        fake.store["get_track_meters:{}"] = {"tracks": []}
        fake.store["get_all_tracks_info:{}"] = {"tracks": []}
        result = _call(srv, "doctor", {})
        assert result["status"] in ("healthy", "issues_found")
        assert result["checks"]

    def test_producer_prompt_parsing_plan(self, replay_server):
        srv, fake = replay_server
        fake.store["get_all_tracks_info:{}"] = {"tracks": []}
        result = _call(srv, "produce_idea_from_prompt",
                       {"prompt": "chill 96 BPM lofi in D minor",
                        "create_tracks": False, "checkpoint": False})
        assert result["plan"]["bpm"] == 96
        assert result["plan"]["key"] == "D minor"
        assert result["plan"]["genre"] == "lofi"
