"""
Show Autopilot for AbleBridge++.

Timed, hands-free scene sequencing for live performance: fire a scene,
have the next one launch automatically after a set length in bars, with
per-scene tempo changes. Designed for backing-track/DJ-style sets where
the musician needs both hands free.

A daemon thread fires scenes; all Live interaction goes through the same
shared Ableton connection as every other tool, sequenced by the tool
semaphore, so autopilot is safe to run alongside normal tool use.
"""
import logging
import threading
import time
from typing import Any, Dict, List

from mcp.server.fastmcp import Context

from MCP_Server.tools._base import _tool_handler
from MCP_Server.connections.ableton import get_ableton_connection

logger = logging.getLogger("MCP_Server.show_autopilot")

_autopilot: Dict[str, Any] = {
    "thread": None,
    "stop_event": threading.Event(),
    "running": False,
    "sequence": [],
    "current_index": -1,
    "current_scene": None,
    "started_at": None,
    "last_error": None,
}
_lock = threading.Lock()


def _autopilot_loop(stop_event: threading.Event, steps: List[Dict[str, Any]],
                    loops: int):
    """Fire each step's scene, hold for its bars, advance. Never touches
    state without the lock; only reads settings mid-loop."""
    round_number = 0
    try:
        while not stop_event.is_set():
            for i, step in enumerate(steps):
                if stop_event.is_set():
                    return
                with _lock:
                    _autopilot["current_index"] = i
                    _autopilot["current_scene"] = step.get("scene_index")

                ableton = get_ableton_connection()
                ableton.send_command("fire_scene",
                                     {"scene_index": step["scene_index"]})
                if step.get("tempo"):
                    try:
                        ableton.send_command("set_tempo",
                                             {"tempo": float(step["tempo"])})
                    except Exception:
                        pass

                bars = max(0.25, float(step.get("bars", 8)))
                # Read live tempo each step so manual tempo rides are honored.
                try:
                    tempo = float(ableton.send_command(
                        "get_session_info").get("tempo", 120.0))
                except Exception:
                    tempo = 120.0
                hold_seconds = bars * 4.0 * (60.0 / tempo)

                deadline = time.time() + hold_seconds
                while time.time() < deadline and not stop_event.is_set():
                    time.sleep(min(0.25, max(0.05, deadline - time.time())))
            round_number += 1
            if loops and round_number >= loops:
                return
    except Exception as e:
        logger.exception("autopilot loop error")
        with _lock:
            _autopilot["last_error"] = str(e)
    finally:
        with _lock:
            _autopilot["running"] = False
            _autopilot["thread"] = None


def register_tools(mcp):

    @mcp.tool()
    @_tool_handler("starting autopilot")
    def start_show_autopilot(ctx: Context, sequence: str, loops: int = 1) -> str:
        """
        Hands-free scene sequencer for live shows. sequence is JSON:
        [{"scene_index":0,"bars":16,"tempo":124},
         {"scene_index":1,"bars":32},
         {"scene_index":2,"bars":8,"tempo":128}]
        Fires scene 0, waits `bars` bars (bar length follows the live
        tempo, so manual tempo rides stay in time), fires the next, and
        loops the whole sequence `loops` times (loops=0 means forever).
        Use stop_show_autopilot to end early; autopilot_status to peek.
        """
        import json as _json
        try:
            steps = _json.loads(sequence)
        except _json.JSONDecodeError as e:
            # NB: do not .format() a message containing a JSON example —
            # the literal braces are parsed as replacement fields.
            raise ValueError("sequence must be JSON like "
                             '[{"scene_index":0,"bars":16,"tempo":124}] — '
                             + str(e))
        if not steps or len(steps) > 64:
            raise ValueError("sequence must contain 1-64 steps")
        for s in steps:
            if "scene_index" not in s:
                raise ValueError("every step needs scene_index")

        with _lock:
            if _autopilot["running"]:
                raise RuntimeError("Autopilot already running — call "
                                   "stop_show_autopilot first.")
            _autopilot["stop_event"] = threading.Event()
            _autopilot["sequence"] = steps
            _autopilot["running"] = True
            _autopilot["started_at"] = time.time()
            _autopilot["last_error"] = None
            thread = threading.Thread(
                target=_autopilot_loop,
                args=(_autopilot["stop_event"], steps, max(0, int(loops))),
                daemon=True)
            _autopilot["thread"] = thread
        thread.start()
        return _json.dumps({"status": "autopilot_started",
                            "steps": len(steps), "loops": loops})

    @mcp.tool()
    @_tool_handler("stopping autopilot")
    def stop_show_autopilot(ctx: Context) -> str:
        """
        Stop the running show autopilot gracefully (lets the current clip
        keep playing — it only stops the automatic advancing).
        """
        with _lock:
            _autopilot["stop_event"].set()
            running = _autopilot["running"]
        return _json_status("autopilot_stopped" if running
                            else "autopilot_not_running")

    @mcp.tool()
    @_tool_handler("checking autopilot status")
    def autopilot_status(ctx: Context) -> str:
        """
        Current autopilot state: running or not, which sequence step and
        scene is live, when it started, and any error from the loop.
        """
        with _lock:
            running = _autopilot["running"]
            idx = _autopilot["current_index"]
            scene = _autopilot["current_scene"]
            started = _autopilot["started_at"]
            err = _autopilot["last_error"]
            steps = len(_autopilot["sequence"])
        import json as _json
        return _json.dumps({
            "running": running, "steps": steps,
            "current_step": idx, "current_scene": scene,
            "elapsed_seconds": round(time.time() - started, 1)
            if started else None,
            "last_error": err,
        })


def _json_status(status: str) -> str:
    import json as _json
    return _json.dumps({"status": status})
