"""
Studio Memory for AbleBridge++.

Two halves:

- Preferences (taste): persistent key/value store in ~/.ablebridge/memory.json
  — "I like 124 BPM", "sidechain the bass 4 dB", "my go-to 909 kit is in
  folder X". recall_preferences() also injects memory-derived suggestions
  (tempo/key/genre defaults) so new sessions start personalized.
- Change journal (accountability): the central _tool_handler hook appends
  every *mutating* tool call (create/set/delete/... prefixed) to a rolling
  JSONL at ~/.ablebridge/journal.jsonl, so "what did the AI change last
  session?" always has an answer. get_change_journal / clear_change_journal
  expose it.
"""
import json
import logging
import os
import threading
import time
from typing import Any, Dict, List

from mcp.server.fastmcp import Context

from MCP_Server.tools._base import _tool_handler
from MCP_Server.connections.ableton import get_ableton_connection

logger = logging.getLogger("MCP_Server.studio_memory")

JOURNAL_MUTATION_PREFIXES = (
    "set_", "create_", "add_", "delete_", "remove_", "move_", "rename_",
    "duplicate_", "start_", "stop_", "apply_", "freeze_", "unfreeze_",
    "fire_", "launch_", "quantize_", "generate_", "build_", "produce_",
    "convert_", "import_", "assign_", "record_", "capture_", "transpose_",
    "slice_", "consolidate_", "delete_", "clear_", "swap_", "copy_",
    "audio_clip_to_midi", "hum_to_clip", "smart_freeze",
)

_lock = threading.Lock()


def _memory_dir():
    return os.path.join(os.path.expanduser("~"), ".ablebridge")


def _memory_path():
    return os.path.join(_memory_dir(), "memory.json")


def _journal_path():
    return os.path.join(_memory_dir(), "journal.jsonl")


def load_memory() -> Dict[str, Any]:
    try:
        with open(_memory_path(), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"preferences": {}, "updated": None}


def save_memory(mem: Dict[str, Any]) -> None:
    os.makedirs(_memory_dir(), exist_ok=True)
    mem["updated"] = time.time()
    tmp = _memory_path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2)
    os.replace(tmp, _memory_path())


def journal_append(tool_name: str, args_summary: str, status: str) -> None:
    """Called by _tool_handler for mutating tools. Rolling cap ~1000 entries."""
    try:
        os.makedirs(_memory_dir(), exist_ok=True)
        entry = json.dumps({"ts": round(time.time(), 2), "tool": tool_name,
                            "args": args_summary[:300], "status": status})
        with _lock:
            path = _journal_path()
            try:
                size = os.path.getsize(path)
            except OSError:
                size = 0
            with open(path, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
            if size > 400_000:  # ~1000+ entries; trim to the last 500 lines
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()[-500:]
                tmp = path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                os.replace(tmp, path)
    except Exception as e:
        logger.debug("journal append failed: %s", e)


def register_tools(mcp):

    @mcp.tool()
    @_tool_handler("remembering a preference")
    def remember_preference(ctx: Context, key: str, value: str) -> str:
        """
        Store a studio preference permanently (survives restarts): tempo,
        favorite key, genre defaults, mixing taste, folder locations...
        e.g. remember_preference('default_tempo', '124'),
             remember_preference('mixing_style', 'tight sidechain, wide pads').
        recall_preferences() brings them all back in later sessions.
        """
        key = str(key).strip()
        if not key:
            raise ValueError("key is required")
        mem = load_memory()
        mem.setdefault("preferences", {})[key] = str(value)
        save_memory(mem)
        return json.dumps({"status": "ok", "key": key, "value": str(value),
                           "total_preferences": len(mem["preferences"])})

    @mcp.tool()
    @_tool_handler("recalling preferences")
    def recall_preferences(ctx: Context) -> str:
        """
        Recall all stored studio preferences plus session-start suggestions
        derived from them (default tempo/key/genre). Call this at the start
        of a session to work with the user's taste instead of guessing.
        """
        mem = load_memory()
        prefs = mem.get("preferences", {})
        suggestions: Dict[str, Any] = {}
        tempo = prefs.get("default_tempo")
        if tempo:
            try:
                suggestions["tempo"] = float(str(tempo).strip())
            except ValueError:
                pass
        for k in ("default_key", "favorite_key", "key"):
            if prefs.get(k):
                suggestions["key"] = prefs[k]
                break
        for k in ("default_genre", "favorite_genre", "genre"):
            if prefs.get(k):
                suggestions["genre"] = prefs[k]
                break
        return json.dumps({"status": "ok",
                           "preferences": prefs,
                           "count": len(prefs),
                           "session_suggestions": suggestions,
                           "note": "apply with set_tempo / build tools as needed"})

    @mcp.tool()
    @_tool_handler("forgetting a preference")
    def forget_preference(ctx: Context, key: str) -> str:
        """Delete a stored preference by key."""
        mem = load_memory()
        prefs = mem.setdefault("preferences", {})
        if str(key) not in prefs:
            return json.dumps({"status": "ok", "removed": None,
                               "message": "no preference named '{0}'".format(key)})
        removed = prefs.pop(str(key))
        save_memory(mem)
        return json.dumps({"status": "ok", "removed": {str(key): removed},
                           "remaining": len(prefs)})

    @mcp.tool()
    @_tool_handler("reading the change journal")
    def get_change_journal(ctx: Context, last_n: int = 30) -> str:
        """
        What has the AI (or any MCP client) changed in Live? Returns the
        last N mutating tool calls (tool name, args, result status, time)
        from the rolling journal at ~/.ablebridge/journal.jsonl.
        Pairs with checkpoints: diff what changed since 'before-overhaul'.
        """
        entries: List[Dict[str, Any]] = []
        try:
            with open(_journal_path(), encoding="utf-8", errors="replace") as f:
                for line in f.readlines()[-max(1, int(last_n)):]:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        return json.dumps({"status": "ok", "entries": entries,
                           "shown": len(entries),
                           "journal_path": _journal_path()})

    @mcp.tool()
    @_tool_handler("clearing the change journal")
    def clear_change_journal(ctx: Context) -> str:
        """Erase the change journal (fresh start). Preferences are kept."""
        try:
            os.remove(_journal_path())
            return json.dumps({"status": "ok", "cleared": True})
        except FileNotFoundError:
            return json.dumps({"status": "ok", "cleared": True,
                               "message": "journal was already empty"})
