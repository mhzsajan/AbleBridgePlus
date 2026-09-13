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

### Core Features (from AbletonBridge)
- **MCP Server** — Model Context Protocol server for AI integration
- **TCP Connection** — Remote Script communication with Ableton
- **UDP Connection** — Real-time parameter updates
- **M4L Bridge** — Access hidden parameters and rack internals
- **340+ Tools** — Comprehensive Ableton control

### Enhanced Features (Our Additions)
- **Routing Channels** — Expose all available audio interface channels
- **MIDI Mapping** — Tools for MIDI controller integration
- **Plugin Management** — Scan, configure, and manage VST/AU plugins
- **Video Integration** — Videosync2 support for live visuals
- **Setlist Management** — AbleSet integration for live shows
- **Performance Monitoring** — CPU/memory usage tracking
- **Live Show Control** — Presets, quick scene fire, emergency stop
- **AI Integration** — Session snapshots, smart suggestions
- **Audio Analysis** — Spectrum, frequency, chord detection
- **Template System** — Save/load session/track/device templates
- **Advanced Routing** — Side-chain, multi-output, presets
- **Automation Enhancement** — Presets, templates, batch operations

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
