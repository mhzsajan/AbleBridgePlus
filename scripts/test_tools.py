"""Systematically test every registered tool against the live Ableton connection.

Usage:
    uv run python scripts/test_tools.py [--quick] [--write]

--quick   skip slow tools (browser cache scan, big reads)
--write   allow safe write operations (tempo, volume, mute, fire clip)

Results are printed and written to /tmp/tool_test_report.txt
"""

import asyncio
import inspect
import json
import sys
import time
from typing import Any, Dict, List, Optional

sys.path.insert(0, '.')

from MCP_Server.server import MCPServer

# Tools that require a running Max for Live bridge device; skipped in sweeps
try:
    from scripts._m4l_skip import M4L_ONLY
except ImportError:
    M4L_ONLY = set()

# Tools that are risky in a live session (create/delete/duplicate/etc.)
DESTRUCTIVE = {
    'delete_track', 'delete_clip', 'delete_scene', 'delete_device',
    'delete_return_track', 'duplicate_track', 'duplicate_clip',
    'duplicate_scene', 'duplicate_clip_loop', 'duplicate_clip_region',
    'create_midi_track', 'create_audio_track', 'create_clip',
    'create_return_track', 'create_scene', 'group_tracks',
    'freeze_track', 'unfreeze_track', 'audio_to_midi',
    'sliced_simpler_to_drum_rack', 'create_midi_track_with_simpler',
    'delete_time', 'duplicate_time', 'insert_silence',
    'delete_backup', 'restore_session', 'delete_snapshot',
    'delete_all_snapshots', 'delete_macro', 'delete_scene_macro',
    'delete_live_preset', 'delete_mix_preset', 'delete_lighting_scene',
    'clear_clip_notes', 'clear_clip_automation', 'clear_track_automation',
    'remove_notes_range', 'crop_clip', 'reverse_clip', 'capture_midi',
    'stop_playback', 'stop_arrangement_recording', 'emergency_stop',
    'panic_mute', 'panic_unmute', 'activate_backup_scene',
    'fire_scene', 'fire_clip', 'stop_clip', 'fire_scene_as_selected',
    'load_instrument_or_effect', 'load_sample', 'load_drum_kit',
    'set_next_song', 'play_cued_song', 'jump_to_next_song',
    'start_arrangement_recording', 'trigger_session_record',
    'set_song_time', 'set_playback_position', 'move_clip_playing_pos',
    'undo', 'redo', 'save_snapshot', 'snapshot_all_devices',
    'morph_between_snapshots', 'restore_group_snapshot',
    'backup_session', 'save_backup_preset', 'load_backup_preset',
    'save_lighting_scene', 'save_audio_preset', 'save_video_preset',
    'save_effect_chain', 'load_effect_chain', 'save_chain_template',
    'apply_effect_chain', 'generate_midi', 'generate_preset',
    'save_scene_macro', 'create_scene_macro', 'save_macro_controller',
    'assign_cc_channel', 'set_plugin_parameter_cc', 'send_raw_cc',
    'set_dmx_channel', 'configure_spout', 'play_video_clip',
    'delete_video_clip', 'create_video_clip',
}

# Hand-crafted safe arguments per tool (must be non-destructive)
SAFE_ARGS: Dict[str, Dict[str, Any]] = {
    'get_track_info': {'track_index': 0},
    'get_track_by_name': {'name': '1-MIDI'},
    'get_all_tracks_info': {},
    'get_return_tracks_info': {},
    'get_master_track_info': {},
    'get_track_routing': {'track_index': 0},
    'get_track_clips': {'track_index': 0},
    'get_clip_info': {'track_index': 0, 'clip_index': 0},
    'get_tracks_with_clips': {},
    'get_track_volume': {'track_index': 0},
    'get_track_pan': {'track_index': 0},
    'get_track_mute': {'track_index': 0},
    'get_track_solo': {'track_index': 0},
    'get_track_sends': {'track_index': 0},
    'get_track_devices': {'track_index': 0},
    'get_device_parameters': {'track_index': 0, 'device_index': 0},
    'get_device_parameter': {'track_index': 0, 'device_index': 0, 'parameter_index': 0},
    'get_device_info': {'track_index': 0, 'device_index': 0},
    'get_scene_info': {'scene_index': 0},
    'get_scenes': {},
    'get_scene_names': {},
    'get_session_info': {},
    'get_song_info': {},
    'get_tempo': {},
    'get_time_signature': {},
    'get_playback_state': {},
    'get_current_time': {},
    'get_is_playing': {},
    'get_is_recording': {},
    'get_metronome': {},
    'get_loop': {},
    'get_arrangement_clips': {'track_index': 0},
    'get_automation_lanes': {'track_index': 0},
    'get_browser_tree': {'category_type': 'all'},
    'search_browser': {'query': 'kick'},
    'get_browser_items_at_path': {'path': 'instruments'},
    'get_show_time': {},
    'get_show_status': {},
    'get_song_timings': {},
    'get_session_stats': {},
    'get_track_stats': {'track_index': 0},
    'get_cpu_usage': {},
    'get_memory_usage': {},
    'get_peak_levels': {},
    'get_plugin_presets': {'track_index': 0, 'device_index': 0},
    'get_latency': {},
    'get_audio_interfaces': {},
    'get_cue_volume': {},
    'get_crossfader': {},
    'get_emergency_status': {},
    'get_backup_status': {},
    'list_backups': {},
    'list_snapshots': {},
    'get_snapshot_details': {'snapshot_id': 'x'},
    'list_scene_macros': {},
    'list_macros': {},
    'list_live_presets': {},
    'list_mix_presets': {},
    'list_lighting_presets': {},
    'list_video_presets': {},
    'get_lighting_presets': {},
    'get_video_presets_list': {},
    'get_device_presets': {},
    'list_instrument_rack_presets': {},
    'get_cc_map': {'plugin_name': 'arturia_analog_lab', 'parameter_name': 'cutoff'},
    'list_cc_maps': {},
    'get_midi_mappings': {},
    'get_highlighted_clip_slot': {},
    'get_audio_analysis': {'track_index': 0},
    'get_spectrum': {'track_index': 0},
    'get_levels': {'track_index': 0},
    'get_average_levels': {'track_index': 0},
    'analyze_dynamics_range': {'track_index': 0},
    'get_dmx_status': {},
    'get_video_tracks': {},
    'get_show_clock': {},
    'get_show_time_data': {},
    'get_performance_trends': {},
    'get_mix_history': {},
    'get_session_history': {},
    'get_cpu_history': {},
    'get_memory_history': {},
    'get_song_performance': {},
    'get_audio_effect_presets': {},
    'get_midi_effect_presets': {},
    'get_sound_design_help': {'sound_type': 'bass', 'style': 'deep'},
    'get_ai_suggestions': {'context': 'mixing'},
    'get_genre_suggestions': {'genre': 'rock', 'track_type': 'drums'},
    'get_arrangement_suggestions': {'song_structure': {'sections': ['intro', 'verse', 'chorus']}},
    'analyze_mix_quality': {'mix_data': {'tracks': 4, 'peak_db': -3.0, 'rms_db': -12.0}},
    'get_template_list': {},
    'get_chain_templates': {},
    'get_snapshots': {},
    'get_workflows': {},
    'get_available_workflows': {},
    'get_effect_chain': {'track_index': 0, 'device_index': 0},
    'get_m4l_status': {},
    'ping_m4l': {},
    'get_m4l_bridge_version': {},
    'get_project_info': {},
    'get_project_path': {},
    'get_live_version': {},
    'get_ableton_version': {},
    'get_app_version': {},
    'get_song': {},
    'get_setlist': {},
    'get_current_song': {},
    'get_next_song': {},
    'get_queued_songs': {},
    'get_show_data': {},
    'get_clock': {},
}

# Safe write tools (allowed with --write)
SAFE_WRITES = {
    'set_tempo': {'tempo': 120.0},
    'set_metronome': {'enabled': False},
    'set_cue_volume': {'value': 0.5},
    'set_track_volume': {'track_index': 0, 'value': 0.8},
    'set_track_pan': {'track_index': 0, 'value': 0.0},
    'set_track_mute': {'track_index': 0, 'mute': False},
    'set_track_solo': {'track_index': 0, 'solo': False},
    'set_master_volume': {'value': 0.8},
    'set_crossfader': {'value': 0.5},
    'set_show_tempo': {'tempo': 120},
    'start_show_clock': {'tempo': 120},
    'stop_show_clock': {},
    'start_performance_timer': {'song_name': 'test'},
    'stop_performance_timer': {'song_name': 'test'},
    'get_performance_timings': {},
    'start_song_timer': {'song_name': 'test'},
    'stop_song_timer': {},
    'set_show_status': {},
    'set_song_loop': {'enabled': False},
    'continue_playing': {},
    'set_track_name': {'track_index': 0, 'name': '1-MIDI'},
    'set_clip_name': {'track_index': 0, 'clip_index': 0, 'name': 'test-clip'},
    'set_scene_name': {'scene_index': 0, 'name': 'test-scene'},
    'refresh_browser_cache': {},
    'set_device_parameter': {'track_index': 0, 'device_index': 0, 'parameter_index': 0, 'value': 0.5},
    'set_device_enabled': {'track_index': 0, 'device_index': 0, 'enabled': True},
    'set_macro_value': {'macro_index': 0, 'value': 0.5},
    'set_panning_mode': {'track_index': 0, 'mode': 0},
    'set_split_stereo_pan': {'track_index': 0, 'value': 0.0},
    'set_crossfade_assign': {'track_index': 0, 'assign': 0},
    'set_track_delay': {'track_index': 0, 'delay': 0.0},
    'set_track_send': {'track_index': 0, 'send_index': 0, 'value': 0.0},
    'set_track_arm': {'track_index': 0, 'arm': False},
    'set_track_color': {'track_index': 0, 'color': 0},
    'set_clip_color': {'track_index': 0, 'clip_index': 0, 'color': 0},
    'set_clip_looping': {'track_index': 0, 'clip_index': 0, 'enabled': False},
    'set_clip_grid': {'track_index': 0, 'clip_index': 0, 'grid': 16},
    'set_track_monitoring': {'track_index': 0, 'mode': 0},
    'set_track_fold': {'track_index': 0, 'folded': False},
    'set_track_routing': {'track_index': 0, 'routing_type': 'input', 'source': 'Ext. In'},
    'set_groove_settings': {'groove_amount': 0.0},
    'set_show_clock': {},
    'set_warp_mode': {'track_index': 0, 'clip_index': 0, 'mode': 'beats'},
    'set_clip_warp': {'track_index': 0, 'clip_index': 0, 'enabled': False},
    'set_clip_legato': {'track_index': 0, 'clip_index': 0, 'enabled': False},
    'set_clip_launch_mode': {'track_index': 0, 'clip_index': 0, 'mode': 0},
    'set_clip_start_end': {'track_index': 0, 'clip_index': 0, 'start': 0, 'end': 4},
    'set_scene_tempo': {'scene_index': 0, 'tempo': None},
    'set_song_settings': {'tempo': 120},
    'set_loop_start': {'position': 0},
    'set_loop_end': {'position': 4},
    'set_loop_length': {'length': 4},
    'set_arrangement_overdub': {'enabled': False},
    'set_playback_position': {'position': 0},
    'set_quantization': {'value': 7},
    'set_session_record': {'enabled': False},
    'set_highlighted_clip_slot': {},
    'set_detail_clip': {'track_index': 0, 'clip_index': 0},
    'select_track': {'track_index': 0},
    'select_scene': {'scene_index': 0},
    'set_next_song': {'song_name': 'test'},
    'set_show_tempo': {'tempo': 120},
    'set_cc_map': {},
    'save_cc_map': {},
    'set_midi_mapping': {},
    'set_device_chain': {},
    'set_plugin_parameter': {'track_index': 0, 'device_index': 0, 'parameter_name': 'x', 'value': 0.5},
    'set_audio_effect_preset': {},
    'set_midi_effect_preset': {},
    'set_lighting_scene': {},
    'set_video_preset': {},
    'set_transition_preset': {},
    'set_template': {},
    'set_effect_chain': {},
    'set_snapshot': {},
    'set_macro': {},
    'set_macro_controller': {},
    'set_workflow': {},
    'set_available_workflow': {},
    'set_current_song': {},
    'set_queued_songs': {},
    'set_setlist': {},
    'set_show_data': {},
}


def build_args(tool_name: str, tool_def: Dict[str, Any], allow_write: bool) -> Optional[Dict[str, Any]]:
    """Build arguments for a tool call. Returns None if it should be skipped."""
    if tool_name in DESTRUCTIVE or tool_name in M4L_ONLY:
        return None
    if tool_name in SAFE_ARGS:
        return SAFE_ARGS[tool_name]
    if allow_write and tool_name in SAFE_WRITES:
        return SAFE_WRITES[tool_name]
    # Generic fallback from inputSchema
    schema = tool_def.get('inputSchema', {})
    props = schema.get('properties', {})
    args = {}
    for pname, pmeta in props.items():
        ptype = pmeta.get('type', 'string')
        pdesc = (pmeta.get('description') or '').lower() if isinstance(pmeta, dict) else ''
        if ptype == 'integer':
            # Validate-style params: a few known value types get real values;
            # everything else uses a safe positive index
            if 'color' in pname or 'color' in pdesc:
                args[pname] = 0
            elif any(w in pname for w in ('mode', 'quantization', 'grid')):
                args[pname] = 1
            else:
                args[pname] = 0
        elif ptype == 'number':
            # Positive values satisfy "must be > 0" validations
            if any(w in pdesc for w in ('length', 'duration', 'positive')) or pname in ('length', 'loop_end', 'end', 'grid_size', 'new_start_time'):
                args[pname] = 4.0
            else:
                args[pname] = 0.0
        elif ptype == 'boolean':
            args[pname] = False
        elif ptype == 'array':
            args[pname] = []
        elif ptype == 'object':
            args[pname] = {}
        else:
            args[pname] = ''
    return args


async def main():
    quick = '--quick' in sys.argv
    allow_write = '--write' in sys.argv
    server = MCPServer()
    tools = server.tool_registry.get_all_tools()
    print(f"Testing {len(tools)} tools against Ableton Live...")
    print(f"quick={quick} write={allow_write}")

    results: List[Dict[str, Any]] = []
    stats = {'ok': 0, 'error': 0, 'exception': 0, 'timeout': 0, 'skipped': 0, 'bug': 0}

    # --- Setup: create a test MIDI clip so clip tools exercise real content ---
    clip_track, clip_slot = 0, 0
    if allow_write:
        try:
            # Find a MIDI track dynamically (create_clip only works there)
            r = await server.handle_request({'method': 'tools/call', 'params': {
                'name': 'get_session_info', 'arguments': {}}})
            info = json.loads(r.get('content', [{}])[0].get('text', '{}'))
            midi_track = None
            for ti in range(info.get('track_count', 0)):
                rt = await server.handle_request({'method': 'tools/call', 'params': {
                    'name': 'get_track_info', 'arguments': {'track_index': ti}}})
                ti_info = json.loads(rt.get('content', [{}])[0].get('text', '{}'))
                if ti_info.get('is_midi_track'):
                    midi_track = ti
                    break
            if midi_track is None:
                rc = await server.handle_request({'method': 'tools/call', 'params': {
                    'name': 'create_midi_track', 'arguments': {'index': -1}}})
                midi_track = info.get('track_count', 0)  # appended at the end
                print(f"  setup: created MIDI track at index {midi_track} -> {rc.get('content', [{}])[0].get('text', '')[:100]}")
            clip_track = midi_track if midi_track is not None else 0
            r = await server.handle_request({'method': 'tools/call', 'params': {
                'name': 'create_clip', 'arguments': {'track_index': clip_track, 'clip_index': clip_slot, 'length': 4.0}}})
            t = r.get('content', [{}])[0].get('text', '')
            print(f"  setup: create_clip on track {clip_track} -> {t[:120]}")
            if 'error' not in t.lower():
                r2 = await server.handle_request({'method': 'tools/call', 'params': {
                    'name': 'add_notes_to_clip', 'arguments': {
                        'track_index': clip_track, 'clip_index': clip_slot,
                        'notes': [{'pitch': 60, 'start_time': 0.0, 'duration': 1.0, 'velocity': 100},
                                  {'pitch': 64, 'start_time': 1.0, 'duration': 1.0, 'velocity': 100}]}}})
                print(f"  setup: add_notes -> {r2.get('content', [{}])[0].get('text', '')[:120]}")
        except Exception as e:
            print(f"  setup: clip creation failed ({e}) — clip tools will report 'No clip in slot'")

    for i, tool_def in enumerate(tools):
        name = tool_def['name']
        args = build_args(name, tool_def, allow_write)
        if args is None:
            stats['skipped'] += 1
            continue

        req = {'method': 'tools/call', 'params': {'name': name, 'arguments': args}}
        start = time.time()
        try:
            resp = await asyncio.wait_for(server.handle_request(req), timeout=25)
            elapsed = time.time() - start
            text = resp.get('content', [{}])[0].get('text', '')
            # Try to parse the envelope
            try:
                parsed = json.loads(text) if text.startswith('{') else None
            except Exception:
                parsed = None
            status = 'ok'
            if parsed and parsed.get('status') == 'error':
                status = 'error'
            elif parsed and parsed.get('success') is False:
                status = 'error'
            elif resp.get('error'):
                status = 'exception'
            stats[status] += 1
            results.append({'tool': name, 'status': status, 'args': args, 'text': text[:400], 'elapsed': round(elapsed, 2)})
        except asyncio.TimeoutError:
            stats['timeout'] += 1
            results.append({'tool': name, 'status': 'timeout', 'args': args, 'text': '', 'elapsed': 25.0})
        except Exception as e:
            stats['exception'] += 1
            results.append({'tool': name, 'status': 'exception', 'args': args, 'text': f"{type(e).__name__}: {e}"[:400], 'elapsed': round(time.time() - start, 2)})

        if (i + 1) % 25 == 0:
            print(f"  ... {i + 1}/{len(tools)} done (ok={stats['ok']} err={stats['error']} exc={stats['exception']} timeout={stats['timeout']})")

    # Report
    lines = []
    lines.append(f"=== TOOL TEST REPORT ({len(tools)} tools) ===")
    lines.append(f"quick={quick} write={allow_write}")
    lines.append(f"OK: {stats['ok']}  ERROR(handled): {stats['error']}  EXCEPTION: {stats['exception']}  TIMEOUT: {stats['timeout']}  SKIPPED(destructive): {stats['skipped']}")
    lines.append("")
    lines.append("--- EXCEPTIONS (likely bugs) ---")
    for r in results:
        if r['status'] == 'exception':
            lines.append(f"[{r['elapsed']}s] {r['tool']} {json.dumps(r['args'])} -> {r['text'][:300]}")
    lines.append("")
    lines.append("--- TIMEOUTS ---")
    for r in results:
        if r['status'] == 'timeout':
            lines.append(f"{r['tool']} {json.dumps(r['args'])}")
    lines.append("")
    lines.append("--- HANDLED ERRORS (check if expected) ---")
    for r in results:
        if r['status'] == 'error':
            lines.append(f"{r['tool']} {json.dumps(r['args'])} -> {r['text'][:300]}")
    lines.append("")
    lines.append("--- OK (sample of 30) ---")
    oks = [r for r in results if r['status'] == 'ok']
    for r in oks[:30]:
        lines.append(f"{r['tool']} -> {r['text'][:150]}")
    if len(oks) > 30:
        lines.append(f"... and {len(oks) - 30} more OK")

    report = "\n".join(lines)
    print(report)
    import tempfile, os
    rpath = os.path.join(tempfile.gettempdir(), 'tool_test_report.txt')
    with open(rpath, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\nReport written to {rpath}")


if __name__ == '__main__':
    asyncio.run(main())