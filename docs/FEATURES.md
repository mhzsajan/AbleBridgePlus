# Features

Complete feature list for AbleBridgePlus.

## Core Features (from AbletonBridge)

### Track Management
- **get_all_tracks_info** — Get information about all tracks at once
- **get_track_info** — Get detailed information about a specific track
- **create_midi_track** — Create a new MIDI track
- **create_audio_track** — Create a new audio track
- **delete_track** — Delete a track
- **duplicate_track** — Duplicate a track with all devices and clips
- **set_track_name** — Set the name of a track
- **set_track_color** — Set the color of a track
- **select_track** — Select a track in the session
- **arm_track** — Arm a track for recording
- **disarm_track** — Disarm a track
- **set_track_arm** — Set the arm state of a track
- **freeze_track** — Freeze a track (render effects in place)
- **unfreeze_track** — Unfreeze a track
- **group_tracks** — Group multiple tracks together
- **set_track_fold** — Collapse or expand a group track
- **set_track_monitoring** — Set the monitoring state of a track

### Clip Management
- **create_clip** — Create a new MIDI clip
- **create_clip_with_notes** — Create a new MIDI clip and add notes in one step
- **delete_clip** — Delete a clip from a clip slot
- **fire_clip** — Launch a clip in Session View
- **stop_clip** — Stop a clip
- **get_clip_info** — Get detailed information about a clip
- **get_clip_notes** — Get MIDI notes from a clip
- **add_notes_to_clip** — Add MIDI notes to a clip
- **add_notes_extended** — Add MIDI notes with extended properties (Live 11+)
- **get_notes_extended** — Get MIDI notes with extended properties
- **clear_clip_notes** — Remove all MIDI notes from a clip
- **duplicate_clip** — Duplicate a clip to another clip slot
- **duplicate_clip_loop** — Double the loop content of a clip
- **set_clip_name** — Set the name of a clip
- **set_clip_color** — Set the color of a clip
- **set_clip_looping** — Set the looping state of a clip
- **set_clip_loop_points** — Set the loop region start and end points
- **set_clip_start_end** — Set clip start and end markers
- **set_clip_warp** — Enable or disable warping
- **set_warp_mode** — Set the warp mode
- **set_clip_pitch** — Set pitch transposition
- **set_clip_properties** — Set multiple clip properties at once
- **set_clip_launch_mode** — Set the launch mode for a clip
- **set_clip_launch_quantization** — Set when a clip starts playing
- **set_clip_legato** — Enable or disable legato mode
- **set_clip_grid** — Set the MIDI editor grid resolution
- **get_clip_properties** — Get extended properties of a clip
- **get_clip_slot_properties** — Get clip slot properties
- **get_clip_follow_actions** — Get follow action settings
- **set_clip_follow_actions** — Set follow action settings
- **batch_set_follow_actions** — Set follow actions on multiple clips at once
- **get_selected_notes** — Get the currently UI-selected notes
- **select_all_notes** — Select all notes in a clip
- **deselect_all_notes** — Deselect all notes in a clip
- **get_clip_notes_with_ids** — Get notes with stable IDs (M4L)
- **modify_clip_notes** — Modify notes in-place by ID (M4L)
- **remove_clip_notes_by_id** — Remove notes by ID (M4L)
- **quantize_clip_notes** — Quantize notes to a grid
- **quantize_to_scale** — Snap notes to a scale
- **transpose_clip_notes** — Transpose all notes
- **transform_notes** — Transform notes (transpose, reverse, etc.)
- **humanize_notes** — Add humanization to notes
- **randomize_clip_notes** — Generate random notes
- **copy_notes_between_clips** — Copy notes from one clip to another
- **duplicate_clip_region** — Duplicate a region of notes
- **remove_notes_range** — Remove notes in a range
- **crop_clip** — Trim clip to loop region
- **reverse_clip** — Reverse an audio clip
- **set_detail_clip** — Show a clip in Detail view

### Device Management
- **get_device_parameters** — Get all parameters for a device
- **set_device_parameter** — Set a device parameter
- **set_device_parameters** — Set multiple parameters at once
- **set_device_enabled** — Toggle a device on/off
- **get_device_info** — Get detailed device information
- **get_device_presets** — Get available presets
- **load_device_preset** — Load a preset onto a device
- **delete_device** — Delete a device
- **move_device** — Move a device to another track
- **get_appointed_device** — Get the selected device
- **select_device_in_view** — Select a device to show in Detail view
- **select_instrument** — Select and show the first instrument
- **get_device_hidden_parameters** — Get all parameters including hidden ones
- **set_device_hidden_parameter** — Set a hidden parameter
- **batch_set_hidden_parameters** — Set multiple hidden parameters at once
- **discover_device_params** — Discover all parameters including hidden ones
- **get_device_property** — Read a device-level LOM property
- **set_device_property** — Set a device-level LOM property
- **list_device_properties** — List all known properties for a device
- **snapshot_device_state** — Capture complete device state
- **restore_device_snapshot** — Restore a saved state
- **snapshot_all_devices** — Snapshot all devices on tracks
- **restore_group_snapshot** — Restore all devices from a group snapshot
- **list_snapshots** — List all stored snapshots
- **get_snapshot_details** — Get full details of a snapshot
- **delete_snapshot** — Delete a snapshot
- **delete_all_snapshots** — Delete all snapshots
- **compare_snapshots** — Compare two snapshots
- **morph_between_snapshots** — Interpolate between two snapshots
- **create_parameter_map** — Create a custom parameter map
- **get_parameter_map** — Retrieve a stored parameter map
- **delete_parameter_map** — Delete a stored parameter map
- **list_parameter_maps** — List all stored parameter maps
- **device_ab_compare** — Compare device presets (Live 12.3+)

### Mixer Controls
- **set_mixer** — Set mixer parameters for a track
- **batch_set_mixer** — Set mixer parameters for multiple tracks at once
- **set_panning_mode** — Set the panning mode
- **set_split_stereo_pan** — Set split stereo panning
- **get_split_stereo** — Get split stereo panning values
- **set_track_send** — Set a send level
- **get_track_send** — Get a send level
- **setup_send_return** — Create a return track with effect and sends
- **set_crossfader** — Set the master crossfader position
- **get_crossfader** — Get the crossfader position
- **set_crossfade_assign** — Set A/B crossfade assignment
- **set_cue_volume** — Set the cue/preview volume
- **get_track_meters** — Get live output meter levels
- **get_track_input_meters** — Get input meter levels
- **analyze_track_audio** — Analyze audio levels on a track
- **analyze_track_spectrum** — Get spectral analysis data
- **analyze_cross_track_audio** — Analyze audio from any track via routing

### Browser Operations
- **get_browser_tree** — Get a hierarchical tree of browser categories
- **search_browser** — Search the browser for items
- **load_instrument_or_effect** — Load an instrument or effect
- **load_drum_kit** — Load a drum rack and kit
- **load_sample** — Load an audio sample
- **get_browser_items_at_path** — Get items at a browser path
- **preview_browser_item** — Preview a browser item
- **get_user_folders** — Get user sample folders
- **get_user_library** — Get user library tree
- **refresh_browser_cache_tool** — Force browser cache refresh
- **list_instrument_rack_presets** — List Instrument Rack presets

### Automation
- **create_clip_automation** — Create automation in a clip envelope
- **create_track_automation** — Create arrangement-level automation
- **get_clip_automation** — Read existing automation from a clip
- **get_clip_automation_hires** — Read automation with configurable resolution
- **get_clip_automation_value** — Read automation value at a specific time
- **list_clip_automated_parameters** — List parameters with automation
- **clear_clip_automation** — Clear automation for a parameter
- **clear_clip_envelope** — Clear automation envelope
- **clear_all_clip_envelopes** — Clear all envelopes
- **clear_track_automation** — Clear automation in a time range
- **create_automation_curve** — Generate curved automation
- **create_step_automation** — Create step (held-value) automation

### Arrangement View
- **get_arrangement_overview** — Get high-level overview
- **get_arrangement_clips** — Get all clips for a track
- **get_arrangement_clip_info** — Get detailed clip info
- **set_arrangement_clip_properties** — Set clip properties
- **create_arrangement_midi_clip** — Create a MIDI clip
- **create_arrangement_audio_clip** — Create an audio clip
- **move_arrangement_clip** — Move a clip
- **delete_arrangement_clip** — Delete a clip
- **duplicate_clip_to_arrangement** — Copy session clip to arrangement
- **duplicate_time** — Duplicate a section of time
- **delete_time** — Delete a section of time
- **insert_silence** — Insert silence
- **analyze_arrangement_density** — Analyze clip density
- **analyze_arrangement_sections** — Detect song sections
- **compare_arrangement_sections** — Compare two sections

### Creative Tools
- **generate_chord_progression** — Generate chord progressions
- **generate_bass_line** — Generate bass lines
- **generate_arpeggio** — Generate arpeggios
- **generate_drum_pattern** — Generate drum patterns
- **euclidean_rhythm** — Generate Euclidean rhythms
- **generate_euclidean_rhythm** — Generate Euclidean rhythms (alternative)
- **create_polyrhythm** — Create polyrhythmic patterns
- **scale_constrained_generate** — Generate notes constrained to a scale
- **harmonize_melody** — Add harmony to a melody
- **stutter_effect** — Create stutter/glitch patterns
- **create_macro_controller** — Create a macro controller
- **set_macro_value** — Set a macro value
- **list_macros** — List all macro controllers
- **delete_macro** — Delete a macro controller

### Scene Management
- **get_scenes** — Get information about all scenes
- **create_scene** — Create a new scene
- **delete_scene** — Delete a scene
- **fire_scene** — Launch a scene
- **fire_scene_as_selected** — Fire a scene without moving selection
- **select_scene** — Select a scene
- **set_scene_name** — Set the name of a scene
- **set_scene_color** — Set the color of a scene
- **capture_and_insert_scene** — Capture currently playing clips into a new scene
- **duplicate_scene** — Duplicate a scene
- **get_scene_follow_actions** — Get follow action settings
- **set_scene_follow_actions** — Set follow action settings
- **set_scene_tempo** — Set or clear a scene's tempo override

### Session Management
- **get_session_info** — Get detailed session information
- **get_full_session_state** — Get complete session state in one call
- **get_all_tracks_info** — Get information about all tracks at once
- **get_return_tracks_info** — Get detailed return track info
- **get_scenes** — Get all scenes
- **get_transport** — Get transport state
- **set_song_time** — Set the playback position
- **get_song_time** — Get the current playback position
- **start_playback** — Start playing
- **stop_playback** — Stop playing
- **continue_playing** — Resume from current position
- **navigate_playback** — Jump, scrub, or play selection
- **set_tempo** — Set the tempo
- **tap_tempo** — Tap tempo
- **nudge_tempo** — Momentarily nudge tempo
- **set_metronome** — Enable/disable metronome
- **set_song_loop** — Control the arrangement loop
- **get_loop_info** — Get loop bracket information
- **set_song_scale** — Set the song's scale settings
- **get_song_scale** — Get the song's scale settings
- **set_song_settings** — Set global song settings
- **get_song_settings** — Get global song settings
- **set_or_delete_cue** — Toggle a cue point
- **get_cue_points** — Get all cue points
- **jump_to_cue** — Jump to next/previous cue
- **jump_to_cue_point** — Jump to a specific cue point
- **set_follow_song** — Toggle follow song
- **set_draw_mode** — Toggle draw mode
- **set_arrangement_overdub** — Enable/disable overdub
- **set_session_record** — Enable/disable session recording
- **trigger_session_record** — Trigger session recording
- **start_arrangement_recording** — Start arrangement recording
- **stop_arrangement_recording** — Stop arrangement recording
- **get_recording_status** — Get recording status
- **get_beat_time** — Get current position as bars:beats:ticks
- **get_smpte_time** — Get current position as SMPTE timecode
- **get_song_length** — Get total song length
- **set_punch_recording** — Control punch in/out
- **get_link_status** — Get Link sync status
- **set_link_enabled** — Enable/disable Link
- **get_tuning_system** — Get tuning system
- **get_all_scales** — Get all available scales
- **set_view** — Show, hide, or focus a view
- **get_view_state** — Get current view state
- **zoom_scroll_view** — Zoom or scroll a view

### Snapshots & State
- **get_song_data** — Get persistent data from the song
- **set_song_data** — Store persistent data in the song
- **get_track_data** — Get persistent data from a track
- **set_track_data** — Store persistent data on a track
- **get_groove_pool** — Get all grooves from the groove pool
- **set_groove_properties** — Set groove properties
- **set_groove_settings** — Set global groove settings
- **apply_groove** — Apply groove to a clip
- **get_highlighted_clip_slot** — Get the currently highlighted clip slot
- **get_selection_state** — Get what is currently selected
- **get_appointed_device** — Get the currently selected device
- **get_selected_parameter** — Get the currently selected parameter
- **get_playing_clips** — Get all currently playing clips
- **get_track_meters** — Get live output meter levels
- **get_track_input_meters** — Get input meter levels
- **stop_all_clips** — Stop all playing clips
- **stop_track_clips** — Stop all clips on a track

### Advanced Features
- **get_track_routing** — Get current input/output routing
- **set_track_routing** — Set input/output routing
- **get_track_delay** — Get track delay compensation
- **set_track_delay** — Set track delay compensation
- **get_return_track_info** — Get detailed return track info
- **get_return_tracks** — Get all return tracks
- **get_master_track_info** — Get master track info
- **get_chain_selector** — Get chain selector value
- **set_chain_selector** — Set chain selector value
- **get_chain_mixing** — Get chain mixing state
- **set_chain_mixing** — Set chain mixing properties
- **set_chain_properties** — Set chain properties
- **discover_chains_m4l** — Discover chains in a rack via M4L
- **get_chain_device_params_m4l** — Get device params in a chain via M4L
- **set_chain_device_param_m4l** — Set device param in a chain via M4L
- **chain_insert_device** — Insert a device into a rack chain
- **chain_insert_device_m4l** — Insert a device into a chain via M4L
- **insert_chain** — Insert a new chain into a rack
- **rack_insert_chain_m4l** — Insert a new chain via M4L
- **rack_store_variation** — Store rack macro variation
- **rack_recall_variation** — Recall rack macro variation
- **rack_variation_action** — Perform variation action
- **get_rack_variations** — Get rack variation info
- **get_plugin_info** — Get plugin-specific info
- **get_eq8_properties** — Get EQ Eight properties
- **set_eq8_properties** — Set EQ Eight properties
- **get_compressor_sidechain** — Get side-chain routing info
- **set_compressor_sidechain** — Set side-chain routing
- **get_hybrid_reverb_ir** — Get impulse response config
- **set_hybrid_reverb_ir** — Set impulse response config
- **get_simpler_properties** — Get Simpler properties
- **set_simpler_properties** — Set Simpler properties
- **simpler_sample_action** — Perform action on Simpler sample
- **manage_sample_slices** — Manage slice points
- **sliced_simpler_to_drum_rack** — Convert sliced Simpler to Drum Rack
- **get_drum_pads** — Get drum pad information
- **set_drum_pad** — Set mute/solo on drum pad
- **copy_drum_pad** — Copy drum pad contents
- **set_drum_chain_note** — Set input note for drum chain
- **get_warp_markers** — Get warp markers
- **add_warp_marker** — Add a warp marker
- **move_warp_marker** — Move a warp marker
- **remove_warp_marker** — Remove a warp marker
- **clip_beat_to_sample_time** — Convert beat time to sample time
- **clip_sample_to_beat_time** — Convert sample time to beat time
- **get_transmute_properties** — Get Transmute properties
- **set_transmute_properties** — Set Transmute properties
- **audio_to_midi** — Convert audio to MIDI
- **capture_midi** — Capture recently played MIDI
- **get_automation_states** — Get automation states for a device
- **re_enable_automation** — Re-enable all overridden automation
- **get_m4l_bridge_status** — Check M4L bridge status
- **get_ableton_version** — Get Ableton version
- **undo** — Undo last action
- **redo** — Redo last undone action
- **end_undo_step** — End undo step

---

## Enhanced Features (Our Additions)

### Routing Channels (Enhancement)
- **get_routing_channels** — Get all available routing channels for a track
- **get_routing_types** — Get all available routing types for a track
- **set_routing_preset** — Set routing from a saved preset
- **get_routing_presets** — Get saved routing presets

### MIDI Mapping Tools (New)
- **get_midi_mappings** — List all MIDI controller mappings
- **create_midi_mapping** — Map controller to parameter
- **delete_midi_mapping** — Remove a MIDI mapping
- **save_midi_mapping** — Save a MIDI mapping preset
- **load_midi_mapping** — Load a MIDI mapping preset
- **get_midi_controllers** — List connected MIDI controllers
- **get_midi_mappings_for_controller** — Get mappings for a specific controller

### Plugin Management Tools (New)
- **scan_plugins** — Scan/rescan VST/AU plugins
- **get_plugin_list** — List available plugins
- **configure_plugin** — Configure VST/AU parameters
- **get_plugin_presets** — Get plugin presets
- **load_plugin_preset** — Load a plugin preset
- **save_plugin_preset** — Save a plugin preset
- **get_plugin_info_detailed** — Get detailed plugin information
- **search_plugins** — Search plugins by name/category

### Video Routing Tools (Videosync2) (New)
- **get_video_tracks** — List video tracks
- **set_video_routing** — Route video to output
- **get_video_status** — Check Videosync2 status
- **play_video_clip** — Play a video clip
- **stop_video_clip** — Stop a video clip
- **get_video_effects** — List video effects
- **set_video_effect** — Set a video effect parameter
- **configure_spout** — Configure Spout output
- **get_spout_status** — Get Spout output status

### Setlist Management Tools (AbleSet) (New)
- **get_setlist** — Get current setlist
- **load_setlist** — Load a setlist file
- **set_next_song** — Set next song to play
- **get_song_info** — Get song details (tempo, key, etc.)
- **get_song_sections** — Get song sections (verse, chorus, etc.)
- **set_song_transition** — Set song transition
- **get_current_song** — Get currently playing song
- **set_setlist_mode** — Switch to setlist mode
- **set_sound_check_mode** — Switch to sound check mode

### Performance Monitoring Tools (New)
- **get_cpu_usage** — Get CPU usage per track/device
- **get_memory_usage** — Get memory usage
- **get_latency_info** — Get latency information
- **get_plugin_cpu_usage** — Get CPU usage per plugin
- **get_buffer_status** — Get buffer status
- **set_performance_alerts** — Set performance alerts
- **get_performance_history** — Get performance history
- **optimize_performance** — Suggest performance optimizations

### Quick Presets Tools (New)
- **save_live_preset** — Save live show preset
- **load_live_preset** — Load live show preset
- **list_live_presets** — List available presets
- **delete_live_preset** — Delete a preset
- **create_scene_preset** — Save scene state as preset
- **load_scene_preset** — Load scene state from preset
- **create_mix_preset** — Save mix state as preset
- **load_mix_preset** — Load mix state from preset
- **create_device_preset** — Save device state as preset
- **load_device_preset_enhanced** — Load device state from preset

### AI Integration Features (New)
- **get_session_snapshot** — Capture full session state
- **analyze_session** — Analyze session for AI suggestions
- **get_ai_suggestions** — Get AI-powered mixing suggestions
- **natural_language_command** — Parse natural language to actions
- **get_context_help** — Get help based on current session state
- **generate_midi** — AI-powered MIDI generation
- **suggest_harmonies** — Suggest harmonies for a melody
- **analyze_mix** — Analyze mix balance
- **suggest_effects** — Suggest effects for a track

### Audio Analysis Tools (New)
- **get_track_spectrum** — Get frequency spectrum per track
- **get_audio_levels** — Get RMS/peak levels
- **analyze_frequency** — Analyze frequency content
- **detect_chord** — Detect chords in MIDI clips
- **detect_scale** — Detect scale/key of session
- **analyze_mix_balance** — Analyze mix balance
- **get_beat_grid** — Get beat grid information
- **analyze_dynamics** — Analyze dynamic range

### Template System (New)
- **save_session_template** — Save session as template
- **load_session_template** — Load session from template
- **save_track_template** — Save track as template
- **load_track_template** — Load track from template
- **save_device_template** — Save device chain as template
- **load_device_template** — Load device chain from template
- **save_mix_template** — Save mix state as template
- **load_mix_template** — Load mix state from template
- **list_templates** — List available templates
- **delete_template** — Delete a template

### Advanced Routing Tools (New)
- **set_sidechain_routing** — Set side-chain compression
- **set_multi_output_routing** — Configure multi-output plugins
- **save_routing_preset** — Save routing configuration
- **load_routing_preset** — Load routing configuration
- **set_resampling** — Configure resampling
- **get_routing_presets_list** — List saved routing presets

### Automation Enhancement (New)
- **save_automation_preset** — Save automation preset
- **load_automation_preset** — Load automation preset
- **apply_automation_template** — Apply automation from template
- **batch_apply_automation** — Apply automation to multiple tracks
- **analyze_automation** — Analyze automation curves
- **suggest_automation** — Suggest automation improvements

---

## Tool Count Summary

| Category | Count |
|----------|-------|
| Core Features (from AbletonBridge) | 340+ |
| Enhanced Features (our additions) | 100+ |
| **Total** | **440+** |

## Tool Usage Examples

### Basic Usage
```python
# Create a MIDI track
create_midi_track()

# Load an instrument
load_instrument_or_effect(track_index=0, uri="Wavetable")

# Create a clip with notes
create_clip_with_notes(
    track_index=0,
    clip_index=0,
    length=4.0,
    notes=[{"pitch": 60, "start_time": 0, "duration": 1.0, "velocity": 100}]
)
```

### Live Show Control
```python
# Load a live show preset
load_live_preset(preset_name="Concert")

# Fire a scene
fire_scene(scene_index=0)

# Set next song
set_next_song(song_name="Kutu Ma Timi")

# Get CPU usage
get_cpu_usage()
```

### Video Integration
```python
# Get video tracks
get_video_tracks()

# Route video to Spout
configure_spout(enabled=True)

# Play a video clip
play_video_clip(track_index=14, clip_index=0)
```

### AI Integration
```python
# Get session snapshot
get_session_snapshot()

# Analyze session
analyze_session()

# Get AI suggestions
get_ai_suggestions()
```

---

## Future Features

### Planned
- LIA plugin integration (when available)
- TouchDesigner integration
- Automated show control
- Multi-DAW support
- Cloud integration
- Advanced AI features
- Machine learning for mixing
- Automated mastering

### Under Consideration
- Video generation
- Audio synthesis
- Real-time collaboration
- Mobile app control
- Voice control
