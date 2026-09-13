# Enhanced AbletonBridge

MCP bridge connecting AI/LLM tools to Ableton Live, enhanced for live show performances. 440+ tools for AI-assisted music production and real-time show control.

Built on [AbletonBridge](https://github.com/hidingwill/AbletonBridge) by [hidingwill](https://github.com/hidingwill).

[![Release](https://img.shields.io/github/v/release/mhzsajan/enhanced-abletonbridge)](https://github.com/mhzsajan/enhanced-abletonbridge/releases)
[![License](https://img.shields.io/github/license/mhzsajan/enhanced-abletonbridge)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## Quick Install

### Windows
```bash
# Download from GitHub Releases, extract, and run:
install.bat
```

### macOS/Linux
```bash
# Download from GitHub Releases, extract, and run:
chmod +x install.sh
./install.sh
```

### Manual Install
```bash
git clone https://github.com/mhzsajan/enhanced-abletonbridge.git
cd enhanced-abletonbridge
uv sync
```

---

## Setup

1. Copy `AbletonBridge_Remote_Script` to Ableton's Remote Scripts folder:
   - **Windows:** `Documents/Ableton/User Library/Remote Scripts/`
   - **macOS:** `~/Music/Ableton/User Library/Remote Scripts/`

2. Open Ableton → Preferences → Link, Tempo & MIDI → Select "AbletonBridge" as Control Surface

3. Start the MCP Server:
   ```bash
   uv run python -m MCP_Server.server
   ```

---

## Features

**440+ tools** across **14 categories** for complete Ableton Live control.

| Category | Tools | Description |
|----------|-------|-------------|
| Tracks, Clips, Devices | 340+ | Core Ableton operations |
| MIDI Mapping | 7 | Controller integration |
| Plugin Management | 8 | VST/AU scanning and config |
| Video Integration | 10 | Videosync2 and Spout |
| Setlist Management | 9 | AbleSet integration |
| Performance Monitoring | 8 | CPU, memory, latency |
| Live Show Presets | 10 | Quick recall, emergency stop |
| AI Integration | 9 | Snapshots, suggestions |
| Audio Analysis | 8 | Spectrum, chords, dynamics |
| Template System | 10 | Save/load sessions |
| Advanced Routing | 6 | Side-chain, multi-output |
| Automation Enhancement | 6 | Presets, templates |

### What's New vs Original

| Feature | Original | Enhanced |
|---------|----------|----------|
| Tool Count | 353 | 440+ |
| Routing Channels | Missing | Exposed |
| MIDI Mapping | No | Yes |
| Video Integration | No | Yes |
| Setlist Management | No | Yes |
| Performance Monitoring | No | Yes |
| AI Integration | No | Yes |

---

## Usage Examples

### Basic Control
```python
create_midi_track()
load_instrument_or_effect(track_index=0, uri="Wavetable")
create_clip_with_notes(
    track_index=0, clip_index=0, length=4.0,
    notes=[{"pitch": 60, "start_time": 0, "duration": 1.0, "velocity": 100}]
)
```

### Live Show
```python
load_live_preset(preset_name="Concert")
fire_scene(scene_index=0)
set_next_song(song_name="Kutu Ma Timi")
get_cpu_usage()
```

### Video Integration
```python
configure_spout(enabled=True, port=5000)
video_tracks = get_video_tracks()
play_video_clip(track_index=14, clip_index=0)
```

### AI Integration
```python
snapshot = get_session_snapshot()
suggestions = get_ai_suggestions(context="mixing")
generate_midi(track_index=0, clip_index=0, style="melody", scale="minor", root=60)
```

---

## Natural Language Commands

- "Create a MIDI track and load Operator"
- "Write a 4-bar chord progression in C minor"
- "Set up side-chain compression on the bass track"
- "Load the 'Concert' preset"
- "Fire scene 3"
- "Show CPU usage"

---

## Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Features](docs/FEATURES.md)
- [Architecture](docs/ARCHITECTURE.md)

---

## Credits

Based on [AbletonBridge](https://github.com/hidingwill/AbletonBridge) by [hidingwill](https://github.com/hidingwill). See [LICENSE](LICENSE) for details.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
