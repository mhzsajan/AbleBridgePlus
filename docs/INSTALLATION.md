# Installation Guide

This guide will walk you through installing AbleBridge++ and getting it up and running.

## Prerequisites

### Required Software
- **Ableton Live** 10, 11, or 12 (Standard or Suite recommended)
- **Python** 3.8 or higher
- **uv** (Python package manager)

### Optional Software
- **Max for Live** (for M4L Bridge features)
- **Videosync2** (for video integration)
- **AbleSet** (for setlist management)

## Step 1: Clone the Repository

```bash
git clone https://github.com/mhzsajan/ablebridge-plus.git
cd ablebridge-plus
```

## Step 2: Install Dependencies

```bash
uv sync
```

This will install all required Python packages.

## Step 3: Copy Remote Script to Ableton

### Windows
1. Copy the `AbleBridgePlus` folder to:
   ```
   Documents/Ableton/User Library/Remote Scripts/
   ```

### macOS
1. Copy the `AbleBridgePlus` folder to:
   ```
   ~/Music/Ableton/User Library/Remote Scripts/
   ```

**Note:** Rename the folder to `AbletonBridge` if you want a simpler name.

## Step 4: Configure Ableton Live

1. Open Ableton Live
2. Go to **Preferences** → **Link, Tempo & MIDI**
3. Under **Control Surface**, select "AbletonBridge"
4. Set **Input** to "AbletonBridge"
5. Set **Output** to "AbletonBridge"
6. Close Preferences

## Step 5: Start the MCP Server

Open a terminal and run:

```bash
uv run python -m MCP_Server.server
```

You should see output indicating the server is running.

## Step 6: Configure Your AI Tool

### For Claude Desktop
Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "abletonbridge": {
      "command": "uv",
      "args": ["run", "python", "-m", "MCP_Server.server"],
      "cwd": "/path/to/ablebridge-plus"
    }
  }
}
```

### For Cursor
Add to your MCP configuration:

```json
{
  "abletonbridge": {
    "command": "uv",
    "args": ["run", "python", "-m", "MCP_Server.server"],
    "cwd": "/path/to/ablebridge-plus"
  }
}
```

### For Claude Code
Add to your MCP configuration:

```json
{
  "abletonbridge": {
    "command": "uv",
    "args": ["run", "python", "-m", "MCP_Server.server"],
    "cwd": "/path/to/ablebridge-plus"
  }
}
```

## Step 7: Test the Connection

1. Start Ableton Live
2. Start the MCP Server
3. Connect your AI tool
4. Try a simple command:
   - "Get all tracks in the session"
   - "What's the current tempo?"

## Troubleshooting

### Connection Issues

**Problem:** MCP Server can't connect to Ableton
**Solution:**
1. Make sure Ableton is running
2. Make sure the Remote Script is properly installed
3. Check that the Control Surface is selected in Ableton preferences
4. Restart Ableton and the MCP Server

**Problem:** M4L Bridge not working
**Solution:**
1. Make sure Max for Live is installed
2. Load the M4L Device onto any track
3. Check that M4L is connected (use `m4l_status` tool)

### Performance Issues

**Problem:** High latency
**Solution:**
1. Close unnecessary applications
2. Reduce buffer size in Ableton preferences
3. Use UDP for real-time parameter updates

**Problem:** CPU usage high
**Solution:**
1. Check which tracks/devices are using CPU
2. Freeze or flatten tracks with heavy plugins
3. Reduce the number of active devices

### Routing Issues

**Problem:** Can't see audio interface channels
**Solution:**
1. Make sure your audio interface is connected
2. Check Ableton's audio preferences
3. Use `get_track_routing` to see available channels

**Problem:** Can't set routing
**Solution:**
1. Use `get_track_routing` first to see available options
2. Use exact display names from the available options
3. Set routing type before channel (channels depend on type)

## Next Steps

Once installed, check out:
- [Features](FEATURES.md) - Complete feature list
- [API Reference](API.md) - Detailed API documentation
- [Examples](EXAMPLES.md) - Usage examples
- [Tutorials](TUTORIALS/) - Step-by-step guides

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Search existing issues on GitHub
3. Create a new issue with detailed information
4. Join the community Discord (link in README)
