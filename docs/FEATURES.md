# AbleBridgePlus — Complete Feature & Tool Reference

**475 tools** available to your AI client, grouped by what they do. Everything below is callable through chat - e.g. *"run the doctor"* or *"build a song skeleton in F# minor"*.

> Generated from the server's live `tools/list` output (v0.5.0). Names are the exact tool identifiers your AI sees. Regenerate with `python scripts/gen_features.py`.

## Contents

- [Session, Transport & Global](#session-transport-and-global) — 53
- [Tracks](#tracks) — 52
- [Clips — Session & MIDI](#clips-—-session-and-midi) — 41
- [Clips — Warp, Loop & Playback](#clips-—-warp-loop-and-playback) — 35
- [Arrangement View](#arrangement-view) — 23
- [Automation](#automation) — 13
- [Devices & Parameters](#devices-and-parameters) — 15
- [Max for Live Bridge (optional)](#max-for-live-bridge-optional) — 10
- [Mixer](#mixer) — 9
- [Browser, Search & Plugins](#browser-search-and-plugins) — 16
- [Creative & Generative](#creative-and-generative) — 24
- [AI Music Toolkit](#ai-music-toolkit) — 5
- [Audio Intelligence](#audio-intelligence) — 6
- [Producer Pipeline](#producer-pipeline) — 2
- [Project Context & Checkpoints](#project-context-and-checkpoints) — 4
- [Studio Memory](#studio-memory) — 5
- [Doctor & Performance Monitoring](#doctor-and-performance-monitoring) — 15
- [Snapshots](#snapshots) — 12
- [Scenes](#scenes) — 19
- [Live Show Control & Backups](#live-show-control-and-backups) — 13
- [Setlist & Show Clock](#setlist-and-show-clock) — 15
- [Show Autopilot](#show-autopilot) — 3
- [Video & Lighting](#video-and-lighting) — 16
- [Presets & Templates](#presets-and-templates) — 31
- [MIDI Controllers & Mapping](#midi-controllers-and-mapping) — 12

---

## Session, Transport & Global (53)

*Everything about the set itself: tempo, transport, loop, scale, metronome, recording, undo, Link.*

`get_session_info` | `get_song_info` | `get_song_transport` | `get_song_length` | `get_song_data` | `set_song_data` | `get_song_settings` | `set_song_settings` | `get_song_scale` | `set_song_scale` | `get_all_scales` | `detect_scale` | `detect_chord` | `set_tempo` | `nudge_tempo` | `tap_tempo` | `start_playback` | `stop_playback` | `continue_playing` | `set_song_time` | `set_playback_position` | `navigate_playback` | `set_song_loop` | `get_loop_info` | `set_metronome` | `set_session_record` | `trigger_session_record` | `get_recording_status` | `set_arrangement_overdub` | `start_arrangement_recording` | `stop_arrangement_recording` | `set_punch_recording` | `undo` | `redo` | `end_undo_step` | `re_enable_automation` | `get_ableton_version` | `get_server_capabilities` | `get_full_session_state` | `get_song_file_path` | `get_song_timings` | `get_beat_time` | `get_property_changes` | `get_count_in_duration` | `set_draw_mode` | `set_follow_song` | `zoom_scroll_view` | `set_view` | `get_view_state` | `get_selection_state` | `get_link_status` | `set_link_enabled` | `get_current_song`

## Tracks (52)

*Create, organize, route, freeze and inspect tracks — including sidechain and sends setup.*

`create_midi_track` | `create_audio_track` | `create_return_track` | `create_instrument_track` | `create_drum_track` | `delete_track` | `duplicate_track` | `group_tracks` | `get_track_info` | `get_all_tracks_info` | `get_return_tracks` | `get_return_tracks_info` | `get_return_track_info` | `get_master_track_info` | `set_track_name` | `set_track_color` | `set_track_arm` | `arm_track` | `disarm_track` | `set_implicit_arm` | `set_track_monitoring` | `set_track_routing` | `get_track_routing` | `delete_return_track` | `freeze_track` | `unfreeze_track` | `smart_freeze` | `set_track_fold` | `set_track_collapse` | `select_track` | `set_track_delay` | `get_track_delay` | `get_track_data` | `set_track_data` | `set_track_send` | `setup_send_return` | `set_sidechain_routing` | `get_routing_presets_list` | `load_routing_preset` | `save_routing_preset` | `get_track_meters` | `get_track_spectrum` | `get_peak_levels` | `get_audio_levels` | `get_take_lanes` | `create_take_lane` | `get_take_lanes_m4l` | `get_split_stereo` | `set_split_stereo` | `set_split_stereo_pan` | `set_panning_mode` | `set_cue_volume`

## Clips — Session & MIDI (41)

*Read and write MIDI notes, quantize/humanize/transpose, manage clip properties.*

`create_clip` | `create_clip_with_notes` | `add_notes_to_clip` | `add_notes_extended` | `get_clip_notes` | `get_clip_notes_with_ids` | `get_notes_extended` | `modify_clip_notes` | `remove_clip_notes_by_id` | `remove_notes_range` | `clear_clip_notes` | `select_all_notes` | `copy_notes_between_clips` | `duplicate_clip_loop` | `deselect_all_notes` | `get_selected_notes` | `transpose_clip_notes` | `humanize_notes` | `randomize_clip_notes` | `transform_notes` | `quantize_clip_notes` | `quantize_to_scale` | `harmonize_melody` | `suggest_harmonies` | `analyze_note_content` | `get_clip_info` | `get_clip_properties` | `get_clip_slot_properties` | `set_clip_properties` | `set_clip_slot_properties` | `set_clip_name` | `set_clip_color` | `get_highlighted_clip_slot` | `set_detail_clip` | `duplicate_clip` | `duplicate_clip_slot` | `delete_clip` | `crop_clip` | `reverse_clip` | `set_clip_pitch` | `get_clip_context`

## Clips — Warp, Loop & Playback (35)

*Warp markers, loop braces, scrubbing, launch modes, follow actions, grooves.*

`set_clip_warp` | `set_warp_mode` | `add_warp_marker` | `move_warp_marker` | `remove_warp_marker` | `get_warp_markers` | `set_clip_loop_points` | `set_clip_looping` | `set_clip_start_end` | `set_clip_start_time` | `set_clip_grid` | `clip_to_grid` | `grid_to_clip` | `clip_beat_to_sample_time` | `clip_sample_to_beat_time` | `clip_scrub` | `clip_scrub_native` | `clip_stop_scrub` | `fire_clip` | `stop_clip` | `stop_track_clips` | `stop_all_clips` | `move_clip_playing_pos` | `jump_in_running_session_clip` | `set_clip_launch_mode` | `set_clip_launch_quantization` | `set_clip_legato` | `set_fire_button_state` | `get_clip_follow_actions` | `set_clip_follow_actions` | `batch_set_follow_actions` | `apply_groove` | `set_groove_settings` | `set_groove_properties` | `get_groove_pool`

## Arrangement View (23)

*Edit the timeline: move/crop/duplicate clips, insert/delete time, cue points, arrangement analysis.*

`get_arrangement_overview` | `get_arrangement_clips` | `get_arrangement_clip_info` | `create_arrangement_midi_clip` | `create_arrangement_audio_clip` | `create_arrangement_midi_clip_m4l` | `create_arrangement_audio_clip_m4l` | `delete_arrangement_clip` | `move_arrangement_clip` | `duplicate_clip_to_arrangement` | `duplicate_clip_region` | `set_arrangement_clip_properties` | `duplicate_time` | `delete_time` | `insert_silence` | `analyze_arrangement_sections` | `analyze_arrangement_density` | `compare_arrangement_sections` | `get_arrangement_suggestions` | `get_cue_points` | `jump_to_cue` | `jump_to_cue_point` | `set_or_delete_cue`

## Automation (13)

*Clip and track automation: read, write, curves, step sequencer-style automation.*

`create_clip_automation` | `get_clip_automation` | `get_clip_automation_hires` | `get_clip_automation_value` | `clear_clip_automation` | `clear_clip_envelope` | `clear_all_clip_envelopes` | `list_clip_automated_parameters` | `create_track_automation` | `clear_track_automation` | `create_automation_curve` | `create_step_automation` | `get_automation_states`

## Devices & Parameters (15)

*Device presets, hidden parameters, macros, parameter maps.*

`get_device_presets` | `load_device_preset` | `get_device_hidden_parameters` | `set_device_hidden_parameter` | `discover_device_params` | `set_parameter_clean` | `create_parameter_map` | `get_parameter_map` | `list_parameter_maps` | `delete_parameter_map` | `create_macro_controller` | `set_macro_value` | `list_macros` | `delete_macro` | `set_drum_chain_note`

## Max for Live Bridge (optional) (10)

*Deep LOM access via the bundled M4L device: rack internals, hidden params, chunked discovery.*

`m4l_status` | `discover_chains_m4l` | `chain_insert_device_m4l` | `rack_insert_chain_m4l` | `get_chain_device_params_m4l` | `set_chain_device_param_m4l` | `rack_store_variation` | `rack_recall_variation` | `batch_set_hidden_parameters` | `analyze_cross_track_audio`

## Mixer (9)

*Volume/pan/sends in one call (batch), crossfader.*

`set_mixer` | `batch_set_mixer` | `get_chain_mixing` | `set_chain_mixing` | `set_crossfader` | `get_crossfader` | `set_crossfade_assign` | `analyze_session` | `get_playing_clips`

## Browser, Search & Plugins (16)

*Instant search over Live's browser (cached), load samples/devices, plugin scanning.*

`get_browser_tree` | `get_browser_items_at_path` | `search_browser` | `load_sample` | `preview_browser_item` | `refresh_browser_cache_tool` | `get_browser_cache_status` | `get_user_folders` | `get_user_library` | `scan_plugins` | `search_plugins` | `get_plugin_list` | `get_plugin_presets` | `load_plugin_preset` | `configure_plugin` | `set_plugin_parameter_cc`

## Creative & Generative (24)

*Generative MIDI content, mix analysis, AI suggestions, sound-design help.*

`generate_midi` | `generate_bass_line` | `generate_chord_progression` | `generate_drum_pattern` | `generate_arpeggio` | `generate_euclidean_rhythm` | `generate_preset` | `create_polyrhythm` | `euclidean_rhythm` | `scale_constrained_generate` | `duplicate_with_variation` | `get_genre_suggestions` | `get_sound_design_help` | `get_context_help` | `get_ai_suggestions` | `auto_gain_stage` | `analyze_mix_quality` | `analyze_mix_balance` | `analyze_dynamics` | `stutter_effect` | `get_mix_history` | `record_mix_change` | `create_mix_preset` | `load_mix_preset`

## AI Music Toolkit (5)

*One-call music generation: prompt-to-clip, progressions, basslines, pro drum patterns, song skeletons.*

`generate_clip_from_prompt` | `build_chord_progression` | `build_bassline_for_progression` | `generate_advanced_drum_pattern` | `build_song_skeleton`

## Audio Intelligence (6)

*The AI listens: key/BPM detection from audio, audio-to-MIDI, clash finder, hum-to-clip.*

`analyze_audio_key_bpm` | `audio_clip_to_midi` | `find_mix_clashes` | `hum_to_clip` | `analyze_track_audio` | `analyze_track_spectrum`

## Producer Pipeline (2)

*One-prompt-to-demo, reference-track matching.*

`produce_idea_from_prompt` | `match_reference_track`

## Project Context & Checkpoints (4)

*Whole-session map in one call; snapshot before experimenting, diff and restore after.*

`get_project_context` | `create_checkpoint` | `checkpoint_diff` | `get_clip_context`

## Studio Memory (5)

*Persistent taste (preferences) and an automatic journal of every change the AI makes.*

`remember_preference` | `recall_preferences` | `forget_preference` | `get_change_journal` | `clear_change_journal`

## Doctor & Performance Monitoring (15)

*Self-diagnosis in plain language plus CPU/memory/latency analytics.*

`doctor` | `session_integrity_report` | `watch_session` | `get_cpu_usage` | `get_cpu_history` | `get_memory_usage` | `get_latency_info` | `get_session_stats` | `optimize_performance` | `set_performance_alerts` | `record_cpu_usage` | `get_performance_history` | `start_performance_timer` | `stop_performance_timer` | `get_performance_timings`

## Snapshots (12)

*Device and session snapshots, A/B compare, morphing.*

`snapshot_device_state` | `snapshot_all_devices` | `restore_device_snapshot` | `restore_group_snapshot` | `list_snapshots` | `delete_snapshot` | `delete_all_snapshots` | `compare_snapshots` | `morph_between_snapshots` | `get_snapshot_details` | `get_session_snapshot` | `device_ab_compare`

## Scenes (19)

*Scene management, firing, follow actions, macros, capture-and-insert.*

`create_scene` | `delete_scene` | `duplicate_scene` | `select_scene` | `fire_scene` | `fire_scene_as_selected` | `set_scene_name` | `set_scene_color` | `set_scene_tempo` | `get_scene_follow_actions` | `set_scene_follow_actions` | `create_scene_macro` | `fire_scene_macro` | `delete_scene_macro` | `list_scene_macros` | `create_scene_preset` | `load_scene_preset` | `capture_midi` | `capture_and_insert_scene`

## Live Show Control & Backups (13)

*Emergency stop, panic mute, session backups and backup presets.*

`emergency_stop` | `panic_mute` | `panic_unmute` | `get_emergency_status` | `backup_session` | `restore_session` | `list_backups` | `delete_backup` | `get_backup_status` | `save_backup_preset` | `load_backup_preset` | `activate_backup_preset` | `activate_backup_scene`

## Setlist & Show Clock (15)

*Gig utilities: show timer, SMPTE time, setlists, next-song.*

`start_show_clock` | `stop_show_clock` | `get_show_time` | `get_show_status` | `set_show_tempo` | `start_song_timer` | `stop_song_timer` | `get_smpte_time` | `start_session_tracking` | `get_setlist` | `add_song_to_setlist` | `remove_song_from_setlist` | `load_setlist` | `set_next_song` | `set_setlist_mode`

## Show Autopilot (3)

*Hands-free timed scene sequencing for live performance.*

`start_show_autopilot` | `stop_show_autopilot` | `autopilot_status`

## Video & Lighting (16)

*Spout video routing, video presets/transitions, DMX lighting scenes.*

`configure_spout` | `get_spout_status` | `set_video_routing` | `get_video_status` | `get_video_tracks` | `set_video_track_config` | `save_video_preset` | `load_video_preset` | `get_video_presets_list` | `load_transition_preset` | `save_transition_preset` | `set_dmx_channel` | `get_dmx_status` | `save_lighting_scene` | `load_lighting_scene` | `get_lighting_presets`

## Presets & Templates (31)

*Save/load reverb, delay, compressor, EQ, chord, arpeggiator presets; session/track/device templates.*

`save_reverb_preset` | `load_reverb_preset` | `save_delay_preset` | `load_delay_preset` | `save_compressor_preset` | `load_compressor_preset` | `save_eq_preset` | `load_eq_preset` | `save_chord_preset` | `load_chord_preset` | `save_arpeggiator_preset` | `load_arpeggiator_preset` | `list_audio_presets` | `list_midi_presets` | `list_instrument_rack_presets` | `apply_effect_chain` | `load_effect_chain` | `save_effect_chain` | `list_effect_chain_templates` | `save_session_template` | `load_session_template` | `save_track_template` | `load_track_template` | `save_device_template` | `list_templates` | `delete_template` | `save_live_preset` | `load_live_preset` | `list_live_presets` | `delete_live_preset` | `load_drum_kit`

## MIDI Controllers & Mapping (12)

*Controller mappings, 100+ plugin CC maps, raw CC, property observation.*

`get_midi_controllers` | `create_midi_mapping` | `delete_midi_mapping` | `get_midi_mappings` | `save_midi_mapping` | `load_midi_mapping` | `list_cc_maps` | `get_cc_map` | `assign_cc_channel` | `send_raw_cc` | `observe_property` | `stop_observing`

---

**See also:** [README](../README.md) · [Installation](INSTALLATION.md) · [OpenCode setup](OPENCODE.md) · [Claude Desktop setup](CLAUDE_DESKTOP.md) · [Architecture](ARCHITECTURE.md)
