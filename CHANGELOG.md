# Changelog

All notable changes to AbleBridge++ will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-09-15

### Added
- **MCP transports** — AI clients can now actually connect:
  - `stdio` (default): newline-delimited JSON-RPC on stdin/stdout for OpenCode, Claude Desktop, and any MCP client
  - `tcp`: per-connection JSON-RPC on `127.0.0.1:9891` for the dashboard and multiple local clients
  - `python -m MCP_Server.server --transport stdio|tcp --tcp-port N`
- `get_browser_cache_status` tool to monitor background browser scans

### Fixed
- **Every tool now advertises its real parameters**: input schemas are derived from function signatures (the source of truth), with hand-written param descriptions merged in — fixes 167 tools that clients could not call correctly
- **Connection stability**: handler-level errors no longer tear down the shared Ableton socket (introduced `CommandError`), eliminating cascading "Could not connect" failures after any error
- **Browser cache refresh no longer blocks**: `refresh_browser_cache` runs the scan in a background thread and returns immediately (was a multi-minute synchronous block)
- **Duplicate tool names**: `start/stop_song_timer` and `get_song_timings` existed twice (show clock vs performance analytics) and silently overwrote each other; analytics variants renamed to `start/stop_performance_timer` and `get_performance_timings`
- `get_arrangement_suggestions` accepts sections as strings or dicts (crashed on strings)
- Added missing `psutil` dependency (`get_memory_usage` crashed without it)
- Remote script: fixed absolute imports that prevented the control surface from loading under its installed folder name (`EnhancedAbletonBridge`)

### Improved
- Systematic test sweep against live Ableton: **154 → 211 tools passing, 0 exceptions, 0 timeouts** (421 tools registered)
- Test harness creates a real MIDI clip (on a dynamically discovered MIDI track) so clip tools exercise real content

## [0.3.0] - 2026-09-14

### Changed
- **Renamed project** from "Enhanced AbletonBridge" to "AbleBridge++"
  - Updated all references across codebase
  - Cleaner, more memorable name

### Added
- **Live Show Control** (15 tools)
  - Show clock & timer
  - Emergency stop / panic mute
  - Backup scene activation
  - Scene macros
- **Performance Analytics** (12 tools)
  - Session & track statistics
  - Mix history tracking
  - CPU/memory history
- **Session Management** (10 tools)
  - Auto-backup & restore
  - Session comparison
- **Audio/MIDI Presets** (12 tools)
  - Reverb, delay, compressor, EQ presets
  - Arpeggiator & chord presets
- **Video/Lighting** (10 tools)
  - Video effect presets
  - DMX lighting control
- **AI Enhancement** (8 tools)
  - Genre-based mixing suggestions
  - Auto gain staging
- **Advanced Show Control** (8 tools)
  - Scene macros
  - Backup presets

## [0.3.0] - 2026-09-14

### Added
- **Full core toolset port** from original AbletonBridge (293 new-style tools)
  - Clips (56), Session (51), M4L Bridge (40), Tracks (29), Snapshots (19)
  - Creative (17), Arrangement (17), Mixer (13), Browser (12), Automation (12)
  - Workflows (10), Scenes (10), MIDI CC (5), Grid (2)
- **Live Show Control categories** (from the 75-tool roadmap)
  - Emergency control (5): `emergency_stop`, `panic_mute`, `panic_unmute`, `activate_backup_scene`, `get_emergency_status`
  - Performance analytics (10): session/track stats, trends, peak/average levels, export report
  - Session backup (4): `backup_session`, `restore_session`, `list_backups`, `delete_backup`
  - Audio presets (14): reverb, delay, compressor, EQ save/load
  - Video/Lighting (10): video presets, transitions, DMX channel control, lighting scenes
  - AI enhancement (5): genre suggestions, auto gain staging, mix optimization, sound design help
  - Scene macros (4): create/fire/delete/list scene macros
  - Backup presets (4): save/load/activate backup presets
- **Browser cache** — BFS scan of Ableton's browser tree, disk cache (gzip), instant search, URI resolution for samples/devices
- **Robust connection layer** — sync TCP with newline-delimited JSON, automatic retry/reconnect, command delay tiers, per-command timeouts
- **Shared module-level state** (`MCP_Server.state`) — connections, stores, browser cache, M4L ping cache
- **Tests** — 29 validation tests (all passing)

### Changed
- Tool registration now supports both `register_tools(mcp)` modules and `@tool()` decorators via a FastMCP-compatible adapter
- `requires-python` >= 3.10 (mcp package requirement)
- `mcp<2` pinned (v1 API — FastMCP import)
- Server now registers **417 tools** (verified via `tools/list`)

### Fixed
- Server failed to boot: missing connection accessors, validation aliases, browser cache functions, state attributes, command tables
- `tool()` decorator rejected `inputSchema` keyword
- `get_m4l_status` missing from dashboard
- `_m4l_batch_set_params` missing from devices

---

## [0.2.1] - 2026-09-14

### Fixed
- **Remote Script loading in Ableton Live 12.4.1**
  - Renamed class from `AbletonBridge` to `AbleBridgePP` to avoid conflict with original
  - Fixed Unicode encoding corruption in `__init__.py` (em-dash mojibake `â??` → ASCII `-`)
  - Added missing `_helpers.py` handler module
  - Installation now works from User Library: `Documents/Ableton/User Library/Remote Scripts/AbleBridge++`

### Changed
- Log messages now show "AbleBridge++" instead of "AbletonBridge"
- `create_instance()` returns `AbleBridgePP` instance

## [0.2.0] - 2026-09-13

### Added
- **MIDI CC Plugin Control** (PR #8 from original AbletonBridge)
  - 5 new tools: `set_plugin_parameter_cc`, `get_cc_map`, `list_cc_maps`, `assign_cc_channel`, `send_raw_cc`
  - 100 MIDI CC maps: 45 Arturia V Collection + 55 NI Komplete Collector's Edition
  - Files: `MCP_Server/tools/midi_cc.py`, `midi_cc/*.json`
- **track_type Support** (PR #14 from original AbletonBridge)
  - Load devices onto master and return tracks via `load_instrument_or_effect(track_type="master")`
  - Files: `MCP_Server/tools/devices.py`, `AbletonBridge_Remote_Script/handlers/browser.py`
- **Extensions SDK Bridge** (PR #11 from original AbletonBridge)
  - Third parameter transport tier (M4L → _Framework → SDK)
  - Requires Live 12.4.5+ Suite + Node.js
  - Files: `MCP_Server/connections/extensions_sdk.py`
- **Show Clock Tool**
  - Show timer and clock display
  - Files: `MCP_Server/tools/show_clock.py`
- **Tests**
  - Validation tests
  - Files: `tests/test_validation.py`
- **Examples**
  - Usage examples
  - Files: `examples/README.md`
- **M4L Device README**
  - Files: `M4L_Device/README.md`
- **Release Infrastructure**
  - GitHub Actions release workflow
  - Windows installer (`release/install.bat`)
  - macOS/Linux installer (`release/install.sh`)
  - Python package config (`pyproject.toml`)
  - Files: `.github/workflows/release.yml`, `release/*`

### Changed
- Updated README with 450+ tool count
- Updated comparison table with new features
- Moved Roadmap section up in README
- Moved Quick Install section down in README
- Description now says "MCP bridge connecting AI/LLM tools to Ableton Live"
- Author changed to "Sajan Maharjan"
- Wording changed to "Inspiration from AbletonBridge by hidingwill"

### Fixed
- CS-80 Brilliance CC collision (CC 23 → CC 81) in Arturia V Collection maps
- Device iteration in `_get_plugin_name_from_track()` now iterates all devices

## [0.1.0] - 2026-09-13

### Added
- Core MCP Server architecture (from AbletonBridge)
- TCP connection to Ableton Remote Script
- UDP connection for real-time updates
- M4L Bridge integration
- Basic tool set (tracks, clips, devices, mixer, browser)

### Enhanced
- Routing channels exposure in `get_track_routing`
- Added `available_input_routing_channels` to response
- Added `available_output_routing_channels` to response

### Added (New Tools)
- MIDI mapping tools (get, create, delete, save/load)
- Plugin management tools (scan, list, configure, presets)
- Video routing tools for Videosync2
- Setlist management tools for AbleSet
- Performance monitoring tools (CPU, memory, latency)
- Quick presets tools for live shows
- AI integration tools (snapshots, suggestions)
- Audio analysis tools (spectrum, levels, chords)
- Template system tools
- Advanced routing tools (side-chain, multi-output)
- Automation enhancement tools

## [0.0.1] - 2026-09-13

### Added
- Project planning and documentation
- Feature roadmap
- Memory file for project tracking

---

## Version History

- **0.2.0** — Added MIDI CC maps, track_type support, Extensions SDK, show clock, tests, release infrastructure
- **0.1.0** — First working release with core features and 10 enhanced tool categories
- **0.0.1** — Initial planning and documentation

## Upgrade Guide

### From 0.1.0 to 0.2.0
1. Pull latest changes: `git pull origin master`
2. Run `uv sync` to update dependencies
3. Install MIDI CC dependencies: `pip install mido python-rtmidi`
4. Copy updated Remote Script to Ableton
5. Restart Ableton Live
6. Restart MCP Server

### From 0.0.1 to 0.1.0
1. Pull latest changes
2. Run `uv sync` to update dependencies
3. Copy Remote Script to Ableton
4. Restart Ableton Live
5. Restart MCP Server

## Known Issues

- Grouping tracks requires manual UI interaction (Ableton limitation)
- Some VST/AU plugins may not expose all parameters
- M4L Bridge requires Max for Live to be installed
- Extensions SDK requires Live 12.4.5+ Suite + Node.js
- MIDI CC maps may not cover all plugin parameters

## Future Plans

- LIA plugin integration (when available)
- TouchDesigner integration
- Automated show control
- Multi-DAW support
- Advanced AI features
- 75+ new tools (see docs/NEW-FEATURES-PLAN.md)
