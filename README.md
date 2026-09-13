# Enhanced AbletonBridge

MCP bridge connecting AI/LLM tools to Ableton Live, enhanced for live show performances. 440+ tools for AI-assisted music production and real-time show control.

**By Sajan Maharjan**  
*Inspiration from [AbletonBridge](https://github.com/hidingwill/AbletonBridge) by [hidingwill](https://github.com/hidingwill)*

[![Release](https://img.shields.io/github/v/release/mhzsajan/enhanced-abletonbridge)](https://github.com/mhzsajan/enhanced-abletonbridge/releases)
[![License](https://img.shields.io/github/license/mhzsajan/enhanced-abletonbridge)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

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

---

## Side-by-Side Comparison

| Category | Original AbletonBridge | Enhanced AbletonBridge |
|----------|----------------------|----------------------|
| **Tool Count** | 353 | 440+ |
| **Tracks** | create, delete, duplicate, group, arm, freeze | + routing channels exposed |
| **Clips** | create, fire, stop, notes, quantize, humanize | + batch operations |
| **Devices** | parameters, presets, snapshots, hidden params | + plugin management |
| **Mixer** | volume, pan, mute, solo, sends | + batch set multiple tracks |
| **Browser** | tree, search, load instruments/effects | + plugin scanning |
| **Automation** | clip envelopes, track automation, curves | + presets, templates |
| **Creative** | chord progression, bass line, drum patterns | + AI generation |
| **MIDI Mapping** | ❌ | ✅ 7 tools (get, create, delete, save/load) |
| **Plugin Management** | ❌ | ✅ 8 tools (scan, list, configure, presets) |
| **Video Integration** | ❌ | ✅ 10 tools (Videosync2, Spout, video clips) |
| **Setlist Management** | ❌ | ✅ 9 tools (AbleSet, songs, transitions) |
| **Performance Monitoring** | ❌ | ✅ 8 tools (CPU, memory, latency, alerts) |
| **Live Show Presets** | ❌ | ✅ 10 tools (save/load, scene presets, emergency stop) |
| **AI Integration** | ❌ | ✅ 9 tools (snapshots, suggestions, MIDI generation) |
| **Audio Analysis** | ❌ | ✅ 8 tools (spectrum, levels, chords, dynamics) |
| **Template System** | ❌ | ✅ 10 tools (session, track, device templates) |
| **Advanced Routing** | ❌ | ✅ 6 tools (side-chain, multi-output, presets) |
| **Automation Enhancement** | ❌ | ✅ 6 tools (presets, templates, batch) |

---

## Use Cases

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

## Roadmap — Upcoming Features (510+ Tools)

### Live Show Control (15 new tools)
- Show clock & timer
- Emergency stop / panic mute
- Backup scene activation
- Scene macros (fire multiple scenes)

### Performance Analytics (12 new tools)
- Session & track statistics
- Mix history tracking
- Performance trends
- CPU/memory history

### Session Management (10 new tools)
- Auto-backup & restore
- Session comparison
- Change history

### Audio/MIDI Presets (12 new tools)
- Reverb, delay, compressor, EQ presets
- Arpeggiator & chord presets

### Video/Lighting (10 new tools)
- Video effect presets
- DMX lighting control
- Lighting scene presets

### AI Enhancement (8 new tools)
- Genre-based mixing suggestions
- Auto gain staging
- Mix optimization
- Sound design assistance

### Advanced Show Control (8 new tools)
- Scene macros
- Backup presets

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
- [New Features Plan](docs/NEW-FEATURES-PLAN.md)

---

## Credits

Inspiration from [AbletonBridge](https://github.com/hidingwill/AbletonBridge) by [hidingwill](https://github.com/hidingwill). See [LICENSE](LICENSE) for details.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
