"""Routing-preset path must be shared, portable and deterministic.

Regression guard for the v0.9.2 -> v0.9.3 fix: the MCP writer and the remote
script reader had both hardcoded ``~/.ableton-bridge/routing-presets.json``,
so copying an AbleSet project to another Mac lost the pc/wing presets. Both
sides now resolve the same configurable path, with the legacy path kept only
as a fallback.

The two resolver modules are loaded straight from their files: the remote one
has no Live dependencies, and importing it through the package would execute
``AbleBridgePlus/__init__.py`` (which needs Ableton's _Framework).
"""
import importlib.util
import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mcp_store = _load("mcp_preset_store", "MCP_Server/preset_store.py")
live_store = _load("live_preset_store", "AbleBridgePlus/preset_store.py")

ENV_PATH = "ABLETON_BRIDGE_PRESET_PATH"
ENV_DIR = "ABLETON_BRIDGE_PRESET_DIR"


@pytest.fixture(autouse=True)
def _isolate(monkeypatch, tmp_path):
    """No env override and no config file unless a test opts in."""
    monkeypatch.delenv(ENV_PATH, raising=False)
    monkeypatch.delenv(ENV_DIR, raising=False)
    config = tmp_path / "config.json"
    for module in (mcp_store, live_store):
        monkeypatch.setattr(module, "CONFIG_PATH", str(config))
    return config


def test_legacy_fallback_when_nothing_configured(_isolate):
    assert mcp_store.resolve_preset_path() == mcp_store.LEGACY_PATH
    assert live_store.resolve_preset_path() == live_store.LEGACY_PATH


def test_both_sides_agree(_isolate):
    assert mcp_store.resolve_preset_path() == live_store.resolve_preset_path()


def test_env_full_path_wins(_isolate, tmp_path, monkeypatch):
    target = tmp_path / "AbleSet" / "AudioProfiles" / "routing-presets.json"
    monkeypatch.setenv(ENV_PATH, str(target))
    assert mcp_store.resolve_preset_path() == str(target)
    assert live_store.resolve_preset_path() == str(target)


def test_env_directory_wins(_isolate, tmp_path, monkeypatch):
    directory = tmp_path / "AudioProfiles"
    monkeypatch.setenv(ENV_DIR, str(directory))
    expected = str(directory / "routing-presets.json")
    assert mcp_store.resolve_preset_path() == expected
    assert live_store.resolve_preset_path() == expected


def test_config_file_path(_isolate):
    target = "/Users/me/Music/Ableton/Projects/Live Show/Ableton Project/" \
             "AbleSet/AudioProfiles/routing-presets.json"
    _isolate.write_text(json.dumps({"routing_presets_path": target}),
                        encoding="utf-8")
    assert mcp_store.resolve_preset_path() == target
    assert live_store.resolve_preset_path() == target


def test_config_file_directory(_isolate):
    directory = "/Users/me/Music/Ableton/Projects/Live Show/Ableton Project/" \
                "AbleSet/AudioProfiles"
    _isolate.write_text(json.dumps({"routing_presets_dir": directory}),
                        encoding="utf-8")
    expected = os.path.join(directory, "routing-presets.json")
    assert mcp_store.resolve_preset_path() == expected
    assert live_store.resolve_preset_path() == expected


def test_env_beats_config(_isolate, tmp_path, monkeypatch):
    _isolate.write_text(json.dumps({
        "routing_presets_path": "/configured/path/routing-presets.json"}),
        encoding="utf-8")
    from_env = str(tmp_path / "from-env.json")
    monkeypatch.setenv(ENV_PATH, from_env)
    assert mcp_store.resolve_preset_path() == from_env
    assert live_store.resolve_preset_path() == from_env


def test_malformed_config_falls_back_to_legacy(_isolate):
    _isolate.write_text("{not json", encoding="utf-8")
    assert mcp_store.resolve_preset_path() == mcp_store.LEGACY_PATH
    assert live_store.resolve_preset_path() == live_store.LEGACY_PATH


def test_tilde_in_config_is_expanded(_isolate):
    target = "~/Documents/Ableton/AbleSet/AudioProfiles/routing-presets.json"
    _isolate.write_text(json.dumps({"routing_presets_path": target}),
                        encoding="utf-8")
    expected = os.path.expanduser(target)
    assert mcp_store.resolve_preset_path() == expected
    assert live_store.resolve_preset_path() == expected
