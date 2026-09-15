# Connecting Claude Desktop to AbleBridge++

AbleBridge++ speaks standard MCP over stdio, so Claude Desktop can drive
your Ableton Live session directly from chat.

## 1. Prerequisites

- Ableton Live 11/12 with the **AbleBridgePlus** control surface installed
  (run `install.bat` / `install.sh` from a release, then select
  **AbleBridgePlus** in Preferences → Link/Tempo/MIDI) and Ableton running
- Claude Desktop for Windows or macOS
- Python 3.10+ available at a fixed path

## 2. Edit the config file

Open (create the folders/files if missing):

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add:

```json
{
  "mcpServers": {
    "ablebridge": {
      "command": "python",
      "args": [
        "C:/path/to/ablebridge-dev/mcp_stdio_launcher.py",
        "--transport", "stdio"
      ]
    }
  }
}
```

Notes:

- Use **forward slashes** in JSON paths, even on Windows
- Replace `C:/path/to/ablebridge-dev` with where you installed the repo,
  or a pip install location if you installed the `ablebridge-plus` package
  (then `command` can be `ablebridge-plus` with args `["--transport","stdio"]`)
- On macOS, `command` may need the absolute interpreter path
  (find it with `which python3`)

## 3. Restart Claude Desktop

Quit fully (system tray → Quit, not just the window) and reopen. You should
see a tools icon (hammer/🔌) — AbleBridge++ exposes 448 tools.

## 4. Try it

- "What's the tempo and how many tracks are in my Ableton session?"
- "Create a MIDI track called AI Bass and generate a 4-bar acid bassline in F# minor"
- "Run the doctor — is everything healthy?"
- "Build a song skeleton: intro 4 bars, verse 8, chorus 8 in D minor at 96 BPM"

## Troubleshooting

| Symptom | Fix |
|---|---|
| No tools icon | Check the config file is valid JSON (no trailing commas) |
| Tools exist but errors mention connection | Ableton isn't running or **AbleBridgePlus** isn't selected as a control surface |
| Timeouts on first use | First tool call connects to Ableton; later calls are fast |
| Server log | Claude Desktop: `~/Library/Logs/Claude/mcp*.log` (macOS), `%APPDATA%\Claude\logs` (Windows) |
| Diagnose startup stalls | Set env `ABLEBRIDGE_TRACE=1` on the server entry; the launcher writes `%TEMP%/ablebridge_mcp_trace.log` |

OpenCode users: see [OPENCODE.md](OPENCODE.md) — same server, different client config.
