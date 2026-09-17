"""Undo-safe checkpoint store for AbleBridgePlus (v0.6 "Full Circle").

Two layers of safety net:

1. **Named checkpoints** (create_checkpoint / restore / diff) — explicit
   snapshots an agent or user creates before risky work.

2. **Automatic checkpoints** — every mutating tool call snapshots the set
   *before* its side effects (hooked in _tool_handler, same choke point as
   the change journal). Kept in a capped ring; `rollback` restores the last
   one, `safe_experiment` wraps sequences with auto-rollback on failure.

Snapshots are "deep enough to restore structure and mixer state": per track
(name, type, mixer, color, arm) plus scene count/names and which clip slots
hold clips. Clip *contents* (notes/warping) are not duplicated — Live's own
undo remains the tool for micro-edits; this layer guarantees the AI can
restore the macro shape of the set even when Live's undo bypasses remote
script operations.

Named checkpoints persist to ~/.ableton-bridge/checkpoints.json so they
survive MCP server restarts; automatic ones live in memory only.
"""
from __future__ import annotations

import json
import logging
import os
import time
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger("AbletonBridge")

_AUTO_LIMIT = 20            # ring size for automatic checkpoints
_NAMED_LIMIT = 50           # persistent named checkpoints

_lock = threading.RLock()
_auto: List[Dict[str, Any]] = []       # newest last
_named: Dict[str, Dict[str, Any]] = {} # name -> {"created": ts, "snapshot": {...}}

_DISK_PATH = os.path.join(
    os.path.expanduser("~"), ".ableton-bridge", "checkpoints.json")


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------

def capture_snapshot(ableton) -> Dict[str, Any]:
    """Capture the restoreable shape of the current set via one connection.

    Uses get_all_tracks_info (tracks + mixer + clips) and get_scene_names /
    get_session_info for the scene dimension. Never raises on individual
    sub-calls — a partial snapshot beats no snapshot.
    """
    tracks: List[Dict[str, Any]] = []
    try:
        all_tracks = ableton.send_command("get_all_tracks_info") or {}
        for t in all_tracks.get("tracks", []):
            entry = {
                "index": t.get("index"),
                "name": t.get("name"),
                "is_audio": bool(t.get("is_audio")),
                "is_midi": bool(t.get("is_midi")),
                "mute": bool(t.get("mute")),
                "solo": bool(t.get("solo")),
                "arm": bool(t.get("arm")),
                "volume": t.get("volume"),
                "panning": t.get("panning"),
            }
            try:
                info = ableton.send_command("get_track_info",
                                            {"track_index": t["index"]})
                entry["color_index"] = info.get("color_index")
                clips = []
                for slot in info.get("clip_slots", []):
                    clip = slot.get("clip")
                    if clip:
                        clips.append({
                            "slot": slot.get("index"),
                            "name": clip.get("name"),
                            "length": clip.get("length"),
                        })
                entry["clips"] = clips
            except Exception:
                pass
            tracks.append(entry)
    except Exception as e:
        logger.warning("checkpoint capture: get_all_tracks_info failed: %s", e)

    scenes: List[str] = []
    try:
        sn = ableton.send_command("get_scenes") or {}
        scenes = [str(s.get("name", "")) for s in sn.get("scenes", [])]
    except Exception:
        pass

    tempo = None
    try:
        tempo = (ableton.send_command("get_session_info") or {}).get("tempo")
    except Exception:
        pass

    return {"captured_at": round(time.time(), 2), "tempo": tempo,
            "tracks": tracks, "scenes": scenes}


def _persist_named() -> None:
    try:
        os.makedirs(os.path.dirname(_DISK_PATH), exist_ok=True)
        tmp = _DISK_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_named, f)
        os.replace(tmp, _DISK_PATH)
    except OSError as e:
        logger.warning("checkpoint persistence failed: %s", e)


def load_persisted() -> None:
    """Load named checkpoints at server startup (best-effort)."""
    global _named
    try:
        with open(_DISK_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            with _lock:
                _named = data
    except (OSError, ValueError):
        pass


def store_auto(snapshot: Dict[str, Any], tool_name: str, args_summary: str) -> None:
    """Record an automatic pre-mutation checkpoint (capped ring)."""
    with _lock:
        _auto.append({
            "created": round(time.time(), 2),
            "trigger": {"tool": tool_name, "args": (args_summary or "")[:200]},
            "snapshot": snapshot,
        })
        del _auto[:-_AUTO_LIMIT]


def store_named(name: str, snapshot: Dict[str, Any]) -> int:
    """Store a named checkpoint. Returns track count captured."""
    with _lock:
        _named[name] = {"created": round(time.time(), 2), "snapshot": snapshot}
        while len(_named) > _NAMED_LIMIT:
            oldest = min(_named, key=lambda k: _named[k]["created"])
            del _named[oldest]
        _persist_named()
    return len(snapshot.get("tracks", []))


# ---------------------------------------------------------------------------
# Access
# ---------------------------------------------------------------------------

def list_all() -> Dict[str, Any]:
    """Summary of both layers for list_checkpoints."""
    with _lock:
        autos = [{"index": i, "created": a["created"],
                  "trigger": a["trigger"],
                  "tracks": len(a["snapshot"].get("tracks", []))}
                 for i, a in enumerate(_auto)]
        named = [{"name": n, "created": c["created"],
                  "tracks": len(c["snapshot"].get("tracks", []))}
                 for n, c in sorted(_named.items(), key=lambda kv: kv[1]["created"])]
    return {"automatic": autos, "named": named}


def get_auto(index: int = -1) -> Optional[Dict[str, Any]]:
    with _lock:
        if not _auto:
            return None
        try:
            return _auto[index]
        except IndexError:
            return None


def get_named(name: str) -> Optional[Dict[str, Any]]:
    with _lock:
        return _named.get(name)


def delete_named(name: str) -> bool:
    with _lock:
        if name in _named:
            del _named[name]
            _persist_named()
            return True
        return False


def clear_auto() -> int:
    with _lock:
        n = len(_auto)
        _auto.clear()
        return n


# ---------------------------------------------------------------------------
# Diff / Restore
# ---------------------------------------------------------------------------

def diff_snapshots(old: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    """Structure+mixer diff between a snapshot and the live set (or another)."""
    old_tracks = {t.get("index"): t for t in old.get("tracks", [])}
    cur_tracks = {t.get("index"): t for t in current.get("tracks", [])}
    added = [{"index": i, "name": t.get("name")}
             for i, t in cur_tracks.items() if i not in old_tracks]
    removed = [{"index": i, "name": t.get("name")}
               for i, t in old_tracks.items() if i not in cur_tracks]
    changed = []
    for i, t in cur_tracks.items():
        o = old_tracks.get(i)
        if not o:
            continue
        changes = {}
        for field in ("name", "mute", "solo", "arm", "volume", "panning",
                      "color_index"):
            if o.get(field) != t.get(field):
                changes[field] = [o.get(field), t.get(field)]
        old_clips = {(c.get("slot"), c.get("name")) for c in o.get("clips", [])}
        cur_clips = {(c.get("slot"), c.get("name")) for c in t.get("clips", [])}
        if old_clips != cur_clips:
            added_c = [c for c in t.get("clips", [])
                       if (c.get("slot"), c.get("name")) not in old_clips]
            removed_c = [c for c in o.get("clips", [])
                         if (c.get("slot"), c.get("name")) not in cur_clips]
            if added_c or removed_c:
                changes["clips"] = {"added": added_c, "removed": removed_c}
        if changes:
            changed.append({"index": i, "name": t.get("name"), "changes": changes})
    old_scenes = old.get("scenes") or []
    cur_scenes = current.get("scenes") or []
    scene_changes = None
    if old_scenes != cur_scenes:
        scene_changes = {"count": [len(old_scenes), len(cur_scenes)],
                         "renamed": [[o, c] for o, c in zip(old_scenes, cur_scenes) if o != c]}
    return {"added": added, "removed": removed, "changed": changed,
            "scenes": scene_changes,
            "tempo": ([old.get("tempo"), current.get("tempo")]
                      if old.get("tempo") != current.get("tempo") else None)}


def restore(ableton, snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Best-effort restore of the set shape from a snapshot.

    Strategy per dimension:
    - tempo: set if it changed
    - scenes: create missing scenes, rename by index where they exist
    - tracks: rename/remix/remute existing indices; create missing tracks
      of the right type; delete tracks that were not in the snapshot
    - clip slots: recreate clip presence (create_clip by length) — contents
      are not duplicated by design

    Returns a report dict; never raises for individual track issues.
    """
    report: Dict[str, Any] = {"tempo_set": None, "scenes": {},
                              "tracks": {"renamed": 0, "mixed": 0, "created": 0,
                                         "deleted": 0, "errors": []},
                              "clips": {"created": 0, "deleted": 0, "errors": []}}

    # --- tempo ---
    current = capture_snapshot(ableton)
    cur_tracks = {t.get("index"): t for t in current.get("tracks", [])}

    if snapshot.get("tempo") and current.get("tempo") and \
            abs(float(snapshot["tempo"]) - float(current["tempo"])) > 0.01:
        try:
            ableton.send_command("set_tempo", {"tempo": float(snapshot["tempo"])})
            report["tempo_set"] = float(snapshot["tempo"])
        except Exception as e:
            report["tracks"]["errors"].append("tempo: " + str(e))

    # --- scenes ---
    want_scenes = snapshot.get("scenes") or []
    if want_scenes:
        cur_scenes = current.get("scenes") or []
        try:
            while len(cur_scenes) < len(want_scenes):
                ableton.send_command("create_scene", {})
                cur_scenes.append("")
                report["scenes"]["created"] = report["scenes"].get("created", 0) + 1
            for i, name in enumerate(want_scenes):
                if name and i < len(cur_scenes) and cur_scenes[i] != name:
                    ableton.send_command("set_scene_name",
                                         {"scene_index": i, "name": name})
                    report["scenes"]["renamed"] = report["scenes"].get("renamed", 0) + 1
        except Exception as e:
            report["scenes"]["errors"] = [str(e)]

    # --- tracks ---
    want_tracks = snapshot.get("tracks", [])
    want_idx = {t.get("index") for t in want_tracks}
    for idx in sorted(cur_tracks.keys(), reverse=True):
        if idx not in want_idx and isinstance(idx, int) and idx >= 0:
            try:
                ableton.send_command("delete_track", {"track_index": idx})
                report["tracks"]["deleted"] += 1
            except Exception as e:
                report["tracks"]["errors"].append(
                    "delete track {0}: {1}".format(idx, e))
    for t in want_tracks:
        idx = t.get("index")
        cur = cur_tracks.get(idx)
        if cur is None:
            try:
                if t.get("is_audio"):
                    ableton.send_command("create_audio_track", {})
                else:
                    ableton.send_command("create_midi_track", {})
                report["tracks"]["created"] += 1
            except Exception as e:
                report["tracks"]["errors"].append(
                    "create track {0}: {1}".format(idx, e))
            continue
        mixer = {"track_index": idx}
        try:
            if t.get("name") and cur.get("name") != t["name"]:
                ableton.send_command("set_track_name",
                                     {"track_index": idx, "name": t["name"]})
                report["tracks"]["renamed"] += 1
            if t.get("volume") is not None and \
                    abs(float(t["volume"]) - float(cur.get("volume", -1))) > 0.001:
                ableton.send_command("set_track_volume",
                                     {"track_index": idx, "value": float(t["volume"])})
                report["tracks"]["mixed"] += 1
            if t.get("panning") is not None and \
                    abs(float(t["panning"]) - float(cur.get("panning", 999))) > 0.001:
                ableton.send_command("set_track_pan",
                                     {"track_index": idx, "value": float(t["panning"])})
                report["tracks"]["mixed"] += 1
            if bool(t.get("mute")) != bool(cur.get("mute")):
                ableton.send_command("set_track_mute",
                                     {"track_index": idx, "mute": bool(t.get("mute"))})
                report["tracks"]["mixed"] += 1
            if bool(t.get("solo")) != bool(cur.get("solo")):
                ableton.send_command("set_track_solo",
                                     {"track_index": idx, "solo": bool(t.get("solo"))})
                report["tracks"]["mixed"] += 1
        except Exception as e:
            report["tracks"]["errors"].append(
                "track {0}: {1}".format(idx, e))

    # --- clip presence ---
    # After track create/delete the indices may have shifted; capture again
    # and map by the *current* track list order to the snapshot order.
    try:
        fresh = capture_snapshot(ableton)
        fresh_tracks = fresh.get("tracks", [])
        if len(fresh_tracks) == len(want_tracks):
            for want, cur_t in zip(want_tracks, fresh_tracks):
                idx = cur_t.get("index")
                cur_clips = {(c.get("slot"), c.get("name"))
                             for c in cur_t.get("clips", [])}
                for c in want.get("clips", []):
                    if (c.get("slot"), c.get("name")) not in cur_clips:
                        try:
                            ableton.send_command("create_clip", {
                                "track_index": idx,
                                "clip_index": c.get("slot"),
                                "length": float(c.get("length") or 4.0)})
                            ableton.send_command("set_clip_name", {
                                "track_index": idx, "clip_index": c.get("slot"),
                                "name": c.get("name") or ""})
                            report["clips"]["created"] += 1
                        except Exception as e:
                            report["clips"]["errors"].append(
                                "track {0} slot {1}: {2}".format(idx, c.get("slot"), e))
        else:
            report["clips"]["errors"].append(
                "track count mismatch after restore; clip presence skipped")
    except Exception as e:
        report["clips"]["errors"].append(str(e))

    return report
