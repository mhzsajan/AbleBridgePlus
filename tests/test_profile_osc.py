"""Offline tests for the zero-AI audio-profile OSC path.

The remote script normally runs inside Ableton, so ``_Framework.ControlSurface``
is stubbed just enough to import it outside Live. No Live objects are used:
apply_profile is exercised against plain fake tracks and a temporary preset
file passed via its explicit ``preset_path`` parameter.
"""
from __future__ import absolute_import

import json
import struct
import sys
import types

import pytest

# Importing AbleBridgePlus.handlers.profile pulls in the control surface, which
# only exists inside Live. Stub it before the import (never overwrite a real one).
if "_Framework.ControlSurface" not in sys.modules:
    _framework = types.ModuleType("_Framework")
    _control_surface = types.ModuleType("_Framework.ControlSurface")

    class _ControlSurface(object):
        pass

    _control_surface.ControlSurface = _ControlSurface
    _framework.ControlSurface = _control_surface
    sys.modules.setdefault("_Framework", _framework)
    sys.modules.setdefault("_Framework.ControlSurface", _control_surface)

from AbleBridgePlus.handlers import profile as profile_mod  # noqa: E402


# ---------------------------------------------------------------------------
# OSC wire helpers: address/type-tag strings are NUL-terminated and padded to 4
# ---------------------------------------------------------------------------

def _osc_string(text):
    raw = text.encode("utf-8") + b"\x00"
    return raw + b"\x00" * ((4 - len(raw) % 4) % 4)


def _build_osc(address, *args):
    packet = _osc_string(address)
    if args:
        tags = "".join("s" if isinstance(a, str) else "i" for a in args)
        packet += _osc_string("," + tags)
        for arg in args:
            if isinstance(arg, str):
                packet += _osc_string(arg)
            else:
                packet += struct.pack(">i", arg)
    return packet


# ---------------------------------------------------------------------------
# Decoder
# ---------------------------------------------------------------------------

def test_decode_profile_wing_without_args():
    address, args = profile_mod.decode_osc_message(_build_osc("/profile/wing"))
    assert address == "/profile/wing"
    assert args == []


def test_decode_profile_pc_with_string_arg():
    packet = _build_osc("/profile/pc", "PC Audio")
    assert packet[:12] == b"/profile/pc\x00"  # address padded to 4 bytes
    address, args = profile_mod.decode_osc_message(packet)
    assert address == "/profile/pc"
    assert args == ["PC Audio"]


def test_decode_int_arg_and_ignore_malformed():
    address, args = profile_mod.decode_osc_message(
        _build_osc("/profile/status", 7))
    assert (address, args) == ("/profile/status", [7])
    assert profile_mod.decode_osc_message(b"\x00\x01garbage")[0] is None
    assert profile_mod.decode_osc_message(b"")[0] is None
    assert profile_mod.decode_osc_message(_build_osc("/other/thing")) == (
        "/other/thing", [])


# ---------------------------------------------------------------------------
# apply_profile
# ---------------------------------------------------------------------------

class _RoutingOption(object):
    def __init__(self, name):
        self.display_name = name


class _FakeTrack(object):
    def __init__(self, name):
        self.name = name
        self.output_routing_type = _RoutingOption("Master")
        self.output_routing_channel = _RoutingOption("1/2")
        self.input_routing_type = _RoutingOption("No Input")
        self.input_routing_channel = _RoutingOption("All Channels")
        self.available_input_routing_types = [_RoutingOption("No Input")]
        self.available_input_routing_channels = [_RoutingOption("All Channels")]
        self.available_output_routing_types = [
            _RoutingOption("Master"), _RoutingOption("Ext. Out")]
        self.available_output_routing_channels = [
            _RoutingOption("1/2"), _RoutingOption("3/4")]


class _FakeMaster(object):
    """Minimal master track for the device-adaptive master step."""
    name = "Master"
    output_routing_type = type("T", (), {"display_name": "Ext. Out"})()
    output_routing_channel = type("C", (), {"display_name": "1/2"})()
    available_output_routing_types = [output_routing_type]
    available_output_routing_channels = [output_routing_channel]


class _FakeSong(object):
    def __init__(self, names):
        self.tracks = [_FakeTrack(name) for name in names]
        self.master_track = _FakeMaster()


class _FakeCtrl(object):
    def __init__(self, names):
        self._song = _FakeSong(names)
        self.messages = []

    def log_message(self, message):
        self.messages.append(message)


def _write_preset(tmp_path, name, tracks):
    path = tmp_path / "routing-presets.json"
    path.write_text(json.dumps({
        "version": 1,
        "presets": {name: {"name": name, "description": "test",
                           "track_count": len(tracks), "tracks": tracks}},
    }), encoding="utf-8")
    return str(path)


def test_apply_profile_applies_verifies_and_reports_errors(tmp_path):
    path = _write_preset(tmp_path, "wing", [
        {"index": 0, "name": "KICK", "output_type": "Ext. Out",
         "output_channel": "1/2"},
        {"index": 1, "name": "SNARE", "output_type": "No Output",
         "output_channel": None},  # not available -> honest error
        {"index": 99, "name": "GONE", "output_type": "Master",
         "output_channel": None},  # out of range -> skipped + error
    ])
    ctrl = _FakeCtrl(["KICK", "SNARE"])

    result = profile_mod.apply_profile(ctrl, "wing", preset_path=path)

    assert result["preset"] == "wing"
    assert result["applied"] == 1
    assert result["skipped"] == 1
    assert result["mismatches"] == []
    assert len(result["errors"]) == 2
    assert "set_track_routing failed" in result["errors"][0]["error"]
    assert "out of range" in result["errors"][1]["error"]
    # Verified through the real read-back helper, not assumed from the write.
    assert ctrl._song.tracks[0].output_routing_type.display_name == "Ext. Out"


def test_apply_profile_never_writes_input_fields(tmp_path, monkeypatch):
    path = _write_preset(tmp_path, "pc", [
        {"index": 0, "name": "KICK", "output_type": "Master",
         "output_channel": "1/2"}])
    ctrl = _FakeCtrl(["KICK"])
    calls = []
    real_set = profile_mod.tracks.set_track_routing

    def spy(song, index, **kwargs):
        calls.append((index, kwargs))
        return real_set(song, index, **kwargs)

    monkeypatch.setattr(profile_mod.tracks, "set_track_routing", spy)
    result = profile_mod.apply_profile(ctrl, "pc", preset_path=path)

    assert result["applied"] == 1
    assert len(calls) == 1
    assert calls[0][0] == 0
    assert calls[0][1] == {"output_type": "Master",
                           "output_channel": "1/2", "ctrl": ctrl}


def test_apply_profile_unknown_preset_and_missing_file(tmp_path):
    path = _write_preset(tmp_path, "wing", [])
    ctrl = _FakeCtrl(["KICK"])

    missing = profile_mod.apply_profile(ctrl, "nope", preset_path=path)
    assert missing["applied"] == 0
    assert "not found" in missing["errors"][0]["error"]

    no_file = profile_mod.apply_profile(
        ctrl, "wing", preset_path=str(tmp_path / "absent.json"))
    assert no_file["applied"] == 0
    assert "Cannot read preset file" in no_file["errors"][0]["error"]


def test_preset_names_are_listed(tmp_path):
    path = _write_preset(tmp_path, "wing", [])
    assert profile_mod.list_preset_names(path) == ["wing"]
