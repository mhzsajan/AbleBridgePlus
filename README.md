# AbleBridgePlus

**Control Ableton Live by chatting with an AI.**

[![Release](https://img.shields.io/github/v/release/mhzsajan/AbleBridgePlus)](https://github.com/mhzsajan/AbleBridgePlus/releases)
[![License](https://img.shields.io/github/license/mhzsajan/AbleBridgePlus)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-37%20passing-brightgreen.svg)]()

AbleBridgePlus is a free, open-source bridge that connects **AI assistants** (Claude, OpenCode, Cursor, any MCP-compatible tool) to **Ableton Live**. Once connected, you can produce music, fix problems, and run live shows by describing what you want in plain language — the AI does the clicking.

- **475 tools** covering virtually everything in Live
- **Works with your existing AI tools** via the open MCP standard
- **Free and open source** (MIT)

📄 **[Complete tool reference — all 475 tools, organized by what they do](docs/FEATURES.md)**

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
Create tracks and clips, edit MIDI notes, warp and quantize, automate, set up sidechain, load any instrument or effect from the browser, save/load presets, manage MIDI controllers, control video and DMX lighting, run timers and setlists — **475 tools** across the whole app.

**What it can't do (honest limits):** it can't render/export audio (Live's scripting API doesn't expose that), it can't hear your speakers' output in real time, and key/BPM detection is an estimate — always confirm by ear.

---

## 💻 For Developers & Advanced Users

### Architecture

```
┌─────────────────────────────┐
│  AI client (MCP host)       │  Claude Desktop, OpenCode, Cursor, any MCP client
│  sees 475 tools             │
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

### Feature areas (475 tools)

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
uv run --with pytest pytest tests/ -q          # 159 tests

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
| v0.5.0 | Audio Intelligence (DSP), Producer Pipeline, Studio Memory, replay-based CI, dashboard |
| v0.6.x | Undo-safe experimentation (checkpoints, rollback, safe_experiment), MCP resources & prompts |
| v0.7 | Spectral engine (Ears v2), loudness / jump-out detection, whole-mix reference matching |
| **v0.8.0** | **Correctness & safety pass — 20 defects fixed, see below** |

Full details: [CHANGELOG.md](CHANGELOG.md)

### v0.8.0 — correctness and safety pass

A full audit of the transport, tool-dispatch, checkpoint and generative layers
found 20 shipped defects. The ones that could lose work or mislead you are fixed
and pinned by regression tests (`tests/test_safety_regressions.py`, 50 tests).

**Set-destroying bugs**

- `build_song_skeleton` / `produce_idea_from_prompt` read a `track_count` key off
  `get_all_tracks_info`, which returns `count`. The lookup always yielded `0`, so
  the tools renamed your **first three tracks** to Chords/Bass/Drums and wrote
  chord clips into them.
- `checkpoints.restore()` treated a snapshot whose capture had *failed* as a
  snapshot of an empty set, and deleted every track in the session. Snapshots now
  carry a `valid` flag; restore refuses to delete anything from an unreadable
  one, and says so in its report.
- `produce_idea_from_prompt`'s checkpoint step imported a symbol that did not
  exist. The `ImportError` was swallowed, so the run created 4 tracks, 4 scenes
  and ~50 clips with no restore point at all.

**Tools that lied about what they did**

- `emergency_stop`, `panic_mute`, `panic_unmute` and `activate_backup_scene` only
  flipped a flag in their own module — the module imported no Ableton connection
  at all. `panic_mute` answered `"Muted 3 tracks"` and muted nothing. They now
  drive Live, report per-item outcomes, and distinguish `*_partial` from success.
  `panic_unmute` restores each track's *prior* mute state rather than
  blanket-unmuting, so a deliberately-killed channel stays killed.
- `doctor`'s M4L check was `bool(x or True)` — permanently healthy. It also
  recommended calling `refresh_browser_cache`, which was registered under the
  name `refresh_browser_cache_tool` (the `__name__` rename happened after
  `@mcp.tool()` had already captured the name), so the suggested fix did not
  exist.

**Undo safety, which was weaker than advertised**

- `restore()` only ever *created* clips — there was no `delete_clip` call and no
  scene deletion, and `report["clips"]["deleted"]` was a dead counter. Rolling
  back a tool that emptied 12 clips left 12 *empty* clips behind. Both
  dimensions are now restored.
- 32 mutating tools (`crop_clip`, `insert_silence`, `humanize_notes`,
  `load_instrument_or_effect`, all `load_*`, …) matched no mutation pattern, so
  they got neither a checkpoint nor a journal entry. Coverage is now explicit:
  a structural-mutation list (checkpointed) plus a journal-only list of cheaper
  tools that shouldn't pay for a 1+N+2 round-trip snapshot.
- The change journal recorded **empty arguments for every mutation** — it sliced
  `args[1:]` for positional dispatch, but the dispatcher calls tools with
  keywords, so `args` was always `()`.
- `rollback(steps_back=0)` computed `-abs(0) == 0` and restored the **oldest**
  checkpoint in the ring. `steps_back` now requires ≥ 1.
- `create_checkpoint` silently replaced an existing named checkpoint, moving
  your restore point between creating it and using it. It now refuses unless you
  pass `overwrite=True`.
- Auto-checkpoint now runs *inside* the connection gate (it could previously
  snapshot a set while another tool's mutation was half applied), and a snapshot
  is rejected outright if its capture was incomplete.

**MCP protocol conformance**

- A JSON-RPC **batch** (`[{…},{…}]`) or any non-object frame — all valid JSON —
  raised `AttributeError` out of the stdio read loop and **killed the server
  process**. Now answered with `-32600`.
- `{"id": null}` got no response, so a client blocked until its own timeout. A
  notification is a request with *no* `id` member; that is now the test.
- Bad tool arguments came back as a **successful** result whose text happened to
  contain a Python `TypeError`. Missing, unknown and mistyped arguments are now
  `-32602`, naming the offending parameter.
- `ping` returned `-32601`, which made healthy clients think the server was dead.
- `resources/list` returned an object carrying `uriTemplate` and no `uri`;
  templates are now served by `resources/templates/list`.
- `initialize` ignored `params` and hardcoded a protocol version. It now
  negotiates, and the version is single-sourced from `MCP_Server/version.py`
  (previously one process reported 0.3.0, 0.5.0 and 0.7.0).
- `state.py` printed a cache warning to **stdout**, which in stdio mode *is* the
  protocol channel — a corrupt cache file made the client declare the server
  broken. Warnings go to stderr, and the cache is written atomically.
- Schema reconciliation discarded every `enum`, `default`, `minimum`, `maximum`
  and `items` a module had declared (7 enums were being lost). All constraints
  now survive, and duplicate tool names are logged instead of silently shadowing.

**Transport robustness**

- The Ableton liveness probe called `settimeout(1.0)` and never reverted it, so
  the next `sendall` inherited a 1-second write deadline and could abort
  part-way through a large payload — silently truncating commands that are
  deliberately never retried.
- `receive_full_response` had no wall-clock deadline, so a peer dribbling bytes
  could hold the socket lock indefinitely and stall every tool.
- It also decoded each `recv` chunk as UTF-8 independently, corrupting any
  multi-byte character that straddled a packet boundary.
- One malformed JSON response was classified as a transport failure and tore
  down a healthy socket.
- A tool timeout released the connection gate while the abandoned worker thread
  was still writing to Ableton, so the agent's retry interleaved with the
  original call. The gate is now held until the worker genuinely stops.

**Generative correctness**

- Two hand-rolled copies of Björklund's algorithm had drifted apart; one emitted
  `10101011` where the tresillo is `10110110`. Replaced with one shared
  Bresenham implementation, verified for length and hit count across every
  `(steps, pulses)` pair up to 24.
- `V7` built a **major** 7th (Gmaj7) instead of a dominant 7th.
- `quantize_to_scale` snapped every out-of-scale note **downward** (ties always
  resolved low), so quantising a sharp melody transposed it flat by a semitone.
  Ties now resolve upward.
- Drum swing flagged the on-beat 16ths and left the actual 8th-note offbeats
  straight, so hi-hats never swung.
- `root_fifth` basslines emitted an unclamped pitch, collapsing into a semitone
  shuffle near the top of the range.
- `generate_euclidean_rhythm` accepted, documented and then ignored
  `clip_length`.
- `get_arrangement_overview` divided by the time-signature numerator instead of
  the bar length, reporting 2× too few bars in 7/8 and 2× too many in 6/8.

**Still worth knowing (deliberately not fixed here)**

- 127 legacy `@tool(...)` tools still bypass the semaphore, the per-tool timeout
  and the unified error envelope, and they block the event loop because they are
  `async def` performing synchronous I/O. Migrating them onto
  `@_tool_handler` is the single largest remaining improvement.
- ~196 of 475 tool names have a >0.80-similarity sibling (e.g. `freeze_track` /
  `unfreeze_track`, and `_m4l`-suffixed duplicates). `tools/list` is a single
  ~220 KB message with no cursor pagination. This measurably degrades agent tool
  selection; grouping or de-duplicating names would help more than any other
  single change.
- `humanize_notes`, `transform_notes` and `quantize_to_scale` still delete a
  clip's notes and write them back. They are now checkpointed and journalled, but
  the rewrite drops Live 11+ per-note properties (probability, velocity
  deviation, release velocity) because `get_clip_notes` doesn't return them.
  They should use `get_notes_extended` / `modify_clip_notes` instead.
- The remote script's main-thread callback has a hardcoded 10 s timeout, which
  the client's 30 s/60 s slow-command table can never exceed — so
  `freeze_track`, `load_sample`, `unfreeze_track`, `load_instrument_or_effect`
  and `audio_to_midi` cannot report success even when they work.

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
