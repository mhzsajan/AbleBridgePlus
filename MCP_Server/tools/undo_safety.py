"""
Undo-safe experimentation tools for AbleBridgePlus (v0.6 "Full Circle").

Built on MCP_Server.checkpoints:
- list_checkpoints  — see both safety layers (named + automatic ring)
- rollback          — restore the last automatic pre-mutation snapshot
- restore_checkpoint — restore a named checkpoint (fills the ghost-tool gap:
  it was referenced in docs and the mutation list but never registered)
- safe_experiment   — run a sequence of tool calls; auto-rollback on failure
- delete_checkpoint — prune named checkpoints

Deep restore relies on the live remote handlers (set_tempo, track
create/delete/name/mixer, create_scene, set_scene_name, create_clip,
set_clip_name). Clip *contents* are not duplicated by design — Live's own
undo covers micro-edits; this layer restores the macro shape of the set.
"""
import json
import logging
from typing import Any, Dict

from mcp.server.fastmcp import Context

from MCP_Server.tools._base import _tool_handler
from MCP_Server.connections.ableton import get_ableton_connection
from MCP_Server import checkpoints as store

logger = logging.getLogger("MCP_Server.undo_safety")


def register_tools(mcp):
    """Register undo-safety tools (new-style register_tools pattern)."""

    @mcp.tool()
    @_tool_handler("listing checkpoints")
    def list_checkpoints(ctx: Context) -> str:
        """
        List every safety point available for undo: named checkpoints
        (persistent, made with create_checkpoint) and the automatic ring of
        pre-mutation snapshots (one captured before each mutating tool call).
        Automatic entries show which tool triggered them and when.
        """
        return json.dumps(store.list_all(), default=str)

    @mcp.tool()
    @_tool_handler("creating rollback point")
    def rollback(ctx: Context, steps_back: int = 1) -> str:
        """
        Undo-safe revert: restore the set to how it was just BEFORE a recent
        mutating tool call. steps_back=1 restores the most recent automatic
        checkpoint, 2 the one before it, and so on. Use list_checkpoints to
        see the ring. Restores structure + mixer + scene shape (clip contents
        are not duplicated; Live's undo handles micro-edits).
        """
        entry = store.get_auto(-abs(int(steps_back)))
        if entry is None:
            raise ValueError(
                "No automatic checkpoint at steps_back={0}. The ring fills as "
                "mutating tools run against a live set — see list_checkpoints."
                .format(steps_back))
        ableton = get_ableton_connection()
        report = store.restore(ableton, entry["snapshot"])
        report["restored_from"] = {
            "created": entry["created"],
            "trigger": entry["trigger"],
        }
        return json.dumps({"status": "rolled_back", **report}, default=str)

    @mcp.tool()
    @_tool_handler("restoring checkpoint")
    def restore_checkpoint(ctx: Context, name: str) -> str:
        """
        Restore a named checkpoint made with create_checkpoint. This is the
        big red button after a bad experiment: tracks, mixer state, scenes
        and clip presence go back to the checkpoint. Reports everything it
        changed. Named checkpoints persist across server restarts.
        """
        entry = store.get_named(name)
        if entry is None:
            available = [c["name"] for c in store.list_all()["named"]][:10]
            raise ValueError(
                "No checkpoint named '{0}'. Available: {1}".format(name, available))
        ableton = get_ableton_connection()
        report = store.restore(ableton, entry["snapshot"])
        return json.dumps({
            "status": "restored", "checkpoint": name,
            "checkpoint_age_seconds": round(
                __import__("time").time() - entry["created"], 1),
            **report,
        }, default=str)

    @mcp.tool()
    @_tool_handler("deleting checkpoint")
    def delete_checkpoint(ctx: Context, name: str) -> str:
        """Delete a named checkpoint to keep the store tidy."""
        if store.delete_named(name):
            return json.dumps({"status": "ok", "deleted": name})
        raise ValueError("No checkpoint named '{0}'".format(name))

    @mcp.tool()
    @_tool_handler("running safe experiment")
    def safe_experiment(ctx: Context, name: str, steps: str) -> str:
        """
        Wrap a sequence of mutations in a safety net. steps is a JSON array of
        {"tool": "...", "arguments": {...}} executed in order. If ANY step
        fails, the set is automatically rolled back to the pre-experiment
        snapshot and the failure is reported. On full success the checkpoint
        is kept so you can still inspect or restore it.

        Example: safe_experiment("test-fader-ride", '[{"tool":
        "set_track_volume", "arguments": {"track_index": 0, "value": 0.9}}]')
        """
        try:
            parsed = json.loads(steps)
        except (ValueError, TypeError):
            raise ValueError("steps must be a JSON array of "
                             "{\"tool\", \"arguments\"} objects")
        if not isinstance(parsed, list) or not parsed:
            raise ValueError("steps must be a non-empty JSON array")
        for s in parsed:
            if not isinstance(s, dict) or "tool" not in s:
                raise ValueError(
                    "each step needs at least a \"tool\" key; got: " + str(s)[:80])

        ableton = get_ableton_connection()
        snapshot = store.capture_snapshot(ableton)
        store.store_named("safe_experiment:" + name, snapshot)

        executed, failed = [], None
        for step in parsed:
            tool_name = step["tool"]
            args = step.get("arguments", {}) or {}
            try:
                result = ableton.send_command(tool_name, args)
                executed.append({"tool": tool_name, "args": args,
                                 "ok": result.get("status") == "success",
                                 "message": str(result.get("message", ""))[:150]})
                if result.get("status") != "success":
                    failed = {"tool": tool_name, "args": args,
                              "message": str(result.get("message", ""))[:200]}
                    break
            except Exception as e:
                executed.append({"tool": tool_name, "args": args, "ok": False,
                                 "message": str(e)[:150]})
                failed = {"tool": tool_name, "args": args, "message": str(e)[:200]}
                break

        response: Dict[str, Any] = {"experiment": name,
                                    "steps_executed": len(executed),
                                    "steps": executed}
        if failed is not None:
            rollback_report = store.restore(ableton, snapshot)
            response.update({"status": "rolled_back",
                             "failed_step": failed,
                             "rollback": rollback_report})
        else:
            response.update({"status": "completed",
                             "checkpoint": "safe_experiment:" + name})
        return json.dumps(response, default=str)
