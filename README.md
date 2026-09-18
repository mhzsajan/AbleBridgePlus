# AbleBridgePlus

**Control Ableton Live by chatting with an AI.**

[![Release](https://img.shields.io/github/v/release/mhzsajan/AbleBridgePlus)](https://github.com/mhzsajan/AbleBridgePlus/releases)
[![License](https://img.shields.io/github/license/mhzsajan/AbleBridgePlus)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-37%20passing-brightgreen.svg)]()

AbleBridgePlus is a free, open-source bridge that connects **AI assistants** (Claude, OpenCode, Cursor, any MCP-compatible tool) to **Ableton Live**. Once connected, you can produce music, fix problems, and run live shows by describing what you want in plain language — the AI does the clicking.

- **468 tools** covering virtually everything in Live
- **Works with your existing AI tools** via the open MCP standard
- **Free and open source** (MIT)

📄 **[Complete tool reference — all 468 tools, organized by what they do](docs/FEATURES.md)**

---

<table>
<tr>
<td align="center" width="50%">

`Built and maintained by`

### **SAJAN MAHARJAN**

<a href="https://github.com/mhzsajan/AbleBridgePlus/issues"><img alt="Issues" src="https://img.shields.io/badge/Report_issue-⭐_Star_&_Suggest-2ea44f?style=flat-square"></a>

</td>
<td align="center" width="50%">

`Inspired by`

### **AbletonBridge**

by [hidingwill](https://github.com/hidingwill)

</td>
</tr>
</table>

---

---

## 🎵 For Musicians — What can it actually do?

Imagine having a producer friend sitting next to you who never gets tired. You talk, they work inside Ableton:

### "Make me a track"
> **You:** *"produce a demo: energetic 128 BPM house in G minor"*

It sets the tempo, builds Intro / Verse / Chorus / Drop scenes, writes the chords, bassline, drums, and a lead hook — each in key, ready to play. Every change is checkpointed first, so one `undo`-style restore takes it all back if you don't like it.

### "Play what I just played"
> **You:** *"turn what I hummed on my MIDI keyboard into a full clip"*

It captures your playing, quantizes the timing, and adds matching chord pads underneath — automatically in the right key.

### "Listen to this audio"
> **You:** *"what key and BPM is that sample on track 3?"*

It analyzes the actual audio (real DSP, not guesswork) and tells you the key, tempo, and confidence. Then it can convert that audio into playable MIDI — melody, chords, or drums.

### "Fix my mix"
> **You:** *"do any of my tracks clash with each other?"*

It checks which tracks occupy the same frequency range with similar pan and suggests fixes: pan one away, EQ the collision, or duck it a few dB.

### "Keep my computer fast"
> **You:** *"Ableton is getting heavy, freeze what I don't need"*

It finds the most device-heavy, currently-playing tracks and freezes them — then verifies.

### "Remember how I like things"
> **You:** *"remember I always work at 124 BPM in F# minor"*

It stores your preferences permanently. Tomorrow's session starts with your taste already loaded. And at any time: *"what did you change today?"* — it keeps an automatic journal of every modification it made.

### "Run my live show"
> **You:** *"fire scene 5, then automatically go to the next scene every 16 bars"*

Hands-free scene sequencing for live sets, with tempo changes per section. Plus one-command **emergency stop**, **panic mute**, and **session backups** — the safety net every performer wishes they had.

### …and all the everyday work
Create tracks and clips, edit MIDI notes, warp and quantize, automate, set up sidechain, load any instrument or effect from the browser, save/load presets, manage MIDI controllers, control video and DMX lighting, run timers and setlists — **468 tools** across the whole app.

**What it can't do (honest limits):** it can't render/export audio (Live's scripting API doesn't expose that), it can't hear your speakers' output in real time, and key/BPM detection is an estimate — always confirm by ear.

---

## 💻 For Developers & Advanced Users

### Architecture

```
┌─────────────────────────────┐
│  AI client (MCP host)       │  Claude Desktop, OpenCode, Cursor, any MCP client
│  sees 468 tools             │
└──────────────┬──────────────┘
               │ MCP over stdio (JSON-RPC) or TCP :9891
               ▼
┌─────────────────────────────┐
│  AbleBridgePlus MCP server  │  Python, stdlib-only DSP, zero heavy deps
│  MCP_Server/                │
└──────────────┬──────────────┘
               │ TCP :9877 (newline-JSON RPC)  ·  UDP/OSC :9878–9882 (realtime, M4L)
               ▼
┌─────────────────────────────┐
│  Ableton Live               │
│  AbleBridgePlus control     │  Remote Script (Python, runs inside Live)
│  surface + optional M4L     │  · schedules all LOM calls on Live's main thread
│  bridge device              │  · optional Max for Live bridge: hidden params,
└─────────────────────────────┘    rack internals, chunked discovery
```

**Key design points**

- **Two registration styles coexist** — new-style modules (`register_tools(mcp)` + `@mcp.tool()` + a central `@_tool_handler` wrapper providing semaphore gating, per-tool timeout, uniform error envelope, and the change-journal hook) and legacy `@tool(...)` modules. `_FastMCPAdapter` registers both into one `ToolRegistry`.
- **Connections**: synchronous TCP with automatic retry/reconnect, drain-on-send, command delay tiers, per-command timeouts. All Live Object Model (LOM) calls are dispatched onto Live's main thread via `schedule_message` — never from background threads.
- **Shared state** lives at module level (`MCP_Server.state`): connections, browser cache, checkpoints, M4L ping cache.
- **Handshake never blocks**: stdio transport answers MCP `initialize` in <1s and connects to Ableton lazily on first tool use.
- **JSON-RPC envelope is spec-correct** — a bug that silently stalled strict clients (OpenCode) was found and fixed; replay tests now lock the wire format in.

### Feature areas (468 tools)

| Area | Highlights |
|---|---|
| Session & transport (61) | playback, tempo, loop, scenes, record, quantization settings |
| Clips (56) | create/edit/fire, notes, warp modes, quantize, launch modes |
| M4L bridge (40) | hidden device params, rack chains, batch set, chunked discovery |
| Tracks (29) | create/route/group/freeze/arm, color, fold |
| Arrangement (17) | clip moves, time edits, locators, automation lanes |
| Creative & grid (19) | progressions, drum patterns, AI generation |
| Snapshots (19) | device/session snapshots, morph, compare |
| **AI Music Toolkit** | `generate_clip_from_prompt`, `build_chord_progression`, `build_bassline_for_progression`, `generate_advanced_drum_pattern` (7 genres + humanize), `build_song_skeleton` |
| **Project Context** | `get_project_context` (whole session map, 1 call), `get_clip_context`, `create/diff/restore_checkpoint` |
| **Doctor & monitoring** | `doctor` (connection, script-version drift, port, cache checks + plain-language fixes), `session_integrity_report`, `watch_session` |
| **Show Autopilot** | timed scene chains, per-step tempo, loops, follows live tempo |
| **Audio Intelligence** | `analyze_audio_key_bpm` (Goertzel chroma + Krumhansl profiles, onset autocorrelation), `audio_clip_to_midi`, `find_mix_clashes`, `hum_to_clip` |
| **Producer Pipeline** | `produce_idea_from_prompt` (fault-tolerant end-to-end), `smart_freeze`, `match_reference_track` |
| **Studio Memory** | persistent preferences (`~/.ablebridge/memory.json`), automatic change journal (`journal.jsonl`), recall with session suggestions |
| Show control (17) | emergency stop, panic mute, session backup, scene macros |
| Setlist & clock (24) | AbleSet-style songs, transitions, timers |
| Video / lighting (16) | Videosync2, Spout, DMX scenes |
| Analytics (16) | CPU/memory/latency, trends, exportable reports |
| MIDI (11) | controller mappings, 100+ plugin CC maps (NI, Arturia) |
| Browser (12) | cached tree, instant search, URI loading |
| Presets & templates (32) | reverb/delay/comp/EQ, session/track/device templates |

*Tool counts are the live `tools/list` output — always accurate.*

### Install

```bash
git clone https://github.com/mhzsajan/AbleBridgePlus.git
cd AbleBridgePlus
uv sync                      # or: pip install -e .
```

Then either run the installer for Live-side files (recommended), or copy manually:

```bash
# from a GitHub release:
#   Windows → unzip, run install.bat
#   macOS/Linux → untar, ./install.sh
# manual: copy the AbleBridgePlus/ folder to:
#   Windows: %USERPROFILE%\Documents\Ableton\User Library\Remote Scripts\
#   macOS:   ~/Music/Ableton/User Library/Remote Scripts\
```

Start Ableton → Preferences → **Link, Tempo & MIDI** → set a Control Surface to **AbleBridgePlus**.

### Connect an AI client

**OpenCode** (`~/.config/opencode/opencode.jsonc`):

```jsonc
"mcp": {
  "ablebridge": {
    "type": "local",
    "command": ["C:/path/to/AbleBridgePlus/.venv/Scripts/AbleBridgePlus.exe", "--transport", "stdio"]
  }
}
```

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ablebridge": {
      "command": "python",
      "args": ["C:/path/to/AbleBridgePlus/mcp_stdio_launcher.py", "--transport", "stdio"]
    }
  }
}
```

Full guides with troubleshooting: [docs/OPENCODE.md](docs/OPENCODE.md) · [docs/CLAUDE_DESKTOP.md](docs/CLAUDE_DESKTOP.md)

**Run manually** (TCP mode, with web dashboard on :9880):

```bash
AbleBridgePlus --transport tcp --tcp-port 9891
```

### Verify

```bash
# 1. Is everything healthy? (connection, script version drift, ports, cache)
#    → ask your AI: "run the doctor"

# 2. Unit + replay tests (no Ableton needed)
uv run --with pytest pytest tests/ -q          # 37 tests

# 3. Full tool sweep against a live Ableton
.venv/Scripts/python scripts/test_tools.py --all

# 4. Every module imports cleanly
python scripts/check_imports.py
```

### Trouble?

Ask your AI to run **`doctor`** — it diagnoses the usual suspects in plain language: Ableton not reachable, control surface not selected, **script/version drift** (installed script older than the server), port conflicts, stale browser cache — each with a suggested fix. Spent debugging time on this bridge drops to near zero.

Full list of every tool: **[docs/FEATURES.md](docs/FEATURES.md)** · Also [docs/INSTALLATION.md](docs/INSTALLATION.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and the [roadmap](docs/ROADMAP.md).

### Version history & maturity

| Version | Milestone |
|---|---|
| v0.3.x | Rename to AbleBridgePlus, JSON-RPC transport fixes, OpenCode integration |
| v0.4.0 | AI Music Toolkit, Project Context Engine, Doctor, Show Autopilot |
| **v0.5.0** | **Audio Intelligence (DSP), Producer Pipeline, Studio Memory, replay-based CI, dashboard** |

Full details: [CHANGELOG.md](CHANGELOG.md)

### Roadmap

- Deeper arrangement editing (tempo track, automation breakpoints)
- Session comparison & richer change history
- TouchDesigner integration
- Multi-DAW support (experiment)

---

## FAQ

**Does it modify my music without asking?**
No — the AI only acts when you ask. Risky operations (producer pipeline) auto-checkpoint first, and the change journal records everything it does.

**Does it need internet?**
No. Everything runs locally between the AI client, the server, and Live.

**Which Live versions?**
Live 11+ for core features. Live 12 required for audio→MIDI conversion. The optional M4L bridge needs a Max for Live device (included in `M4L_Device/`).

**Is my project safe?**
The bridge talks to Live's official scripting API. It can only do what a human could do in the UI — and checkpoints + the change journal make experimentation reversible.

---

## Credits

- Original concept: [AbletonBridge](https://github.com/hidingwill/AbletonBridge) by [hidingwill](https://github.com/hidingwill)
- AbleBridgePlus: **Sajan Maharjan**

## License

MIT — see [LICENSE](LICENSE).
