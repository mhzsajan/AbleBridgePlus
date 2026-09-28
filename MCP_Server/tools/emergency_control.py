"""
Emergency Control Tools for AbleBridgePlus MCP Server.

Provides emergency stop, panic mute, and backup scene activation for live shows.

These tools previously only flipped flags in this module and returned a
success message describing an action they never performed — ``panic_mute``
answered "Muted 3 tracks" while the PA stayed live. They now actually talk to
Ableton over the shared connection, and report what they could not do.

A safety tool that lies is worse than no safety tool: an operator who is told
the mute is engaged will not reach for the physical fader. Every path here
reports per-item outcomes and never claims an action it did not perform.
"""

import asyncio
from typing import Any, Dict, List, Optional
from . import tool


def _run(fn, *args, **kwargs):
    """Run a blocking Ableton call off the event loop.

    These are legacy (non-@_tool_handler) tools, so nothing else keeps the
    socket I/O off the shared asyncio loop.
    """
    return asyncio.to_thread(fn, *args, **kwargs)


class EmergencyControl:
    """Emergency control manager for live shows."""

    def __init__(self):
        """Initialize emergency control."""
        self.emergency_active = False
        self.backup_scene_index = None
        self.original_mute_states: Dict[int, bool] = {}

    # ------------------------------------------------------------------
    # Individual primitives (sync — always invoked through _run())
    # ------------------------------------------------------------------

    @staticmethod
    def _do_emergency_stop() -> Dict[str, Any]:
        from MCP_Server.connections.ableton import get_ableton_connection
        ableton = get_ableton_connection()
        stopped, errors = [], []

        # Stop every playing clip first, then halt the transport.
        try:
            ableton.send_command("stop_all_clips", {})
            stopped.append("all_clips")
        except Exception as e:
            errors.append("stop_all_clips: {0}".format(e))
        try:
            ableton.send_command("stop_playback", {})
            stopped.append("playback")
        except Exception as e:
            errors.append("stop_playback: {0}".format(e))

        return {"stopped": stopped, "errors": errors}

    @staticmethod
    def _resolve_track_indices(tracks: Optional[List[Any]]) -> List[int]:
        """Accept [0, 1, 2] or [{"index": 0, ...}]; None means every track."""
        from MCP_Server.connections.ableton import get_ableton_connection
        ableton = get_ableton_connection()

        if tracks is None:
            info = ableton.send_command("get_all_tracks_info") or {}
            return [t.get("index") for t in info.get("tracks", [])
                    if isinstance(t.get("index"), int)]

        out: List[int] = []
        for t in tracks:
            idx = t.get("index") if isinstance(t, dict) else t
            if isinstance(idx, bool) or not isinstance(idx, int) or idx < 0:
                continue
            out.append(idx)
        return out

    def _do_mute(self, tracks: Optional[List[Any]], mute: bool) -> Dict[str, Any]:
        from MCP_Server.connections.ableton import get_ableton_connection
        ableton = get_ableton_connection()

        indices = self._resolve_track_indices(tracks)
        changed, errors = [], []
        for idx in indices:
            try:
                if mute:
                    # Record the pre-panic state the first time so unmute can
                    # restore it instead of blanket-unmuting the set.
                    if idx not in self.original_mute_states:
                        info = ableton.send_command(
                            "get_track_info", {"track_index": idx}) or {}
                        self.original_mute_states[idx] = bool(info.get("mute"))
                ableton.send_command("set_track_mute",
                                     {"track_index": idx, "mute": mute})
                changed.append(idx)
            except Exception as e:
                errors.append("track {0}: {1}".format(idx, e))
        return {"changed": changed, "errors": errors, "requested": len(indices)}

    def _do_restore_mutes(self) -> Dict[str, Any]:
        """Put every panicked track back to the mute state it had before.

        Blanket-unmuting is NOT the same thing: a track that was already muted
        before the emergency must stay muted afterwards, or a panic/unmute
        cycle silently unmutes a channel the operator had deliberately killed.
        """
        from MCP_Server.connections.ableton import get_ableton_connection
        ableton = get_ableton_connection()

        restored, errors = [], []
        for idx, prior in list(self.original_mute_states.items()):
            try:
                ableton.send_command("set_track_mute",
                                     {"track_index": idx, "mute": bool(prior)})
                restored.append(idx)
            except Exception as e:
                errors.append("track {0}: {1}".format(idx, e))
        return {"changed": restored, "errors": errors,
                "requested": len(self.original_mute_states)}

    @staticmethod
    def _do_fire_scene(scene_index: int) -> Dict[str, Any]:
        from MCP_Server.connections.ableton import get_ableton_connection
        ableton = get_ableton_connection()
        ableton.send_command("fire_scene", {"scene_index": int(scene_index)})
        return {"scene_index": int(scene_index)}


# Global instance
_emergency_control = EmergencyControl()


@tool(
    name="emergency_stop",
    description="Emergency stop - stop all clips and playback instantly",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def emergency_stop() -> Dict[str, Any]:
    """Emergency stop - stop all clips and playback instantly."""
    try:
        res = await _run(_emergency_control._do_emergency_stop)
    except Exception as e:
        return {"status": "error",
                "message": "Emergency stop FAILED: {0}".format(e),
                "stopped": [], "errors": [str(e)]}

    _emergency_control.emergency_active = True
    ok = not res["errors"]
    return {
        "status": "emergency_stop_activated" if ok else "emergency_stop_partial",
        "message": ("Stopped all clips and halted playback"
                    if ok else
                    "PARTIAL emergency stop — check errors and use the physical "
                    "controls for anything not listed in 'stopped'"),
        "stopped": res["stopped"],
        "errors": res["errors"],
    }


@tool(
    name="panic_mute",
    description="Mute all tracks instantly for emergency situations",
    input_schema={
        "type": "object",
        "properties": {
            "tracks": {
                "type": "array",
                "description": "Optional track indices (or objects with an "
                               "'index' key) to mute. Omit to mute every track."
            }
        },
        "required": []
    }
)
async def panic_mute(tracks: Optional[List[Any]] = None) -> Dict[str, Any]:
    """Mute all tracks instantly for emergency situations."""
    try:
        res = await _run(_emergency_control._do_mute, tracks, True)
    except Exception as e:
        return {"status": "error",
                "message": "Panic mute FAILED: {0}".format(e),
                "muted_tracks": [], "errors": [str(e)]}

    ok = not res["errors"] and res["changed"]
    return {
        "status": "panic_mute_activated" if ok else "panic_mute_partial",
        "message": ("Muted {0} track(s)".format(len(res["changed"])) if ok else
                    "PARTIAL panic mute — {0} of {1} tracks muted; check "
                    "errors".format(len(res["changed"]), res["requested"])),
        "muted_tracks": res["changed"],
        "errors": res["errors"],
    }


@tool(
    name="panic_unmute",
    description="Unmute all tracks after panic mute",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def panic_unmute() -> Dict[str, Any]:
    """Unmute the tracks that panic_mute muted, restoring their prior state."""
    if not _emergency_control.original_mute_states:
        return {"status": "nothing_to_unmute",
                "message": "No panic mute is active; nothing changed.",
                "unmuted_tracks": [], "errors": []}
    targets = dict(_emergency_control.original_mute_states)
    try:
        res = await _run(_emergency_control._do_restore_mutes)
    except Exception as e:
        return {"status": "error",
                "message": "Panic unmute FAILED: {0}".format(e),
                "unmuted_tracks": [], "errors": [str(e)]}

    # Only forget the states we actually managed to put back, so a partial
    # failure can still be retried.
    for idx in res["changed"]:
        _emergency_control.original_mute_states.pop(idx, None)
    ok = not res["errors"] and len(targets) == len(res["changed"])
    return {
        "status": "panic_unmute_activated" if ok else "panic_unmute_partial",
        "message": ("Restored {0} track(s) to their pre-panic mute state".format(
            len(res["changed"])) if ok else
            "PARTIAL panic unmute — {0} of {1} tracks restored; check "
            "errors".format(len(res["changed"]), len(targets))),
        "unmuted_tracks": res["changed"],
        "errors": res["errors"],
    }


@tool(
    name="activate_backup_scene",
    description="Activate a backup scene in case of emergency",
    input_schema={
        "type": "object",
        "properties": {
            "scene_index": {
                "type": "integer",
                "description": "Zero-based index of the backup scene to fire"
            }
        },
        "required": ["scene_index"]
    }
)
async def activate_backup_scene(scene_index: int) -> Dict[str, Any]:
    """Activate a backup scene in case of emergency."""
    if isinstance(scene_index, bool) or not isinstance(scene_index, int) \
            or scene_index < 0:
        return {"status": "error",
                "message": "scene_index must be a non-negative integer",
                "errors": []}
    try:
        res = await _run(_emergency_control._do_fire_scene, scene_index)
    except Exception as e:
        return {"status": "error",
                "message": "Failed to fire backup scene {0}: {1}".format(
                    scene_index, e),
                "scene_index": scene_index, "errors": [str(e)]}

    _emergency_control.backup_scene_index = scene_index
    return {"status": "backup_scene_activated",
            "scene_index": res["scene_index"],
            "message": "Fired scene {0}".format(res["scene_index"]),
            "errors": []}


@tool(
    name="get_emergency_status",
    description="Get current emergency control status",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def get_emergency_status() -> Dict[str, Any]:
    """Get current emergency control status."""
    return {
        "status": "ok",
        "emergency_active": _emergency_control.emergency_active,
        "backup_scene_index": _emergency_control.backup_scene_index,
        "muted_tracks_count": len(_emergency_control.original_mute_states),
        "muted_tracks": sorted(_emergency_control.original_mute_states.keys()),
    }
