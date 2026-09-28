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

# Absolute timeout for how long a tool call may BLOCK THE CALLER. It is not a
# kill switch: asyncio cannot cancel a thread that is already running, so on
# timeout the caller is told immediately while the semaphore stays held until
# the abandoned worker actually finishes (see _tool_handler).
_TOOL_TIMEOUT_SECONDS = 120.0

# Event loop reference, captured by the active wrapper so _report_progress can
# schedule coroutines from a worker thread. asyncio.get_event_loop() raises in
# a non-loop thread, which is why progress reporting used to be dead code.
_loop_ref = None


# ---------------------------------------------------------------------------
# Change-journal / auto-checkpoint classification
# ---------------------------------------------------------------------------

# Structural mutations: journaled AND auto-checkpointed before they run.
# The prefix list covers the bulk of it; the exact list catches the tools whose
# names do not start with a mutation verb.
_MUTATION_PREFIXES = (
    "set_", "create_", "add_", "delete_", "remove_", "move_", "rename_",
    "duplicate_", "apply_", "freeze_", "unfreeze_", "fire_", "launch_",
    "quantize_", "generate_", "build_", "produce_", "convert_",
    "transpose_", "slice_", "consolidate_", "clear_", "swap_", "copy_",
)
_MUTATION_EXACT = {
    # transport / show
    "start_show_autopilot", "stop_show_autopilot", "smart_freeze",
    "audio_clip_to_midi", "hum_to_clip", "record_clip", "start_recording",
    "tap_tempo", "undo", "redo",
    "capture_and_insert_scene",
    # emergency (these now really do drive Ableton)
    "emergency_stop", "panic_mute", "panic_unmute", "activate_backup_scene",
    # device / instrument loading — inserts devices and return tracks
    "load_instrument_or_effect", "load_sample", "load_drum_kit",
    "load_effect_chain", "setup_send_return", "batch_set_mixer",
    "apply_effect_chain", "group_tracks",
    # destructive clip edits
    "crop_clip", "reverse_clip", "insert_silence", "modify_clip_notes",
    "capture_midi", "re_enable_automation", "nudge_tempo",
    # note-level rewrites (delete-then-recreate inside the clip)
    "humanize_notes", "transform_notes", "randomize_clip_notes",
    "stutter_effect", "scale_constrained_generate",
    "batch_set_follow_actions", "euclidean_rhythm", "harmonize_melody",
    # M4L structural device edits
    "rack_insert_chain_m4l", "chain_insert_device_m4l", "rack_store_variation",
    "restore_group_snapshot", "device_ab_compare",
    # studio memory
    "remember_preference", "forget_preference", "clear_change_journal",
}

# Mutations that must appear in the change journal but do NOT justify a
# full pre-mutation snapshot: a snapshot costs 1 + N + 2 round trips, so
# arming a track or stopping a clip should not pay that on every call.
_JOURNAL_ONLY = {
    "arm_track", "disarm_track", "start_arrangement_recording",
    "stop_arrangement_recording", "trigger_session_record", "stop_clip",
    "set_groove_properties", "analyze_cross_track_audio",
    "preview_browser_item", "program_song_video_automation", "video_failover",
    "rack_recall_variation", "undo", "redo", "tap_tempo",
}

# Tools that mutate server state (or are restores/undo themselves) rather
# than the set shape — auto-checkpointing before them adds no safety.
_NO_AUTO_CHECKPOINT = {
    "undo", "redo", "rollback", "restore_checkpoint", "safe_experiment",
    "remember_preference", "forget_preference", "clear_change_journal",
    "start_show_autopilot", "stop_show_autopilot", "tap_tempo",
}


def _is_structural_mutation(name: str) -> bool:
    # An explicit opt-out wins over the prefix list: without this check,
    # _JOURNAL_ONLY entries whose names begin with a mutation verb (e.g.
    # set_groove_properties) would still be checkpointed, making that list a
    # silent no-op.
    if name in _JOURNAL_ONLY:
        return False
    return name.startswith(_MUTATION_PREFIXES) or name in _MUTATION_EXACT


def _is_mutation(name: str) -> bool:
    return _is_structural_mutation(name) or name in _JOURNAL_ONLY


def _get_live_connection():
    """Return the shared live Ableton connection if one is established.

    Returns None when no connection exists yet (replay tests, CI, first call
    not yet made) so auto-checkpointing stays a no-op outside live sessions.
    """
    try:
        import MCP_Server.state as _state
        conn = getattr(_state, "ableton_connection", None)
        if conn is not None and getattr(conn, "sock", None) is not None:
            return conn
    except Exception:
        pass
    return None


def _args_summary(args, kwargs) -> str:
    """Serialise a tool call's arguments for the change journal / checkpoints.

    The dispatcher invokes tools as ``tool_func(**call_args)``, so positional
    ``args`` is normally empty and the previous ``args[1:]`` slice always
    produced an empty string — the journal recorded no arguments at all.
    """
    payload: dict = {}
    for key, value in kwargs.items():
        if key == "ctx":
            continue
        payload[key] = value
    for i, value in enumerate(args):
        if hasattr(value, "report_progress"):
            continue
        payload["arg{0}".format(i)] = value
    if not payload:
        return ""
    try:
        return json.dumps(payload, default=str)
    except (TypeError, ValueError):
        return str(payload)[:200]


def _tool_handler(error_prefix: str):
    """Decorator that wraps tool functions with standard error handling.

    Runs the synchronous tool function in a thread pool via asyncio.to_thread()
    so it doesn't block the async event loop during TCP/UDP I/O.

    An asyncio.Semaphore gates entry so that only one tool occupies the thread
    pool (and the shared TCP socket) at a time. The timeout bounds how long the
    CALLER waits; because a running thread cannot be cancelled, the semaphore
    is handed over to a done-callback and released only once the abandoned
    worker has really stopped touching Ableton.

    All plain-string returns are wrapped in tool_success() for consistent JSON
    envelope. Returns that are already JSON (start with '{' or '[') pass through.

    Catches ValueError -> tool_error("Invalid input: ..."),
    ConnectionError -> tool_error("M4L bridge not available: ..."),
    Exception -> tool_error("Error {prefix}: ...")
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            global _loop_ref
            try:
                _loop_ref = asyncio.get_running_loop()
            except RuntimeError:
                pass

            journal_tool = func.__name__ if _is_mutation(func.__name__) else None
            checkpoint = (_is_structural_mutation(func.__name__)
                          and func.__name__ not in _NO_AUTO_CHECKPOINT)

            await _ableton_semaphore.acquire()
            # Set while this wrapper still owns the semaphore. Handed to the
            # done-callback on timeout so it is released exactly once, and
            # only after the worker is genuinely finished.
            worker: "asyncio.Future | None" = None
            try:
                # Auto-checkpoint INSIDE the gate. Capturing before acquiring
                # it could snapshot a set while another tool's multi-command
                # mutation was only half applied, making the restore point a
                # state that never actually existed.
                if checkpoint:
                    try:
                        conn = _get_live_connection()
                        if conn is not None:
                            from MCP_Server import checkpoints as _ckpt
                            _ckpt.store_auto(
                                _ckpt.capture_snapshot(conn),
                                func.__name__, _args_summary(args, kwargs))
                    except Exception:
                        logger.debug("auto-checkpoint capture failed for %s",
                                     func.__name__, exc_info=True)

                worker = asyncio.ensure_future(
                    asyncio.to_thread(func, *args, **kwargs))
                try:
                    result = await asyncio.wait_for(
                        asyncio.shield(worker),
                        timeout=_TOOL_TIMEOUT_SECONDS,
                    )
                except asyncio.TimeoutError:
                    logger.error("Tool timed out after %ds: %s",
                                 _TOOL_TIMEOUT_SECONDS, error_prefix)
                    # shield() means the inner task survives the timeout.
                    # Ownership of the semaphore passes to the callback so the
                    # next tool cannot start on the same socket while this one
                    # is still writing to Ableton.
                    worker.add_done_callback(
                        lambda _f: _ableton_semaphore.release())
                    worker = None
                    return tool_error(
                        "Tool timed out after {0}s: {1}. The call is still "
                        "running in the background and may still change your "
                        "set — do NOT retry until it settles.".format(
                            _TOOL_TIMEOUT_SECONDS, error_prefix))

                if journal_tool:
                    from MCP_Server.tools.studio_memory import journal_append
                    status = "ok"
                    try:
                        parsed = json.loads(result) if isinstance(result, str) else {}
                        status = parsed.get("status", "ok")
                    except (json.JSONDecodeError, TypeError, AttributeError):
                        pass
                    journal_append(journal_tool, _args_summary(args, kwargs),
                                   status)

                if isinstance(result, str):
                    stripped = result.strip()
                    if stripped.startswith(("{", "[")):
                        return result  # already structured JSON
                    return tool_success(result)
                return result
            except ValueError as e:
                return tool_error(f"Invalid input: {e}")
            except ConnectionError as e:
                return tool_error(f"M4L bridge not available: {e}")
            except Exception as e:
                logger.error("Error %s: %s", error_prefix, e)
                return tool_error(f"Error {error_prefix}: {e}")
            finally:
                # Runs on every path except the timeout hand-off above, where
                # ownership of the semaphore was transferred to the callback.
                if worker is not None:
                    _ableton_semaphore.release()
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
    This helper bridges the gap by scheduling the coroutine on the event loop
    captured by the active tool wrapper. asyncio.get_event_loop() raises inside
    a worker thread, so the loop is held in a module global instead.
    """
    loop = _loop_ref
    if loop is None or loop.is_closed():
        return
    try:
        asyncio.run_coroutine_threadsafe(
            ctx.report_progress(current, total, message), loop)
    except Exception:
        pass  # progress is best-effort
