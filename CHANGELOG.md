# Changelog

All notable changes to Enhanced AbletonBridge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial repository setup
- README with credits to original AbletonBridge
- LICENSE file (MIT)
- CHANGELOG.md

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

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
- MIDI mapping tools (get, create, delete)
- Plugin management tools (scan, list, configure)
- Video routing tools for Videosync2
- Setlist management tools for AbleSet
- Performance monitoring tools (CPU, memory)
- Quick presets tools for live shows

## [0.0.1] - 2026-09-13

### Added
- Project planning and documentation
- Feature roadmap
- Memory file for project tracking

---

## Version History

- **0.1.0** — First working release with core features
- **0.0.1** — Initial planning and documentation

## Upgrade Guide

### From 0.0.1 to 0.1.0
1. Pull latest changes
2. Run `uv sync` to update dependencies
3. Copy updated Remote Script to Ableton
4. Restart Ableton Live
5. Restart MCP Server

## Known Issues

- Grouping tracks requires manual UI interaction (Ableton limitation)
- Some VST/AU plugins may not expose all parameters
- M4L Bridge requires Max for Live to be installed

## Future Plans

- LIA plugin integration (when available)
- TouchDesigner integration
- Automated show control
- Multi-DAW support
- Advanced AI features
