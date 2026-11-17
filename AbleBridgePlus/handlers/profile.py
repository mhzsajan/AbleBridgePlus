"""Zero-AI audio-profile switching (remote-script side).

AbleSet Canvas buttons send raw OSC UDP to the remote script on port 9883,
e.g. ``/profile/wing`` or ``/profile/pc`` (optionally with one string argument).
The listener in ``AbleBridgePlus/__init__.py`` decodes those datagrams here and
defers the actual Live API work to Ableton's main thread.

The presets themselves are the shared source of truth built by the MCP tool
``MCP_Server/tools/output_routing.py``:

    ~/.ableton-bridge/routing-presets.json
    {"version": 1, "presets": {"wing": {"name": ..., "description": ...,
      "track_count": 49, "tracks": [{"index": N, "name": "TrackName",
      "output_type": "Ext. Out", "output_channel": "1/2"}, ...]}}}

Only output routing is written.  The global audio device (PC speakers vs WING
USB) is outside Live's object model and remains a MANUAL switch; this module
never claims otherwise.  If the WING is not connected, ``set_track_routing``
cannot resolve its output name and the error is reported honestly per track.

Python 2.7 compatible (Live 10's embedded Python): no f-strings, no annotations.
"""
from __future__ import absolute_import, print_function, unicode_literals

import io
import json
import os
import struct

from . import tracks

# OSC addresses the listener will act on.  Any other /profile/<name> is also
# accepted when <name> is a preset in the shared JSON file.
OSC_ADDRESS_PREFIX = "/profile/"
KNOWN_PROFILE_ADDRESSES = ("/profile/pc", "/profile/wing", "/profile/status")

# Same relative location as MCP_Server/tools/output_routing.py::_PRESET_PATH.
PRESET_RELATIVE_PATH = os.path.join(".ableton-bridge", "routing-presets.json")


# ---------------------------------------------------------------------------
# Minimal OSC decoder (~40 lines) -- no python-osc dependency in Live.
# ---------------------------------------------------------------------------

def _osc_padded(length):
    """OSC strings occupy a whole number of 4-byte words, NUL included."""
    return (length + 3) & ~3


def _osc_read_string(data, offset):
    """Read one NUL-terminated, 4-byte-padded OSC string -> (bytes, next)."""
    nul = data.find(b"\x00", offset)
    if nul < 0:
        return b"", len(data)
    return data[offset:nul], offset + _osc_padded(nul - offset + 1)


def decode_osc_message(data):
    """Decode one OSC datagram -> (address, args).

    Supports the type tags a Canvas button could plausibly send: ``s`` (str),
    ``i`` (32-bit big-endian int), ``f`` (32-bit big-endian float), plus the
    valueless ``T``/``F``/``N`` tags.  Anything malformed returns ``(None, [])``
    so the listener can ignore it without ever touching the Live API.
    """
    try:
        address_bytes, pos = _osc_read_string(data, 0)
        if not address_bytes:
            return None, []
        address = address_bytes.decode("utf-8", "replace")
        if pos >= len(data):
            return address, []
        tag_bytes, pos = _osc_read_string(data, pos)
        if not tag_bytes.startswith(b","):
            return address, []
        args = []
        for tag in tag_bytes[1:].decode("ascii", "replace"):
            if tag == "s":
                value, pos = _osc_read_string(data, pos)
                args.append(value.decode("utf-8", "replace"))
            elif tag in ("i", "f"):
                if pos + 4 > len(data):
                    break
                fmt = ">i" if tag == "i" else ">f"
                args.append(struct.unpack(fmt, data[pos:pos + 4])[0])
                pos += 4
            elif tag in ("T", "F", "N"):
                args.append({"T": True, "F": False, "N": None}[tag])
            else:
                # Unknown tag: its byte width is unknown, so stop rather than
                # risk misinterpreting the rest of the packet.
                break
        return address, args
    except Exception:
        return None, []


# ---------------------------------------------------------------------------
# Preset store helpers
# ---------------------------------------------------------------------------

def _default_preset_path():
    return os.path.join(os.path.expanduser("~"), PRESET_RELATIVE_PATH)


def _load_store(path=None):
    """Return (store, error) -- never raises, so the listener cannot crash."""
    target = path or _default_preset_path()
    try:
        with io.open(target, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict) and isinstance(data.get("presets"), dict):
            return data, None
        return {"presets": {}}, "Preset file has an unexpected format: {0}".format(target)
    except (IOError, OSError) as e:
        return {"presets": {}}, "Cannot read preset file {0}: {1}".format(target, e)
    except ValueError as e:
        return {"presets": {}}, "Invalid JSON in preset file {0}: {1}".format(target, e)


def list_preset_names(path=None):
    """Plain list of available preset names (used for /profile/status)."""
    store, _error = _load_store(path)
    return sorted(store.get("presets", {}).keys())


def _norm_channel(value):
    """Live reports an unused output channel as '' -- treat that as 'unset'."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


# ---------------------------------------------------------------------------
# Applier -- runs on Ableton's main thread via schedule_message.
# ---------------------------------------------------------------------------

def apply_profile(ctrl, name, preset_path=None):
    """Apply one saved output-routing preset; return a plain result dict.

    ``preset_path`` is optional and only exists to make this testable offline;
    production always reads the shared ~/.ableton-bridge/routing-presets.json.
    The Live object is reached through ``ctrl._song`` exactly once, on the
    main thread; no Live API call happens on the OSC listener thread.
    """
    result = {"preset": name, "applied": 0, "skipped": 0,
              "errors": [], "mismatches": []}

    store, load_error = _load_store(preset_path)
    if load_error:
        result["errors"].append({"error": load_error})
        return result

    presets = store.get("presets", {})
    preset = presets.get(name)
    if preset is None:
        result["errors"].append({
            "error": "Preset '{0}' not found (available: {1})".format(
                name, ", ".join(sorted(presets.keys()))) })
        return result

    song = ctrl._song
    track_count = len(song.tracks)

    for entry in preset.get("tracks", []) or []:
        if not isinstance(entry, dict):
            result["skipped"] += 1
            result["errors"].append({"error": "Malformed preset entry: {0}".format(entry)})
            continue

        index = entry.get("index")
        label = entry.get("name") or ""
        target_type = entry.get("output_type")
        target_channel = _norm_channel(entry.get("output_channel"))

        # Honest bounds check: a track removed since the preset was saved is
        # skipped, never silently re-created.  Name match is a best-effort
        # fallback because indices shift after any setlist edit.
        if (not isinstance(index, int) or isinstance(index, bool)
                or index < 0 or index >= track_count):
            match = None
            if label:
                for i, track in enumerate(song.tracks):
                    if getattr(track, "name", None) == label:
                        match = i
                        break
            if match is None:
                result["skipped"] += 1
                result["errors"].append({
                    "index": index, "name": label,
                    "error": "track index out of range and no name match"})
                continue
            index = match

        if not target_type:
            result["skipped"] += 1
            result["errors"].append({
                "index": index, "name": label,
                "error": "preset entry has no output_type"})
            continue

        # OUTPUT ONLY -- input routing and mixer state are never touched.
        try:
            options = {"output_type": target_type, "ctrl": ctrl}
            if target_channel is not None:
                options["output_channel"] = target_channel
            tracks.set_track_routing(song, index, **options)
        except Exception as e:
            # e.g. WING USB not connected -> 'Ext. Out' not in available list.
            result["errors"].append({
                "index": index, "name": label,
                "error": "set_track_routing failed: {0}".format(e)})
            continue

        # Verify with a read-back, just like the MCP apply path does.
        try:
            after = tracks.get_track_routing(song, index, ctrl=ctrl)
        except Exception as e:
            result["errors"].append({
                "index": index, "name": label,
                "error": "read-back failed: {0}".format(e)})
            continue
        actual_type = after.get("output_routing_type")
        actual_channel = _norm_channel(after.get("output_routing_channel"))
        if (actual_type != target_type
                or (target_channel is not None and actual_channel != target_channel)):
            result["mismatches"].append({
                "index": index, "name": label,
                "expected": {"output_type": target_type,
                             "output_channel": target_channel},
                "actual": {"output_type": actual_type,
                           "output_channel": actual_channel}})
            continue

        result["applied"] += 1

    return result
