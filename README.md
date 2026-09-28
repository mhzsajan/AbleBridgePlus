# AbleBridgePlus

**Control Ableton Live by talking to it.**

[![Release](https://img.shields.io/github/v/release/mhzsajan/AbleBridgePlus)](https://github.com/mhzsajan/AbleBridgePlus/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests: 159 passing](https://img.shields.io/badge/tests-159%20passing-brightgreen.svg)](https://github.com/mhzsajan/AbleBridgePlus/actions)
[![Ableton Live 11+](https://img.shields.io/badge/ableton-Live%2011%2B-orange.svg)](https://www.ableton.com/en/live/)

A free, open-source [MCP](https://modelcontextprotocol.io/) server that connects any
AI assistant — Claude, OpenCode, Cursor, anything MCP-compatible — to Ableton Live.
Describe what you want in plain language; the AI works inside Live through its
official scripting API.

**475 tools** · works with the AI you already use · MIT licensed · runs entirely
locally

📄 **[Complete tool reference — all 475 tools](docs/FEATURES.md)**

---

## Quick start

**You need:** Ableton Live 11 or 12 · Python 3.10+ · an MCP-capable AI client

### 1. Install

```bash
git clone https://github.com/mhzsajan/AbleBridgePlus.git
cd AbleBridgePlus
uv sync                      # or: pip install -e .
```

### 2. Put the script inside Live

```bash
# from a GitHub release (recommended):
#   Windows     → unzip ablebridge-windows.zip, run install.bat
#   macOS/Linux → untar ablebridge-linux.tar.gz, ./install.sh

# or copy manually:
#   Windows: %USERPROFILE%\Documents\Ableton\User Library\Remote Scripts\
#   macOS:   ~/Music/Ableton/User Library/Remote Scripts/
```

Then in Ableton: **Preferences → Link, Tempo & MIDI → Control Surface →
AbleBridgePlus**. Restart Live if it was already open.

### 3. Connect your AI client

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

### 4. Check it works

Ask your AI: **"run the doctor"**

`doctor` reports connection state, script-version drift, port conflicts and cache
staleness in plain language, each with a suggested fix.

<details>
<summary>More ways to verify (optional)</summary>

```bash
# 159 unit + replay tests — no Ableton required
uv run --with pytest pytest tests/ -q

# every module imports cleanly
python scripts/check_imports.py

# TCP mode with a web dashboard on :9880
AbleBridgePlus --transport tcp --tcp-port 9891
```

</details>

Guides: [OpenCode](docs/OPENCODE.md) · [Claude Desktop](docs/CLAUDE_DESKTOP.md) ·
[Installation](docs/INSTALLATION.md)

---

## What you can actually ask it

### "Make me a track"

> *"produce a demo: energetic 128 BPM house in G minor"*

Sets the tempo, builds Intro / Verse / Chorus / Drop scenes, and writes chords,
bassline, drums and a lead hook — all in key. Every change is checkpointed first,
so a single restore takes it all back.

### "Turn what I just played into a clip"

> *"turn what I hummed on my MIDI keyboard into a full clip"*

Captures your playing, quantizes the timing, and adds matching chord pads
underneath in the right key.

### "What's this sample?"

> *"what key and BPM is that sample on track 3?"*

Runs real DSP on the audio — Goertzel chroma against Krumhansl profiles, onset
autocorrelation for tempo — and reports key, BPM and a confidence value. It can
then convert the audio to playable MIDI as melody, chords or drums.

### "Do any of my tracks clash?"

> *"do any of my tracks clash with each other?"*

Finds tracks sharing frequency range at similar pan, and suggests concrete fixes:
pan one away, EQ the collision, or duck a few dB.

### "Keep my computer fast"

> *"Ableton is getting heavy, freeze what I don't need"*

Finds the most device-heavy currently-playing tracks, freezes them, then verifies
the result.

### "Remember how I like things"

> *"remember I always work at 124 BPM in F# minor"*

Persists it to disk. Tomorrow's session starts with your taste loaded. Ask *"what
did you change today?"* any time — it keeps an automatic journal of every
modification it made.

### "Run my live show"

> *"fire scene 5, then automatically go to the next scene every 16 bars"*

Hands-free scene sequencing with per-section tempo. Plus one-command **emergency
stop**, **panic mute** and **session backups**.

…and the everyday work: create tracks and clips, edit MIDI notes, warp and
quantize, write automation, set up sidechain, load any instrument or effect from
the browser, save presets, map MIDI controllers, drive video and DMX lighting, run
timers and setlists. **475 tools** across the whole application.

### What it can't do

Being straight about the limits, because a tool that overpromises is worse than
one that doesn't:

- It **cannot render or export audio** — Live's scripting API doesn't expose that.
- It **cannot hear your speakers** in real time, so it can't judge how a mix
  actually sounds.
- **Key and BPM detection are estimates.** Always confirm by ear.
- The **optional M4L bridge** (for Max for Live device internals) needs a Max
  device loaded; everything else works without it.

---

## How it works

```
┌─────────────────────────────┐
│  AI client (MCP host)       │  Claude Desktop, OpenCode, Cursor, any MCP client
│  sees 475 tools             │
└──────────────┬──────────────┘
               │ MCP over stdio (JSON-RPC) or TCP :9891
               ▼
┌─────────────────────────────┐
│  AbleBridgePlus MCP server  │  Python, stdlib-only DSP, few deps
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

Three layers, and the middle one is the only part that talks to the outside world:

- **Inside Live**, a Remote Script listens on TCP :9877. Ableton's Live Object
  Model is not thread-safe, so every LOM call is dispatched onto Live's main
  thread — the UI never freezes and the session never corrupts.
- **Outside Live**, the MCP server exposes 475 tools over stdio (what MCP clients
  spawn) or TCP :9891. The stdio handshake answers `initialize` in under a second
  and dials Live lazily on first tool call, so client startup is never blocked.
- **Optional M4L bridge** on UDP/OSC :9878–9882 for real-time parameter writes
  into Max for Live devices.

More detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## The safety model

This is the part that matters most when an AI is touching your work.

**It only acts when you ask.** There is no autonomous behaviour.

**Every mutating call is checkpointed first.** Before a tool changes your set,
the server captures its structure, mixer and clip layout. `rollback` restores the
last one; `safe_experiment` wraps a sequence of changes and reverts the whole
thing if any step fails.

**Every change is journalled.** Tool, arguments, outcome and timestamp, appended
to `~/.ablebridge/journal.jsonl`. Ask *"what did you change today?"*.

**Destructive work is reversible by construction.** `produce_idea_from_prompt`
checkpoints before it starts. The restore path refuses to delete tracks from a
snapshot it couldn't fully read, so a flaky connection can never translate into
"delete everything".

**It can only do what a human could do in the UI**, through Live's official
scripting API.

---

## What's inside

| Area | Tools | Highlights |
|---|--:|---|
| Session & transport | 61 | playback, tempo, loop, scenes, record, quantization settings |
| Clips | 56 | create / edit / fire, notes, warp modes, quantize, launch modes |
| M4L bridge | 40 | hidden device params, rack chains, batch set, chunked discovery |
| Tracks | 29 | create, route, group, freeze, arm, color, fold |
| Snapshots | 19 | device + session snapshots, morph, compare |
| Creative & grid | 19 | progressions, drum patterns, Euclidean rhythms, polyrhythms |
| Arrangement | 17 | clip moves, time edits, locators, automation lanes |
| Show control | 17 | emergency stop, panic mute, session backup, scene macros |
| Video & lighting | 16 | Videosync2 timeline automation, Spout, DMX scenes |
| Analytics | 16 | CPU / memory / latency trends, exportable reports |
| Setlist & clock | 24 | song lists, transitions, countdowns and timers |
| MIDI | 11 | controller mappings, 100+ plugin CC maps (NI, Arturia) |
| Browser | 12 | cached tree, instant search, URI loading |
| Presets & templates | 32 | reverb / delay / comp / EQ, session / track / device templates |

Plus the headline tools that don't fit a category:

| Tool | What it does |
|---|---|
| `produce_idea_from_prompt` | End-to-end fault-tolerant demo generation from one sentence |
| `build_song_skeleton` | Scenes + chords + bass + drums laid out in key |
| `analyze_audio_key_bpm` | Real DSP key/tempo detection with a confidence value |
| `audio_clip_to_midi` | Converts audio to playable melody, chords or drums (Live 12) |
| `find_mix_clashes` | Frequency-overlap and masking analysis across tracks |
| `get_project_context` | The whole session map in one call |
| `doctor` | Health check with plain-language fixes |
| `create_checkpoint` / `rollback` | Named snapshots and one-step revert |
| `match_reference_track` | Match your mix to a reference track |
| `hum_to_clip` | Turns hummed input into a quantised clip with harmony |

*Counts are the live `tools/list` output.*

---

## Recent release

### v0.8.0 — correctness and safety pass

A systematic audit of the transport, tool-dispatch, checkpoint and generative
layers found **20 shipped defects**. The serious ones:

- `build_song_skeleton` read a `track_count` key that `get_all_tracks_info` never
  returns, so it renamed your **first three tracks** to Chords/Bass/Drums.
- `restore()` treated a *failed* snapshot as a snapshot of an empty set and
  **deleted every track in the session**.
- `panic_mute` reported `"Muted 3 tracks"` and muted nothing — the module
  imported no Ableton connection at all.
- A JSON-RPC batch frame **killed the server process**.
- `V7` built Gmaj7, and `quantize_to_scale` flattened every sharp note downward.

All fixed and pinned by 50 new regression tests written to fail against the old
code (159 total).

<details>
<summary>Full v0.8.0 notes — all 20 defects</summary>

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
  back a tool that emptied 12 clips left 12 *empty* clips behind.
- 32 mutating tools (`crop_clip`, `insert_silence`, `humanize_notes`,
  `load_instrument_or_effect`, all `load_*`, …) matched no mutation pattern, so
  they got neither a checkpoint nor a journal entry. Coverage is now an explicit
  structural / journal-only split.
- The change journal recorded **empty arguments for every mutation** — it sliced
  `args[1:]` for positional dispatch, but the dispatcher calls tools with
  keywords, so `args` was always `()`.
- `rollback(steps_back=0)` computed `-abs(0) == 0` and restored the **oldest**
  checkpoint in the ring.
- `create_checkpoint` silently replaced an existing named checkpoint, moving your
  restore point between creating it and using it. It now refuses unless you pass
  `overwrite=True`.
- Auto-checkpoint now runs *inside* the connection gate, and a snapshot is
  rejected outright if its capture was incomplete.

**MCP protocol conformance**

- A JSON-RPC **batch** (`[{…},{…}]`) or any non-object frame — all valid JSON —
  raised `AttributeError` out of the stdio read loop and **killed the server
  process**. Now answered with `-32600`.
- `{"id": null}` got no response, so a client blocked until its own timeout.
- Bad tool arguments came back as a **successful** result whose text happened to
  contain a Python `TypeError`. Missing, unknown and mistyped arguments are now
  `-32602`, naming the offending parameter.
- `ping` returned `-32601`, which made healthy clients think the server was dead.
- `resources/list` returned an object carrying `uriTemplate` and no `uri`.
- `initialize` ignored `params` and hardcoded a protocol version. The version is
  now single-sourced from `MCP_Server/version.py` — one process previously
  reported 0.3.0, 0.5.0 and 0.7.0.
- `state.py` printed a cache warning to **stdout**, which in stdio mode *is* the
  protocol channel; a corrupt cache file made the client declare the server
  broken.
- Schema reconciliation discarded every `enum`, `default`, `minimum`, `maximum`
  and `items` a module had declared (7 enums were being lost).

**Transport robustness**

- The Ableton liveness probe called `settimeout(1.0)` and never reverted it, so
  the next `sendall` inherited a 1-second write deadline and could abort
  part-way through a large payload — silently truncating commands that are
  deliberately never retried.
- `receive_full_response` had no wall-clock deadline, so a peer dribbling bytes
  could hold the socket lock indefinitely and stall every tool.
- It also decoded each `recv` chunk as UTF-8 independently, corrupting any
  multi-byte character that straddled a packet boundary.
- One malformed JSON response was classified as a transport failure and tore down
  a healthy socket.
- A tool timeout released the connection gate while the abandoned worker thread
  was still writing to Ableton, so the agent's retry interleaved with the
  original call.

**Generative correctness**

- Two hand-rolled copies of Björklund's algorithm had drifted apart; one emitted
  `10101011` where the tresillo is `10110110`. Replaced with one shared
  Bresenham implementation, verified for length and hit count across every
  `(steps, pulses)` pair up to 24.
- `V7` built a **major** 7th (Gmaj7) instead of a dominant 7th.
- `quantize_to_scale` snapped every out-of-scale note **downward** (ties always
  resolved low), so quantising a sharp melody transposed it flat by a semitone.
- Drum swing flagged the on-beat 16ths and left the actual 8th-note offbeats
  straight, so hi-hats never swung.
- `root_fifth` basslines emitted an unclamped pitch, collapsing into a semitone
  shuffle near the top of the range.
- `generate_euclidean_rhythm` accepted, documented and then ignored
  `clip_length`.
- `get_arrangement_overview` divided by the time-signature numerator instead of
  the bar length, reporting 2× too few bars in 7/8 and 2× too many in 6/8.

**Known limitations that remain**

- 127 legacy `@tool(...)` tools still bypass the semaphore, the per-tool timeout
  and the unified error envelope, and they block the event loop because they are
  `async def` performing synchronous I/O.
- ~196 of 475 tool names have a >0.80-similarity sibling (e.g. `freeze_track` /
  `unfreeze_track`, and `_m4l`-suffixed duplicates). `tools/list` is a single
  ~220 KB message with no cursor pagination.
- `humanize_notes`, `transform_notes` and `quantize_to_scale` still delete a
  clip's notes and write them back, which drops Live 11+ per-note properties
  (probability, velocity deviation, release velocity).
- The remote script's main-thread callback has a hardcoded 10 s timeout, which
  the client's 30 s/60 s slow-command table can never exceed — so `freeze_track`,
  `load_sample`, `unfreeze_track`, `load_instrument_or_effect` and
  `audio_to_midi` cannot report success even when they work.

</details>

Full history: [CHANGELOG.md](CHANGELOG.md)

---

## FAQ

**Does it modify my music without asking?**
No. The AI only acts when you tell it to. Risky operations auto-checkpoint first,
and every modification is journalled.

**Does it need internet?**
No. Everything runs locally between the AI client, the server and Live.

**Which Live versions?**
Live 11+ for core features. Live 12 is required for audio→MIDI conversion. The
optional M4L bridge needs a Max for Live device (included in `M4L_Device/`).

**Which AI clients work?**
Anything that speaks MCP — Claude Desktop, OpenCode, Cursor, and others. It uses
the open standard, not a vendor API.

**Is my project safe?**
The bridge talks to Live's official scripting API and can only do what a human
could do in the UI. Checkpoints and the change journal make experimentation
reversible.

---

## Documentation

| | |
|---|---|
| [docs/FEATURES.md](docs/FEATURES.md) | All 475 tools, organised by what they do |
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | Full install guide |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Protocol and threading design |
| [docs/OPENCODE.md](docs/OPENCODE.md) | OpenCode setup + troubleshooting |
| [docs/CLAUDE_DESKTOP.md](docs/CLAUDE_DESKTOP.md) | Claude Desktop setup + troubleshooting |
| [docs/ROADMAP.md](docs/ROADMAP.md) | What's planned |

## Roadmap

- Deeper arrangement editing (tempo track, automation breakpoints)
- Session comparison & richer change history
- TouchDesigner integration
- Multi-DAW support (experiment)

---

## Credits

AbleBridgePlus is built and maintained by **Sajan Maharjan**, on the foundation
of [AbletonBridge](https://github.com/hidingwill/AbletonBridge) by
**hidingwill**.

## License

MIT — see [LICENSE](LICENSE).
