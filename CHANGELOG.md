# Changelog

All notable changes to AbleBridgePlus will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-09-15

### Added — Audio Intelligence ("Ears")
- `analyze_audio_key_bpm` — key + BPM detection of audio samples: Live warp metadata plus server-side DSP (Goertzel chroma with Krumhansl-Schmuckler profiles, onset autocorrelation for tempo). The AI can now *hear* the key it's writing in
- `audio_clip_to_midi` — one-call Live 12 audio->MIDI (melody/harmony/drums) with a report of where the MIDI landed
- `find_mix_clashes` — heuristic frequency/mask clash finder across tracks with suggestions
- `hum_to_clip` — capture what you just played, quantize it, and add chord pads in-key

### Added — Producer Pipeline
- `produce_idea_from_prompt` — one sentence to a playable demo: parses BPM/key/genre, sets tempo, builds skeleton scenes, writes chord/bass/drum/lead clips per scene, checkpoints first, fault-tolerant at every step
- `smart_freeze` — CPU guardian: ranks tracks by device load and playing state, freezes the heaviest (dry-run supported)
- `match_reference_track` — copy a reference track's pan/volume/send levels/device on-off pattern onto a target

### Added — Studio Memory (Taste & Accountability)
- `remember_preference` / `recall_preferences` / `forget_preference` — persistent taste across sessions (~/.ablebridge/memory.json), with session-start suggestions
- Automatic **change journal** — every mutating tool call is recorded to ~/.ablebridge/journal.jsonl; `get_change_journal` answers "what did the AI change?"; `clear_change_journal` resets

### Added — Platform
- **Replay-based CI tests** (tests/test_replay.py): the full tool layer runs against recorded responses — no Ableton needed in CI
- **Web dashboard now starts in TCP mode** with a live `/api/session` endpoint (tempo, transport, per-track levels)
- Claude Desktop setup guide (docs/CLAUDE_DESKTOP.md)
- Remote script: `get_clip_file_path`, `get_track_sends` (read-only) and a SCRIPT_VERSION marker the doctor uses for drift detection

### Fixed
- `produce_idea_from_prompt` called the skeleton tool as a remote handler (wrong layer) — skeleton logic now runs against the live connection
- Note format in the producer lead melody used "start" instead of "start_time"
- Duplicate demo tracks: skeleton now matches the newest MIDI track by name and verifies it accepts MIDI clips
- `get_track_meters` called with an invalid index -1 by smart_freeze

### Verified live
- 448 tools registered; sweep 260 OK, 0 exceptions, 0 timeouts; 37/37 tests
- Key/BPM DSP: A-minor triad -> "A minor" (conf 0.68), 120 BPM clicks -> 121.6
- Full producer pipeline ran against the live set: 7/7 steps, 0 errors, scenes + clips + lead hook created
- Journal, preferences, doctor (version-drift check working), smart_freeze, mix clashes all verified

**Upgrade note:** the remote script changed — reinstall and restart Ableton once; the doctor will confirm version 0.5.0.

## [0.4.0] - 2026-09-15

### Added — AI Music Toolkit
- `generate_clip_from_prompt` — "4-bar acid bassline in F# minor" becomes a real MIDI clip in one call (style presets: acid bass, chords, arp, melody, pluck)
- `build_chord_progression` — genre-aware progressions (pop, jazz, edm, blues, epic) with optional sevenths, auto voice-leading
- `build_bassline_for_progression` — bassline following a chord degree pattern (styles: roots, octave, walking, 808)
- `generate_advanced_drum_pattern` — house/techno/trap/dnb/rock/pop/lofi templates with fills and humanization
- `build_song_skeleton` — "intro 4, verse 8, chorus 8" builds named, colored scenes + clips, ready to produce

### Added — Project Context Engine
- `get_project_context` — the whole session map (tracks, devices, clips, routing, key) in one compact call instead of 20 small ones
- `get_clip_context` — clip name, length, key scale, and note summary in one call
- `create_checkpoint` / `list_checkpoints` / `diff_checkpoint` / `restore_checkpoint` — snapshot the session structure before experimenting, diff after, restore if unwanted

### Added — Doctor & Monitoring
- `doctor` — one-call diagnosis: connection health, control-surface script version drift, port conflicts, browser-cache staleness, with plain-language fixes
- `session_integrity_report` — empty routings, clips on muted tracks, missing devices and other real-world gotchas
- `watch_session` — lightweight monitor of tempo, playing position, CPU, and clip levels the AI can poll

### Added — Show Autopilot
- `start_show_autopilot` / `stop_show_autopilot` / `autopilot_status` — hands-free timed scene sequencing for live sets: fire a scene, auto-advance after N bars (follows live tempo), per-step tempo changes, loop the whole sequence forever or N times

### Fixed
- Autopilot's invalid-JSON error message crashed itself via a str.format brace collision with the JSON example in the message
- `build_song_skeleton` missing json import
- `analyze_arrangement_*` burned ~10s per call probing a silent Max for Live bridge; now probes with a 0.75s timeout (also available to all tools via `m4l.ping(timeout=...)`)
- Test harness: setup phase creates a real MIDI clip on a dynamically discovered track; generators and destructive tools excluded from sweeps; M4L-only tools (need a running Max device) validated separately

### Verified live
- 436 tools registered; sweep 211 -> 224 OK, 0 exceptions, 0 timeouts
- Music generators wrote a real F# minor acid bassline (30 notes) and chord progression into a live Ableton 12 session
- Doctor correctly flagged version drift, port status, and a stale browser cache; autopilot fired scenes and shut down cleanly against the live set

## [0.3.4] - 2026-09-15

### Fixed (critical for MCP clients)
- **JSON-RPC envelope bug**: responses were missing the required `"result"` wrapper, so OpenCode and other strict MCP clients timed out on connect. Both stdio and TCP transports now emit spec-compliant envelopes
- **Instant handshake**: stdio no longer pre-connects to Ableton/M4L before serving — the MCP handshake answers in <1s and Ableton connects lazily on first tool use
- `create_midi_track(-1)` (append at end) crashed on a validation signature mismatch — fixed

### Added
- `mcp_stdio_launcher.py` — absolute-path entry point recommended for MCP client configs (see docs/OPENCODE.md); supports `ABLEBRIDGE_TRACE=1` file tracing for spawn debugging

### Verified end-to-end
- `opencode mcp list` -> `ablebridge connected`
- Chat-driven control of a live Ableton 12 session: session info reads and a MIDI track created from a chat prompt

## [0.3.2] - 2026-09-15

### Renamed
- **Remote script folder is now `AbleBridgePlus`** — this is the name shown in Ableton's Preferences → Link/Tempo/MIDI → Control Surface list (was "AbleBridgePlus")
- Python package renamed to `AbleBridgePlus`; console command `AbleBridgePlus`
- Persistent data directory moved from `~/.AbleBridgePlus` to `~/.ablebridge`
- Installer now removes the legacy `AbleBridgePlus` folder automatically
- Brand string **AbleBridgePlus** is kept in display messages and the dashboard title

### Note
- After upgrading, restart Ableton once and select **AbleBridgePlus** as the control surface (the old entry no longer exists once the old folder is removed)

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
- Remote script: fixed absolute imports that prevented the control surface from loading under its installed folder name (`AbleBridgePlus`)

### Improved
- Systematic test sweep against live Ableton: **154 → 211 tools passing, 0 exceptions, 0 timeouts** (421 tools registered)
- Test harness creates a real MIDI clip (on a dynamically discovered MIDI track) so clip tools exercise real content

## [0.3.0] - 2026-09-14

### Changed
- **Renamed project** from "Enhanced AbletonBridge" to "AbleBridgePlus"
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
  - Renamed class from `AbletonBridge` to `AbleBridgePlus` to avoid conflict with original
  - Fixed Unicode encoding corruption in `__init__.py` (em-dash mojibake `â??` → ASCII `-`)
  - Added missing `_helpers.py` handler module
  - Installation now works from User Library: `Documents/Ableton/User Library/Remote Scripts/AbleBridgePlus`

### Changed
- Log messages now show "AbleBridgePlus" instead of "AbletonBridge"
- `create_instance()` returns `AbleBridgePlus` instance

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
