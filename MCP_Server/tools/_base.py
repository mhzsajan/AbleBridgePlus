"""Shared tool infrastructure: decorators, helpers, error formatting."""
import asyncio
import functools
import json
import logging

logger = logging.getLogger("AbletonBridge")

# Limits concurrent tool executions that use the Ableton TCP connection.
# Set to 1 because the TCP protocol is strictly request-response on a single socket.
# This prevents thread pool exhaustion and ensures orderly command dispatch.
_ableton_semaphore = asyncio.Semaphore(1)

# Absolute timeout for any single tool call (prevents a stuck tool from
# blocking the semaphore indefinitely).
_TOOL_TIMEOUT_SECONDS = 120.0


# Change-journal classification: tool names that mutate the set.
_MUTATION_PREFIXES = (
    "set_", "create_", "add_", "delete_", "remove_", "move_", "rename_",
    "duplicate_", "apply_", "freeze_", "unfreeze_", "fire_", "launch_",
    "quantize_", "generate_", "build_", "produce_", "convert_",
    "transpose_", "slice_", "consolidate_", "clear_", "swap_", "copy_",
)
_MUTATION_EXACT = {
    "start_show_autopilot", "stop_show_autopilot", "smart_freeze",
    "audio_clip_to_midi", "hum_to_clip", "restore_checkpoint",
    "match_reference_track", "record_clip", "start_recording",
    "stop_playback", "start_playback", "tap_tempo", "undo", "redo",
    "capture_and_insert_scene", "emergency_stop", "panic_mute",
    "remember_preference", "forget_preference", "clear_change_journal",
}


def _tool_handler(error_prefix: str):
    """Decorator that wraps tool functions with standard error handling.

    Runs the synchronous tool function in a thread pool via asyncio.to_thread()
    so it doesn't block the FastMCP async event loop during TCP/UDP I/O.

    An asyncio.Semaphore gates entry so that only one tool occupies the thread
    pool (and the shared TCP socket) at a time. An outer timeout ensures a
    stuck tool releases the semaphore after _TOOL_TIMEOUT_SECONDS.

    All plain-string returns are wrapped in tool_success() for consistent JSON
    envelope. Returns that are already JSON (start with '{' or '[') pass through.

    Catches ValueError -> tool_error("Invalid input: ..."),
    ConnectionError -> tool_error("M4L bridge not available: ..."),
    Exception -> tool_error("Error {prefix}: ...")
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Change-journal hook: mutating tools get recorded (best-effort,
            # never on the hot path's failure domain).
            journal_tool = None
            if func.__name__.startswith(_MUTATION_PREFIXES) or func.__name__ in _MUTATION_EXACT:
                journal_tool = func.__name__
            try:
                async with _ableton_semaphore:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(func, *args, **kwargs),
                        timeout=_TOOL_TIMEOUT_SECONDS,
                    )
                if journal_tool:
                    from MCP_Server.tools.studio_memory import journal_append
                    args_summary = json.dumps(
                        [a for a in args[1:] if not hasattr(a, "report_progress")],
                        default=str) if len(args) > 1 else ""
                    status = "ok"
                    try:
                        parsed = json.loads(result) if isinstance(result, str) else {}
                        status = parsed.get("status", "ok")
                    except (json.JSONDecodeError, TypeError, AttributeError):
                        pass
                    journal_append(journal_tool, args_summary, status)
                if isinstance(result, str):
                    stripped = result.strip()
                    if stripped.startswith(("{", "[")):
                        return result  # already structured JSON
                    return tool_success(result)
                return result
            except asyncio.TimeoutError:
                logger.error("Tool timed out after %ds: %s", _TOOL_TIMEOUT_SECONDS, error_prefix)
                return tool_error(f"Tool timed out after {_TOOL_TIMEOUT_SECONDS}s: {error_prefix}")
            except ValueError as e:
                return tool_error(f"Invalid input: {e}")
            except ConnectionError as e:
                return tool_error(f"M4L bridge not available: {e}")
            except Exception as e:
                logger.error("Error %s: %s", error_prefix, e)
                return tool_error(f"Error {error_prefix}: {e}")
        return wrapper
    return decorator


def _m4l_result(result: dict) -> dict:
    """Extract result data from M4L response, or raise on error."""
    if result.get("status") == "success":
        return result.get("result", {})
    msg = result.get("message", "Unknown error")
    raise Exception(f"M4L bridge error: {msg}")


def tool_success(message: str, data: dict = None) -> str:
    """Create a standardized success response."""
    result = {"status": "ok", "message": message}
    if data:
        result["data"] = data
    return json.dumps(result)


def tool_error(message: str) -> str:
    """Create a standardized error response."""
    return json.dumps({"status": "error", "message": message})


def _report_progress(ctx, current: float, total: float, message: str = None):
    """Report progress from a sync tool thread.

    ctx.report_progress() is async, but tools run in asyncio.to_thread().
    This helper bridges the gap by scheduling the coroutine on the event loop.
    Fails silently if the event loop is unavailable.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                ctx.report_progress(current, total, message), loop
            )
    except Exception:
        pass  # progress is best-effort
