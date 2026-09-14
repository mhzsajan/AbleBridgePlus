# AbleBridge++ Release

This directory contains the release files for AbleBridge++.

## Quick Install

### Windows
1. Download the latest release from [GitHub Releases](https://github.com/mhzsajan/enhanced-abletonbridge/releases)
2. Extract the ZIP file
3. Run `install.bat`
4. Follow the on-screen instructions

### macOS/Linux
1. Download the latest release from [GitHub Releases](https://github.com/mhzsajan/enhanced-abletonbridge/releases)
2. Extract the ZIP file
3. Open terminal and navigate to the extracted directory
4. Run `chmod +x install.sh` to make the script executable
5. Run `./install.sh`
6. Follow the on-screen instructions

## Manual Install

If you prefer to install manually:

### Prerequisites
- Python 3.8+
- uv package manager (`pip install uv`)

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/mhzsajan/enhanced-abletonbridge.git
   cd enhanced-abletonbridge
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Copy `AbletonBridge_Remote_Script` to your Ableton Remote Scripts folder:
   - **Windows:** `Documents/Ableton/User Library/Remote Scripts/`
   - **macOS:** `~/Music/Ableton/User Library/Remote Scripts/`
   - **Linux:** `~/.ableton/User Library/Remote Scripts/`

4. Configure Ableton:
   - Open Ableton Live
   - Go to Preferences → Link, Tempo & MIDI
   - Under "Control Surface", select "AbletonBridge"
   - Set Input and Output to "AbletonBridge"

5. Start the MCP Server:
   ```bash
   uv run python -m MCP_Server.server
   ```

## Files

| File | Description |
|------|-------------|
| `install.bat` | Windows installer script |
| `install.sh` | macOS/Linux installer script |
| `pyproject.toml` | Python project configuration |
| `README.md` | This file |

## Troubleshooting

### Python not found
Make sure Python 3.8+ is installed and added to your PATH.

### uv not found
Install uv with: `pip install uv`

### Ableton not connecting
1. Make sure the Remote Script is in the correct folder
2. Restart Ableton Live
3. Check that "AbletonBridge" is selected as Control Surface

### MCP Server won't start
1. Make sure you're in the correct directory
2. Run `uv sync` to install dependencies
3. Check for error messages in the console

## Support

For issues and questions:
- [GitHub Issues](https://github.com/mhzsajan/enhanced-abletonbridge/issues)
- [Documentation](docs/)
- [README](README.md)

## License

MIT License - see [LICENSE](LICENSE) for details.
