# Using AbleBridge++ with OpenCode

AbleBridge++ ships a real MCP server (stdio transport), so AI agents like
OpenCode can control Ableton Live directly as tools.

## 1. Install the AbleBridge++ package

From the repo root:

```bash
uv sync        # creates .venv with the ablebridge-plus console command
```

Or after `pip install ablebridge-plus`, the command `ablebridge-plus` is on
your PATH.

## 2. Make sure Ableton is running

The MCP server connects to the **AbleBridgePlus** control surface
(TCP 127.0.0.1:9877) when it starts. If Ableton is closed, tools that touch
Live will report connection errors until it is running.

## 3. Add the MCP server to OpenCode

In `~/.config/opencode/opencode.jsonc` (Windows:
`C:\Users\<you>\.config\opencode\opencode.jsonc`):

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "ablebridge": {
      "type": "local",
      "command": [
        "C:\\path\\to\\.venv\\Scripts\\ablebridge-plus.exe",
        "--transport", "stdio"
      ],
      "enabled": true,
      "timeout": 30000
    }
  }
}
```

Notes:
- `timeout: 30000` gives the 400+ tools time to be fetched on startup
  (the default 5 s is too short).
- Restart OpenCode after editing the config so the MCP server is spawned.

## 4. Try it

In an OpenCode session:

```
use the ablebridge tool get_session_info and tell me the tempo
```

or make something happen:

```
create a MIDI track called "AI Bass", then create a 4-bar clip in slot 0
```

## TCP transport (optional)

For the dashboard or multiple local clients sharing one Ableton connection:

```bash
ablebridge-plus --transport tcp --tcp-port 9891
```

Then in OpenCode config use `"type": "remote", "url": "http://127.0.0.1:9891"`.
