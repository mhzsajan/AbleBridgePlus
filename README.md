# AbleBridge++

MCP bridge connecting AI/LLM tools to Ableton Live, enhanced for live show performances. **417 tools registered** for AI-assisted music production and real-time show control.

**By Sajan Maharjan**  
*Inspiration from [AbletonBridge](https://github.com/hidingwill/AbletonBridge) by [hidingwill](https://github.com/hidingwill)*

[![Release](https://img.shields.io/github/v/release/mhzsajan/ablebridge-dev)](https://github.com/mhzsajan/ablebridge-dev/releases)
[![License](https://img.shields.io/github/license/mhzsajan/ablebridge-dev)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## What is AbleBridge++?

AbleBridge++ is the next iteration of **Enhanced AbletonBridge** — a Model Context Protocol (MCP) server that lets AI tools (OpenCode, Claude, etc.) control Ableton Live through its Remote Script. It adds the full core toolset from the original AbletonBridge **plus** a complete live-show engineering layer: emergency control, performance analytics, session backup/restore, audio presets, video/lighting, and scene macros.

```
AI Tool (OpenCode, Claude, ...)
        │  MCP Protocol
        ▼
  MCP Server (AbleBridge++)
        │  TCP (9877) / UDP/OSC (9878-9882)
        ▼
  Ableton Live (Remote Script + M4L Bridge)
```

---

## Features

**417 tools** across **15+ categories** for complete Ableton Live control.

| Category | Tools | Description |
|----------|-------|-------------|
| Session & Transport | 61 | Playback, tempo, loops, scenes, recording |
| Clips | 56 | Create, edit, fire, notes, warp, quantize |
| M4L Device Bridge | 40 | Hidden parameters, rack internals, deep LOM |
| Tracks | 29 | Create, route, group, freeze, arm |
| Snapshots | 19 | Device/session snapshots, morph, compare |
| Creative & Grid | 19 | Chord progressions, drum patterns, AI generation |
| Arrangement | 17 | Clip/time editing, automation lanes |
| Mixer | 13 | Volume, pan, sends, crossfader, delay |
| Browser & Search | 12 | Cached browser tree, instant search, URI loading |
| Automation | 12 | Clip/track envelopes, curves, templates |
| Workflows | 10 | Compound multi-step operations |
| Audio Presets | 14 | Reverb, delay, compressor, EQ presets |
| Video / Lighting | 16 | Videosync2, Spout, DMX, lighting scenes |
| Performance Analytics | 16 | CPU/memory/latency, trends, reports |
| Show Clock & Setlist | 24 | Timers, AbleSet integration, quick presets |
| Live Show Control | 17 | Emergency stop, panic mute, session backup, scene macros |
| Templates & Routing | 11 | Session/device templates, side-chain, multi-output |
| MIDI (Mapping + CC) | 11 | Controller maps, 100+ plugin CC maps |
| Plugins & AI | 23 | Plugin scanning, mix suggestions, MIDI generation |

*Counts are the live `tools/list` output of the server — always accurate.*

---

## Enhanced AbletonBridge vs AbleBridge++

AbleBridge++ is what Enhanced AbletonBridge grows into. The table below shows what changed between the two.

| Area | Enhanced AbletonBridge (v0.2.x) | AbleBridge++ (v0.3.0) |
|------|--------------------------------|------------------------|
| **Registered tools** | 450+ (enhanced categories only) | **417 registered** — full core toolset + enhanced + live-show categories |
| **Core toolset** | ❌ Not ported | ✅ Full port: clips (56), session (51), tracks (29), mixer, browser, arrangement, automation, creative, grid, scenes, snapshots, workflows |
| **Tool registration** | Old-style `@tool()` decorators only | ✅ **Hybrid**: new-style `register_tools(mcp)` modules (293 tools) + old-style `@tool()` modules (127) |
| **Connection layer** | Simple async TCP | ✅ **Original sync connection**: newline-delimited JSON, automatic retry/reconnect, command delay tiers (0/50ms/100ms), per-command timeouts |
| **M4L Bridge** | Basic OSC | ✅ Full bridge: hidden params, `_m4l_batch_set_params`, ping cache, version check |
| **Browser cache** | ❌ | ✅ **Instant search**: BFS scan of the browser tree, disk cache (gzip), URI resolution for samples/devices |
| **Emergency control** | ❌ | ✅ emergency_stop, panic_mute, backup scene activation |
| **Performance analytics** | Basic CPU/memory | ✅ Session/track stats, trends, peak/average levels, export reports |
| **Session backup** | ❌ | ✅ backup/restore/list/delete, auto-backup |
| **Audio/MIDI presets** | ❌ | ✅ Reverb, delay, compressor, EQ, arpeggiator, chord presets |
| **Video / Lighting** | Video routing only | ✅ + video presets, transitions, **DMX lighting**, lighting scenes |
| **Scene macros** | ❌ | ✅ create/fire/delete/list scene macros |
| **Backup presets** | ❌ | ✅ save/load/activate backup presets |
| **AI enhancement** | Suggestions only | ✅ Genre suggestions, auto gain staging, mix optimization, sound design help |
| **State management** | Class-based `GlobalState` | ✅ **Module-level shared state** (`MCP_Server.state`) + `GlobalState` — connections, stores, browser cache, M4L ping all shared |
| **Tests** | 0 | ✅ 29 validation tests |
| **Python** | >=3.8 | ✅ >=3.10, `mcp<2` (v1 API) |

---

## Side-by-Side: Original AbletonBridge vs AbleBridge++

| Category | Original AbletonBridge | AbleBridge++ |
|----------|------------------------|--------------|
| **Tool Count** | 353 | 417+ |
| **Tracks** | create, delete, duplicate, group, arm, freeze | + routing channels exposed |
| **Clips** | create, fire, stop, notes, quantize, humanize | + batch operations |
| **Devices** | parameters, presets, snapshots, hidden params | + plugin management, track_type support |
| **Mixer** | volume, pan, mute, solo, sends | + batch set multiple tracks |
| **Browser** | tree, search, load instruments/effects | + plugin scanning, master/return loading, **cached instant search** |
| **Automation** | clip envelopes, track automation, curves | + presets, templates |
| **Creative** | chord progression, bass line, drum patterns | + AI generation |
| **MIDI Mapping** | ❌ | ✅ 6 tools (get, create, delete, save/load) |
| **MIDI CC Control** | ❌ | ✅ 5 tools (100+ maps: NI Komplete + Arturia V Collection) |
| **Plugin Management** | ❌ | ✅ 6 tools (scan, list, configure, presets) |
| **Video Integration** | ❌ | ✅ 16 tools (Videosync2, Spout, DMX, video presets) |
| **Setlist Management** | ❌ | ✅ 8 tools (AbleSet, songs, transitions) |
| **Performance Monitoring** | ❌ | ✅ 16 tools (CPU, memory, latency, trends, reports) |
| **Live Show Presets** | ❌ | ✅ 8 tools (save/load, scene presets) |
| **Emergency Control** | ❌ | ✅ 5 tools (emergency stop, panic mute, backup scene) |
| **AI Integration** | ❌ | ✅ 11 tools (snapshots, suggestions, MIDI generation) |
| **Audio Analysis** | ❌ | ✅ 6 tools (spectrum, levels, chords, dynamics) |
| **Template System** | ❌ | ✅ 7 tools (session, track, device templates) |
| **Advanced Routing** | ❌ | ✅ 4 tools (side-chain, multi-output, presets) |
| **Automation Enhancement** | ❌ | ✅ presets, templates, batch |

---

## Use Cases

| Use Case | Original | Enhanced | AbleBridge++ |
|----------|----------|----------|--------------|
| General Ableton control | ✅ | ✅ | ✅ |
| Live show engineering | ❌ | ✅ | ✅ (emergency + analytics + backups) |
| Video integration | ❌ | ✅ | ✅ (+ DMX lighting) |
| AI-assisted mixing | ❌ | ✅ | ✅ (+ auto gain staging) |
| Plugin management | ❌ | ✅ | ✅ |
| MIDI controller mapping | ❌ | ✅ | ✅ |
| Performance monitoring | ❌ | ✅ | ✅ (+ trends, reports) |
| Setlist management | ❌ | ✅ | ✅ |
| Session backup/restore | ❌ | ❌ | ✅ |

---

## Roadmap

### ✅ Implemented in v0.3.0
- Show clock & timer (8 tools)
- Emergency control (5 tools)
- Session backup/restore (4 tools)
- Performance analytics (10 tools)
- Audio presets (14 tools)
- Video/lighting incl. DMX (16 tools)
- AI enhancement (5 tools)
- Scene macros (4 tools)
- Backup presets (4 tools)

### ⏳ Planned
- Session comparison & change history
- MIDI effect presets (arpeggiator, chord)
- Multi-DAW support
- TouchDesigner integration
- LIA plugin integration (when available)

---

## Quick Install

### From GitHub Releases
```bash
# Windows
install.bat

# macOS/Linux
chmod +x install.sh && ./install.sh
```

### Manual Install
```bash
git clone https://github.com/mhzsajan/ablebridge-dev.git
cd ablebridge-dev
uv sync
```

---

## Setup

1. Copy `AbleBridgePlus` to Ableton's Remote Scripts folder:
   - **Windows:** `Documents/Ableton/User Library/Remote Scripts/`
   - **macOS:** `~/Music/Ableton/User Library/Remote Scripts/`

2. Open Ableton → Preferences → Link, Tempo & MIDI → Select **"AbleBridgePlus"** as Control Surface

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
start_show_clock(tempo=128)
load_live_preset(preset_name="Concert")
fire_scene(scene_index=0)
set_next_song(song_name="Kutu Ma Timi")
emergency_stop()          # stop everything instantly
panic_mute()              # mute all tracks
backup_session()          # snapshot the session before the show
```

### Performance & Analytics
```python
get_cpu_usage()
get_session_stats()
get_performance_trends()
export_performance_report()
```

### Video & Lighting
```python
configure_spout(enabled=True, port=5000)
play_video_clip(track_index=14, clip_index=0)
set_dmx_channel(channel=1, value=255)
save_lighting_scene(name="Verse")
```

### Browser & Search
```python
search_browser(query="Operator")
load_sample(track_index=0, sample_uri="query:UserLibrary#kick.wav")
refresh_browser_cache()   # after installing new packs
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
- "Emergency stop!"
- "Show CPU usage"
- "Back up the session"
- "Search the browser for a nice pad"

---

## Development

```bash
uv sync                    # install dependencies
uv run python -m MCP_Server.server   # run the server
uv run --with pytest pytest tests/   # run tests
python scripts/check_imports.py      # verify every module imports cleanly
```

### Architecture Notes (v0.3.0)

- **Two tool styles coexist**: new-style modules expose `register_tools(mcp)` (decorated with `@mcp.tool()` + `@_tool_handler`) and old-style modules use `@tool(...)`. The server's `_FastMCPAdapter` lets both register into the same `ToolRegistry`.
- **Shared state** lives in `MCP_Server.state` (module-level) — connections, browser cache, stores, M4L ping cache.
- **Browser cache** scans Ableton's browser tree (BFS, depth 3) and persists to `~/.ableton-bridge/browser_cache.json.gz` for instant search.
- **Connections** are synchronous with automatic retry, reconnect, and per-command delay tiers to keep Ableton's main thread stable.

---

## Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Features](docs/FEATURES.md)
- [Architecture](docs/ARCHITECTURE.md)
- [New Features Plan](docs/NEW-FEATURES-PLAN.md)
- [Changelog](CHANGELOG.md)

---

## Credits

Inspiration from [AbletonBridge](https://github.com/hidingwill/AbletonBridge) by [hidingwill](https://github.com/hidingwill). See [LICENSE](LICENSE) for details.

---

## License

MIT License — see [LICENSE](LICENSE) for details.