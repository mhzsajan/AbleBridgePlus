"""
Project Context Engine for AbleBridgePlus.

Gives an AI a compact, high-signal view of the whole Live set in one call,
plus server-side checkpoints so experiments can be diffed and reverted
without wading through dozens of individual tool calls.
"""
import logging
import time
from typing import Any, Dict, List

from mcp.server.fastmcp import Context

from MCP_Server.tools._base import _tool_handler
from MCP_Server.connections.ableton import get_ableton_connection
from MCP_Server import checkpoints as store

logger = logging.getLogger("MCP_Server.project_context")


def register_tools(mcp):
    """Register project-context tools (new-style register_tools pattern)."""

    @mcp.tool()
    @_tool_handler("building project context")
    def get_project_context(ctx: Context, include_devices: bool = False,
                            include_clips: bool = True) -> str:
        """
        Get a compact overview of the ENTIRE Live set in one call: tempo,
        time signature, scale/key, transport state, every track (name, type,
        color, volume, pan, mute/solo/arm, routing) and its clips.

        This is the fastest way to understand a project before working on it
        — one call instead of dozens of get_track_info calls.
        """
        ableton = get_ableton_connection()
        session = ableton.send_command("get_session_info")
        scale = ableton.send_command("get_song_scale")
        transport = ableton.send_command("get_song_transport")

        tracks: List[Dict[str, Any]] = []
        all_tracks = ableton.send_command("get_all_tracks_info")
        for t in all_tracks.get("tracks", []):
            entry: Dict[str, Any] = {
                "index": t.get("index"),
                "name": t.get("name"),
                "type": ("audio" if t.get("is_audio") else
                         "midi" if t.get("is_midi") else "return/master"),
                "mute": t.get("mute"), "solo": t.get("solo"),
                "arm": t.get("arm"),
                "volume": round(float(t.get("volume", 1.0)), 3),
                "panning": round(float(t.get("panning", 0.0)), 3),
            }
            if include_clips:
                slots = []
                try:
                    info = ableton.send_command("get_track_info",
                                                {"track_index": t["index"]})
                    for slot in info.get("clip_slots", []):
                        clip = slot.get("clip")
                        if clip:
                            slots.append({
                                "slot": slot.get("index"),
                                "name": clip.get("name"),
                                "length": clip.get("length"),
                            })
                except Exception:
                    pass
                if slots:
                    entry["clips"] = slots
            tracks.append(entry)

        import json as _json
        return _json.dumps({
            "tempo": session.get("tempo"),
            "time_signature": "{}/{}".format(session.get("signature_numerator", 4),
                                             session.get("signature_denominator", 4)),
            "scale": scale if scale else None,
            "transport": transport,
            "track_count": session.get("track_count"),
            "tracks": tracks,
        }, default=str)

    @mcp.tool()
    @_tool_handler("getting clip context")
    def get_clip_context(ctx: Context, track_index: int, clip_index: int) -> str:
        """
        Deep context for ONE clip in one call: notes summary (count, pitch
        range, average velocity, rhythmic density), loop state, launch mode,
        warp/loop markers and name/color — everything needed before editing.
        """
        ableton = get_ableton_connection()
        clip = ableton.send_command("get_clip_info",
                                    {"track_index": track_index,
                                     "clip_index": clip_index})
        summary: Dict[str, Any] = {
            "track_index": track_index, "clip_index": clip_index,
            "name": clip.get("name"), "length": clip.get("length"),
            "looping": clip.get("looping"), "start": clip.get("start"),
            "end": clip.get("end"),
        }
        # get_clip_info does not reliably flag MIDI clips — probe the notes
        # directly and treat success as the MIDI indicator.
        try:
            notes = ableton.send_command("get_clip_notes",
                                         {"track_index": track_index,
                                          "clip_index": clip_index})
            note_list = notes.get("notes", [])
            pitches = [n.get("pitch", 0) for n in note_list]
            velocities = [n.get("velocity", 0) for n in note_list]
            summary["is_midi"] = True
            summary["note_count"] = len(note_list)
            if pitches:
                summary["pitch_range"] = [min(pitches), max(pitches)]
                summary["avg_velocity"] = round(sum(velocities) / len(velocities), 1)
                summary["density_per_beat"] = round(
                    len(note_list) / max(clip.get("length", 4.0) or 4.0, 0.001), 2)
        except Exception:
            summary["is_midi"] = False
        import json as _json
        return _json.dumps(summary, default=str)

    @mcp.tool()
    @_tool_handler("creating checkpoint")
    def create_checkpoint(ctx: Context, name: str, overwrite: bool = False) -> str:
        """
        Snapshot the set structure (tracks + clips layout + scenes) under a
        name so you can diff later with checkpoint_diff or go back with
        restore_checkpoint. Use before risky edits:
        create_checkpoint("before-overhaul") -> experiment freely ->
        checkpoint_diff("before-overhaul") to see what changed, or
        restore_checkpoint("before-overhaul") to undo it all.

        Refuses to replace an existing name unless overwrite=True, so a
        restore point cannot silently move after you created it.

        v0.6: stored in the shared undo-safety store — persists across
        server restarts and is visible to list_checkpoints/rollback tools.
        """
        ableton = get_ableton_connection()
        snapshot = store.capture_snapshot(ableton)
        tracks_captured = store.store_named(name, snapshot, overwrite=overwrite)
        import json as _json
        return _json.dumps({
            "status": "checkpoint_created", "name": name,
            "tracks_captured": tracks_captured,
            "scenes_captured": len(snapshot.get("scenes", [])),
            "note": "Use checkpoint_diff to compare, restore_checkpoint to "
                    "revert, or the undo tool for single-step Live undo.",
        })

    @mcp.tool()
    @_tool_handler("diffing checkpoint")
    def checkpoint_diff(ctx: Context, name: str) -> str:
        """
        Compare the current set structure against a named checkpoint made
        with create_checkpoint: added/removed/renamed tracks, mute/solo
        flips, volume/pan drift, clip changes and scene changes.
        Read-only — nothing is changed.
        """
        entry = store.get_named(name)
        if entry is None:
            available = [c["name"] for c in store.list_all()["named"]][:10]
            raise ValueError("No checkpoint named '{0}'. Create one with "
                             "create_checkpoint first. Available: {1}"
                             .format(name, available))
        ableton = get_ableton_connection()
        current = store.capture_snapshot(ableton)
        diff = store.diff_snapshots(entry["snapshot"], current)

        import json as _json
        return _json.dumps({
            "checkpoint": name,
            "age_seconds": round(time.time() - entry["created"], 1),
            "summary": "{0} added, {1} removed, {2} changed".format(
                len(diff["added"]), len(diff["removed"]), len(diff["changed"])),
            **diff,
        }, default=str)
