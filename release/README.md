# AbleBridge++ Release

This directory contains the release files for AbleBridge++ — the MCP bridge for Ableton Live (**417 tools**).

## Quick Install

### Windows
1. Download the latest release from [GitHub Releases](https://github.com/mhzsajan/ablebridge-dev/releases)
2. Extract the ZIP file
3. Run `install.bat`
4. Follow the on-screen instructions

### macOS/Linux
1. Download the latest release from [GitHub Releases](https://github.com/mhzsajan/ablebridge-dev/releases)
2. Extract the ZIP file
3. Open terminal and navigate to the extracted directory
4. Run `chmod +x install.sh`
5. Run `./install.sh`
6. Follow the on-screen instructions

## Manual Install

### Prerequisites
- Python 3.10+
- uv package manager (`pip install uv`)

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/mhzsajan/ablebridge-dev.git
   cd ablebridge-dev
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Copy `AbleBridgePlus` to your Ableton Remote Scripts folder as **`AbleBridgePlus`**:
   - **Windows:** `Documents/Ableton/User Library/Remote Scripts/AbleBridgePlus`
   - **macOS:** `~/Music/Ableton/User Library/Remote Scripts/AbleBridgePlus`
   - **Linux:** `~/.ableton/User Library/Remote Scripts/AbleBridgePlus`

4. Configure Ableton:
   - Open Ableton Live
   - Go to Preferences → Link, Tempo & MIDI
   - Under "Control Surface", select **"AbleBridgePlus"**
   - Set Input and Output to "AbleBridgePlus"

5. Start the MCP Server:
   ```bash
   uv run python -m MCP_Server.server
   ```

## Files

| File | Description |
|------|-------------|
| `install.bat` | Windows installer script |
| `install.sh` | macOS/Linux installer script |
| `README.md` | This file |
| `../CHANGELOG.md` | Full changelog for all versions |

## Troubleshooting

### Python not found
Make sure Python 3.10+ is installed and added to your PATH.

### uv not found
Install uv with: `pip install uv`

### Ableton not connecting
1. Make sure the Remote Script is in the correct folder (`.../Remote Scripts/AbleBridgePlus`)
2. Restart Ableton Live
3. Check that "AbleBridgePlus" is selected as Control Surface

### MCP Server won't start
1. Make sure you're in the correct directory
2. Run `uv sync` to install dependencies
3. Check for error messages in the console

## Support

For issues and questions:
- [GitHub Issues](https://github.com/mhzsajan/ablebridge-dev/issues)
- [Documentation](docs/)
- [README](../README.md)

## License

MIT License — see [LICENSE](../LICENSE) for details.