# Changelog

All notable changes to Enhanced AbletonBridge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-09-14

### Fixed
- **Remote Script loading in Ableton Live 12.4.1**
  - Renamed class from `AbletonBridge` to `EnhancedAbletonBridge` to avoid conflict with original
  - Fixed Unicode encoding corruption in `__init__.py` (em-dash mojibake `â??` → ASCII `-`)
  - Added missing `_helpers.py` handler module
  - Installation now works from User Library: `Documents/Ableton/User Library/Remote Scripts/EnhancedAbletonBridge`

### Changed
- Log messages now show "EnhancedAbletonBridge" instead of "AbletonBridge"
- `create_instance()` returns `EnhancedAbletonBridge` instance

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
