# Enhanced AbletonBridge

An enhanced AI integration layer for Ableton Live, designed to bridge the gap between AI tools and music production. Built on the foundation of [AbletonBridge](https://github.com/hidingwill/AbletonBridge) by [hidingwill](https://github.com/hidingwill).

## Credits

This project is based on [AbletonBridge](https://github.com/hidingwill/AbletonBridge) by [hidingwill](https://github.com/hidingwill).

**Original Features Preserved:**
- MCP Server architecture
- TCP/UDP communication protocol
- M4L Bridge for hidden parameters
- Tool organization and modular structure
- Chunked response handling
- Real-time UDP parameter updates
- Browser cache system
- Async tool handlers

**Enhanced Features Added:**
- Routing channel exposure
- MIDI controller mapping tools
- Plugin management tools
- Videosync2 video routing integration
- AbleSet setlist management
- Performance monitoring (CPU/memory)
- Live show presets and control
- AI integration features
- Audio analysis tools
- Template system
- Advanced routing capabilities
- Automation enhancement

**Special Thanks:**
- hidingwill for creating the original AbletonBridge
- The Ableton Live community for inspiration
- Max for Live developers for the M4L Bridge

## Features

### Tool Count: 440+ Tools Across 14 Categories

| Category | Count | Description |
|----------|-------|-------------|
| Core Features (from AbletonBridge) | 340+ | Tracks, Clips, Devices, Mixer, Browser, Automation, etc. |
| Enhanced Features (our additions) | 100+ | MIDI Mapping, Video, Setlist, Performance, AI, etc. |
| **Total** | **440+** | Complete Ableton Live control |

---

### Original AbletonBridge Features (340+ tools)

#### Track Management
- **get_all_tracks_info** — Get information about all tracks at once
- **create_midi_track** / **create_audio_track** — Create new tracks
- **delete_track** / **duplicate_track** — Manage tracks
- **arm_track** / **disarm_track** — Recording control
- **freeze_track** / **unfreeze_track** — CPU optimization
- **group_tracks** — Group tracks together

#### Clip Management
- **create_clip_with_notes** — Create MIDI clips with notes
- **fire_clip** / **stop_clip** — Launch clips
- **add_notes_to_clip** / **get_clip_notes** — MIDI note operations
- **quantize_clip_notes** / **transpose_clip_notes** — Note transformation
- **humanize_notes** / **randomize_clip_notes** — Creative tools

#### Device Management
- **get_device_parameters** / **set_device_parameter** — Parameter control
- **load_instrument_or_effect** — Load devices from browser
- **get_device_hidden_parameters** — Access hidden parameters
- **snapshot_device_state** / **restore_device_snapshot** — State management

#### Mixer Controls
- **set_mixer** — Volume, pan, mute, solo
- **batch_set_mixer** — Multiple tracks at once
- **set_track_send** — Send levels

#### Browser Operations
- **get_browser_tree** — Browse categories
- **search_browser** — Find devices/presets
- **load_instrument_or_effect** — Load items

#### Automation
- **create_clip_automation** — Clip envelope automation
- **create_track_automation** — Arrangement automation
- **create_automation_curve** — Generate curved automation

#### Creative Tools
- **generate_chord_progression** — AI chord generation
- **generate_bass_line** — Bass pattern creation
- **generate_drum_pattern** — Drum patterns
- **scale_constrained_generate** — Scale-aware generation
- **quantize_to_scale** — Snap to scale

---

### Enhanced Features (Our Additions — 100+ Tools)

#### 1. MIDI Mapping (7 tools)
- **get_midi_mappings** — List all MIDI controller mappings
- **create_midi_mapping** — Map controller to parameter
- **delete_midi_mapping** — Remove a MIDI mapping
- **save_midi_mapping** / **load_midi_mapping** — Save/load presets
- **get_midi_controllers** — List connected MIDI controllers

#### 2. Plugin Management (8 tools)
- **scan_plugins** — Scan/rescan VST/AU plugins
- **get_plugin_list** — List available plugins
- **configure_plugin** — Configure VST/AU parameters
- **get_plugin_presets** / **load_plugin_preset** — Preset management
- **search_plugins** — Search by name/category

#### 3. Video Integration (10 tools)
- **get_video_tracks** — List video tracks
- **set_video_routing** — Route video to output
- **get_video_status** — Check Videosync2 status
- **play_video_clip** / **stop_video_clip** — Video clip control
- **configure_spout** — Configure Spout output
- **get_spout_status** — Get Spout output status

#### 4. Setlist Management (9 tools)
- **get_setlist** — Get current setlist
- **load_setlist** — Load a setlist file
- **set_next_song** — Set next song to play
- **get_song_info** — Get song details (tempo, key, etc.)
- **get_song_sections** — Get song sections (verse, chorus, etc.)
- **set_setlist_mode** — Switch to setlist mode
- **set_sound_check_mode** — Switch to sound check mode

#### 5. Performance Monitoring (8 tools)
- **get_cpu_usage** — Get CPU usage per track/device
- **get_memory_usage** — Get memory usage
- **get_latency_info** — Get latency information
- **get_plugin_cpu_usage** — Get CPU usage per plugin
- **get_buffer_status** — Get buffer status
- **optimize_performance** — Suggest performance optimizations

#### 6. Quick Presets (10 tools)
- **save_live_preset** / **load_live_preset** — Live show presets
- **list_live_presets** / **delete_live_preset** — Preset management
- **create_scene_preset** / **load_scene_preset** — Scene presets
- **create_mix_preset** / **load_mix_preset** — Mix presets
- **create_device_preset** / **load_device_preset_enhanced** — Device presets

#### 7. AI Integration (9 tools)
- **get_session_snapshot** — Capture full session state
- **analyze_session** — Analyze session for AI suggestions
- **get_ai_suggestions** — Get AI-powered mixing suggestions
- **generate_midi** — AI-powered MIDI generation
- **suggest_harmonies** — Suggest harmonies for a melody
- **get_context_help** — Get help based on current session state

#### 8. Audio Analysis (8 tools)
- **get_track_spectrum** — Get frequency spectrum per track
- **get_audio_levels** — Get RMS/peak levels
- **analyze_frequency** — Analyze frequency content
- **detect_chord** — Detect chords in MIDI clips
- **detect_scale** — Detect scale/key of session
- **analyze_mix_balance** — Analyze mix balance
- **analyze_dynamics** — Analyze dynamic range

#### 9. Template System (10 tools)
- **save_session_template** / **load_session_template** — Session templates
- **save_track_template** / **load_track_template** — Track templates
- **save_device_template** / **load_device_template** — Device templates
- **list_templates** / **delete_template** — Template management

#### 10. Advanced Routing (6 tools)
- **set_sidechain_routing** — Set side-chain compression
- **save_routing_preset** / **load_routing_preset** — Routing presets
- **get_routing_presets_list** — List saved routing presets

#### 11. Automation Enhancement (6 tools)
- **save_automation_preset** / **load_automation_preset** — Automation presets
- **apply_automation_template** — Apply automation from template
- **batch_apply_automation** — Apply automation to multiple tracks
- **analyze_automation** — Analyze automation curves

---

### Comparison: Original vs Enhanced

| Feature | Original | Enhanced |
|---------|----------|----------|
| **Tool Count** | 353 | 440+ |
| **Routing Channels** | Missing | Exposed ✅ |
| **MIDI Mapping** | None | 7 tools ✅ |
| **Plugin Management** | None | 8 tools ✅ |
| **Video Integration** | None | 10 tools ✅ |
| **Setlist Management** | None | 9 tools ✅ |
| **Performance Monitoring** | None | 8 tools ✅ |
| **Live Show Presets** | None | 10 tools ✅ |
| **AI Integration** | None | 9 tools ✅ |
| **Audio Analysis** | None | 8 tools ✅ |
| **Template System** | None | 10 tools ✅ |
| **Advanced Routing** | None | 6 tools ✅ |
| **Emergency Stop** | None | Included ✅ |
| **Session Snapshots** | None | Included ✅ |

---

### Use Cases

| Use Case | Original | Enhanced |
|----------|----------|----------|
| General Ableton control | ✅ | ✅ |
| Live show engineering | ❌ | ✅ |
| Video integration | ❌ | ✅ |
| AI-assisted mixing | ❌ | ✅ |
| Plugin management | ❌ | ✅ |
| MIDI controller mapping | ❌ | ✅ |
| Performance monitoring | ❌ | ✅ |
| Setlist management | ❌ | ✅ |

---

### Example Usage

#### Basic Ableton Control
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

#### Live Show Control
```python
# Load live show preset
load_live_preset(preset_name="Concert")

# Fire scene
fire_scene(scene_index=0)

# Set next song
set_next_song(song_name="Kutu Ma Timi")

# Get CPU usage
get_cpu_usage()
```

#### Video Integration
```python
# Configure Spout output
configure_spout(enabled=True, port=5000)

# Get video tracks
video_tracks = get_video_tracks()

# Play video clip
play_video_clip(track_index=14, clip_index=0)
```

#### AI Integration
```python
# Get session snapshot
snapshot = get_session_snapshot()

# Get AI suggestions
suggestions = get_ai_suggestions(context="mixing")

# Generate MIDI
generate_midi(
    track_index=0,
    clip_index=0,
    style="melody",
    scale="minor",
    root=60
)
```

## Installation

### Prerequisites
- Ableton Live 10, 11, or 12
- Python 3.8+
- uv (for running the MCP server)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mhzsajan/enhanced-abletonbridge.git
   cd enhanced-abletonbridge
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Copy Remote Script to Ableton:**
   - Copy `AbletonBridge_Remote_Script` folder to:
     - Windows: `Documents/Ableton/User Library/Remote Scripts/`
     - macOS: `~/Music/Ableton/User Library/Remote Scripts/`

4. **Configure Ableton:**
   - Open Ableton Live
   - Go to Preferences → Link, Tempo & MIDI
   - Under "Control Surface", select "AbletonBridge"
   - Set Input and Output to "AbletonBridge"

5. **Start the MCP Server:**
   ```bash
   uv run python -m MCP_Server.server
   ```

6. **Configure your AI tool:**
   - Add to your MCP client configuration:
   ```json
   {
     "abletonbridge": {
       "command": "uv",
       "args": ["run", "python", "-m", "MCP_Server.server"],
       "cwd": "/path/to/enhanced-abletonbridge"
     }
   }
   ```

## Usage

### Basic Usage
Once configured, you can control Ableton Live through natural language:

- "Create a MIDI track and load Operator"
- "Write a 4-bar chord progression in C minor"
- "Set up side-chain compression on the bass track"
- "Get the current session state"

### Live Show Control
For live performance:

- "Load the 'Concert' preset"
- "Fire scene 3"
- "Set next song to 'Kutu Ma Timi'"
- "Show CPU usage"

### Video Integration
For Videosync2:

- "Get video tracks"
- "Route video to Spout output"
- "Play video clip on track 15"

## Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Features](docs/FEATURES.md)
- [API Reference](docs/API.md)
- [Examples](docs/EXAMPLES.md)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [hidingwill](https://github.com/hidingwill) for creating the original AbletonBridge
- [Ableton](https://www.ableton.com/) for making such an amazing DAW
- [Max for Live](https://cycling74.com/products/max) for the M4L Bridge
- The music production community for inspiration and feedback
