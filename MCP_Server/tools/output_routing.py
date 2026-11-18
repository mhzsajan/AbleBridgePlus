"""Named per-track audio output routing presets (PC <-> WING switching).

The live set has ~50 tracks whose outputs are assigned one by one. Re-pointing
every track between the PC's audio device and the WING console's USB outputs by
hand is tedious and error-prone. This module captures the output routing of
*every* track into a named preset and applies it back in one call.

Presets are written to the path resolved by ``MCP_Server.preset_store``: a
project-local ``AbleSet/AudioProfiles/routing-presets.json`` when configured,
otherwise the legacy ``~/.ableton-bridge/routing-presets.json``. Applying a
preset defaults to a dry run and verifies every write by reading the routing
back from Ableton.

Nothing here restructures the set: only each track's output routing type and
channel are read/written, using the existing ``get_track_routing`` /
``set_track_routing`` commands in the remote script.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from mcp.server.fastmcp import Context

from MCP_Server.connections.ableton import get_ableton_connection
from MCP_Server.preset_store import resolve_preset_path
from MCP_Server.tools._base import _tool_handler

_lock = threading.RLock()
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,63}$")


# ---------------------------------------------------------------------------
# Store helpers
# ---------------------------------------------------------------------------

def _load_store() -> Dict[str, Any]:
    try:
        with open(resolve_preset_path(), encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("presets"), dict):
            return data
    except (OSError, ValueError):
        pass
    return {"version": 1, "presets": {}}


def _write_store(store: Dict[str, Any]) -> None:
    """Atomic write, matching the checkpoint store's durability pattern."""
    target = resolve_preset_path()
    os.makedirs(os.path.dirname(target), exist_ok=True)
    tmp = target + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)
    os.replace(tmp, target)


def _valid_name(name: str) -> str:
    if not isinstance(name, str):
        raise ValueError("preset name must be a string")
    name = name.strip()
    if not _NAME_RE.match(name):
        raise ValueError(
            "preset name must be 1-64 characters: letters, digits, spaces, "
            "'.', '_' or '-' (start with a letter or digit)")
    return name


def _norm_channel(value: Any) -> Optional[str]:
    """Live reports an unused output channel as '' — treat that as 'unset'."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _capture_master(ableton) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Read the master track's output routing (PC 1/2 vs WING 41/42, etc.)."""
    try:
        info = ableton.send_command("get_master_routing") or {}
        if not info.get("output_routing_type"):
            return None, "master track exposes no output routing on this Live version"
        return {
            "output_type": info.get("output_routing_type"),
            "output_channel": _norm_channel(info.get("output_routing_channel")),
        }, None
    except Exception as e:
        return None, "master routing capture failed: {0}".format(e)


def _capture(ableton) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Read every track's current output routing in one bulk call + N reads."""
    all_info = ableton.send_command("get_all_tracks_info") or {}
    raw = all_info.get("tracks")
    if not isinstance(raw, list):
        raise RuntimeError("get_all_tracks_info did not return a track list")

    tracks: List[Dict[str, Any]] = []
    errors: List[str] = []
    for t in raw:
        idx = t.get("index")
        if not isinstance(idx, int):
            continue
        try:
            r = ableton.send_command("get_track_routing",
                                     {"track_index": idx}) or {}
            tracks.append({
                "index": idx,
                "name": r.get("track_name") or t.get("name"),
                "output_type": r.get("output_routing_type"),
                "output_channel": _norm_channel(r.get("output_routing_channel")),
            })
        except Exception as e:
            errors.append("track {0} ({1}): {2}".format(
                idx, t.get("name"), e))
    return tracks, errors


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def register_tools(mcp):
    @mcp.tool()
    @_tool_handler("capturing output routing preset")
    def save_output_preset(ctx: Context, name: str, description: str = "",
                           overwrite: bool = False) -> str:
        """Snapshot every track's current audio output routing as a named preset.

        Use this while the set is routed the way you want it (e.g. all outputs
        on the PC device -> save as 'pc'; all outputs on WING USB -> save as
        'wing'). Captures both the output type ('Main', 'Ext. Out', a group
        track, 'No Output', ...) and the output channel (e.g. '1/2').

        Parameters:
        - name: preset name, e.g. 'pc' or 'wing'
        - description: optional note about this routing
        - overwrite: allow replacing an existing preset (default False)
        """
        name = _valid_name(name)
        ableton = get_ableton_connection()
        tracks, read_errors = _capture(ableton)
        master, master_error = _capture_master(ableton)
        if master_error:
            read_errors.append("master: " + master_error)
        if not tracks:
            return json.dumps({
                "status": "error",
                "message": "Could not capture any track routing; nothing saved.",
                "read_errors": read_errors,
            })

        destinations = sorted({t["output_type"] for t in tracks
                               if t["output_type"]})
        with _lock:
            store = _load_store()
            if name in store["presets"] and not overwrite:
                return json.dumps({
                    "status": "error",
                    "message": "Preset '{0}' already exists; pass "
                               "overwrite=True to replace it.".format(name),
                })
            store["presets"][name] = {
                "name": name,
                "description": description or "",
                "created": time.time(),
                "track_count": len(tracks),
                "tracks": tracks,
                "master": master,
            }
            _write_store(store)
        return json.dumps({
            "status": "ok",
            "message": "Saved output routing preset '{0}' ({1} tracks).".format(
                name, len(tracks)),
            "name": name,
            "track_count": len(tracks),
            "distinct_output_destinations": len(destinations),
            "destinations": destinations,
            "read_errors": read_errors,
        })

    @mcp.tool()
    @_tool_handler("listing output routing presets")
    def list_output_presets(ctx: Context) -> str:
        """List saved output routing presets with their track counts."""
        with _lock:
            store = _load_store()
        presets = []
        for name, p in sorted(store["presets"].items()):
            presets.append({
                "name": name,
                "description": p.get("description", ""),
                "created": p.get("created"),
                "track_count": p.get("track_count", len(p.get("tracks", []))),
            })
        return json.dumps({"status": "ok", "presets": presets,
                           "count": len(presets)})

    @mcp.tool()
    @_tool_handler("reading current output routing")
    def get_current_output_routing(ctx: Context) -> str:
        """Read every track's current output routing (read-only).

        Returns each track's index, name, output type and channel, plus the
        number of distinct output destinations — useful for checking what a
        preset would capture before saving it.
        """
        ableton = get_ableton_connection()
        tracks, read_errors = _capture(ableton)
        destinations = sorted({t["output_type"] for t in tracks
                               if t["output_type"]})
        return json.dumps({
            "status": "ok",
            "track_count": len(tracks),
            "distinct_output_destinations": len(destinations),
            "destinations": destinations,
            "tracks": tracks,
            "read_errors": read_errors,
        })

    @mcp.tool()
    @_tool_handler("applying output routing preset")
    def apply_output_preset(ctx: Context, name: str,
                            dry_run: bool = True) -> str:
        """Apply a saved output routing preset to the live set.

        Defaults to DRY RUN: reports exactly what would change without writing
        anything. Pass dry_run=False to actually route the tracks. Every write
        is verified by reading the track's routing back, and a per-track report
        of applied / already-matching / mismatched / skipped / errored tracks is
        returned. Tracks that no longer exist in the set are skipped, not
        recreated.

        Parameters:
        - name: preset name to apply (see list_output_presets)
        - dry_run: True (default) = preview only; False = apply and verify
        """
        name = _valid_name(name)
        with _lock:
            store = _load_store()
            preset = store["presets"].get(name)
        if not preset:
            return json.dumps({
                "status": "error",
                "message": "Output routing preset '{0}' not found.".format(name),
            })

        ableton = get_ableton_connection()
        try:
            all_info = ableton.send_command("get_all_tracks_info") or {}
            live_indexes = {
                t.get("index") for t in (all_info.get("tracks") or [])
                if isinstance(t.get("index"), int)
            }
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": "Could not read the live track list; nothing "
                           "changed: {0}".format(e),
            })

        applied: List[Dict[str, Any]] = []
        already: List[Dict[str, Any]] = []
        planned: List[Dict[str, Any]] = []
        skipped: List[Dict[str, Any]] = []
        mismatches: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        for entry in preset.get("tracks", []):
            idx = entry.get("index")
            target_type = entry.get("output_type")
            target_ch = _norm_channel(entry.get("output_channel"))
            label = entry.get("name")
            if idx not in live_indexes:
                skipped.append({"index": idx, "name": label,
                                "reason": "track no longer in set"})
                continue
            if target_type is None:
                skipped.append({"index": idx, "name": label,
                                "reason": "preset has no output type"})
                continue

            try:
                cur = ableton.send_command("get_track_routing",
                                           {"track_index": idx}) or {}
            except Exception as e:
                errors.append({"index": idx, "name": label,
                               "error": "read failed: {0}".format(e)})
                continue

            cur_type = cur.get("output_routing_type")
            cur_ch = _norm_channel(cur.get("output_routing_channel"))
            plan = {
                "index": idx,
                "name": label,
                "from": {"output_type": cur_type, "output_channel": cur_ch},
                "to": {"output_type": target_type, "output_channel": target_ch},
            }
            if cur_type == target_type and (target_ch is None or cur_ch == target_ch):
                already.append(plan)
                continue
            if dry_run:
                planned.append(plan)
                continue

            params: Dict[str, Any] = {"track_index": idx,
                                       "output_type": target_type}
            if target_ch is not None:
                params["output_channel"] = target_ch
            try:
                ableton.send_command("set_track_routing", params)
                after = ableton.send_command("get_track_routing",
                                             {"track_index": idx}) or {}
                got_type = after.get("output_routing_type")
                got_ch = _norm_channel(after.get("output_routing_channel"))
                if got_type == target_type and (target_ch is None or got_ch == target_ch):
                    applied.append(plan)
                else:
                    mismatches.append({
                        "index": idx, "name": label,
                        "expected": {"output_type": target_type,
                                     "output_channel": target_ch},
                        "actual": {"output_type": got_type,
                                   "output_channel": got_ch},
                    })
            except Exception as e:
                errors.append({"index": idx, "name": label,
                               "error": str(e)})

        # --- master output routing: PC 1/2 vs WING 41/42 --------------------
        master_result = None
        master_info = preset.get("master")
        if isinstance(master_info, dict) and master_info.get("output_type"):
            cur_master, merr = _capture_master(ableton)
            target_mt = master_info.get("output_type")
            target_mc = _norm_channel(master_info.get("output_channel"))
            plan = {"from": cur_master,
                    "to": {"output_type": target_mt, "output_channel": target_mc}}
            if merr:
                errors.append({"master": merr})
            elif (cur_master and cur_master.get("output_type") == target_mt
                  and (target_mc is None
                       or cur_master.get("output_channel") == target_mc)):
                master_result = {"already_matching": True, "plan": plan}
            elif dry_run:
                master_result = {"would_change": True, "plan": plan}
            else:
                try:
                    params: Dict[str, Any] = {"output_type": target_mt}
                    if target_mc is not None:
                        params["output_channel"] = target_mc
                    ableton.send_command("set_master_routing", params)
                    after, _ = _capture_master(ableton)
                    if (after and after.get("output_type") == target_mt
                            and (target_mc is None
                                 or after.get("output_channel") == target_mc)):
                        master_result = {"applied": True, "plan": plan}
                    else:
                        master_result = {"mismatch": True, "expected": plan["to"],
                                         "actual": after}
                except Exception as e:
                    master_result = {"error": str(e)}
                    errors.append({"master": str(e)})

        return json.dumps({
            "status": "ok",
            "message": ("Dry run for preset '{0}': {1} track(s) would change. "
                        "Pass dry_run=False to apply.".format(name, len(planned))
                        if dry_run else
                        "Applied preset '{0}': {1} changed, {2} verified, "
                        "{3} mismatch(es).".format(
                            name, len(applied), len(already), len(mismatches))),
            "preset": name,
            "dry_run": dry_run,
            "tracks_in_preset": len(preset.get("tracks", [])),
            "would_change": len(planned) if dry_run else None,
            "planned": planned if dry_run else None,
            "already_matching": len(already),
            "applied_and_verified": len(applied) if not dry_run else None,
            "mismatches": mismatches,
            "skipped": skipped,
            "errors": errors,
            "master": master_result,
        })

    @mcp.tool()
    @_tool_handler("deleting output routing preset")
    def delete_output_preset(ctx: Context, name: str) -> str:
        """Delete a named output routing preset.

        Parameters:
        - name: preset name to remove
        """
        name = _valid_name(name)
        with _lock:
            store = _load_store()
            if name not in store["presets"]:
                return json.dumps({
                    "status": "error",
                    "message": "Output routing preset '{0}' not found.".format(name),
                })
            del store["presets"][name]
            _write_store(store)
        return json.dumps({"status": "ok",
                           "message": "Deleted output routing preset '{0}'.".format(name)})
