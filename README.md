# AbleBridgePlus

**Control Ableton Live by talking to it.**

[![Release](https://img.shields.io/github/v/release/mhzsajan/AbleBridgePlus)](https://github.com/mhzsajan/AbleBridgePlus/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests: 159 passing](https://img.shields.io/badge/tests-159%20passing-brightgreen.svg)](https://github.com/mhzsajan/AbleBridgePlus/actions)
[![Ableton Live 11+](https://img.shields.io/badge/ableton-Live%2011%2B-orange.svg)](https://www.ableton.com/en/live/)

---

- **Just curious what this is?** Read [What is this?](#what-is-this) and
  [What can I ask it?](#what-can-i-ask-it). That's the whole pitch, no
  technical knowledge needed.
- **Want to try it?** Jump to [Getting started](#getting-started).
- **Building or integrating?** See [How it works](#how-it-works) and
  [What's inside](#whats-inside).

---

## What is this?

Ableton Live is powerful, but it rewards you for clicking. Making a change means
finding the right track, opening the right panel, dragging the right thing.

AbleBridgePlus lets you skip that. You describe what you want, and it does the
work inside Live:

> *"the drums are drowning out the bass — fix the balance"*

It can duck the bass on every kick, rebalance the levels, and tell you exactly
what it changed.

### What is an MCP bridge?

You may have seen tools like this described as "an MCP bridge". Here's what that
actually means, without the jargon.

**The problem.** AI assistants are very good at talking and fairly bad at
*doing*. Ask one to tighten a compressor and it will happily explain how — but
it cannot reach into your computer and turn the knob.

**The fix — MCP.** *Model Context Protocol* is an open standard, agreed on by
several companies, that lets an AI assistant connect to other software. Think of
it as a universal plug. A tool says "here is what I can do, in these words", and
any assistant that speaks the standard can pick it up and use it.

The nice part: you use the assistant you already have. Nothing here is locked to
one AI company. Claude, OpenCode, Cursor and others all work, and you switch
between them freely.

**The bridge.** That's the piece in the middle. Ableton doesn't speak MCP, and
MCP doesn't speak Ableton. This is the translator between them — software that
listens to what the AI wants, then goes and does it in Live through Ableton's
own official controls, exactly as if you'd clicked it yourself.

So the chain is simple:

> **You** → AI assistant → **this bridge** → Ableton Live

You talk. The assistant understands. The bridge does the clicking.

### Do I need to learn anything?

No. You don't memorize commands, and you don't learn 475 tool names. You say what
you want the way you'd say it to a producer sitting next to you. Under the hood
there are 475 operations available across Live — that's a measure of depth, not
something you have to study.

### Is it safe to let an AI touch my music?

Reasonable question. Four things make it safer than it sounds:

- **It only acts when you tell it to.** There's no autonomous behaviour. It waits
  for you.
- **It saves your work first.** Before it changes anything, it takes a snapshot
  of your set — tracks, mixer, arrangement. Change your mind? One word puts it
  back.
- **It keeps a diary.** Every single change it makes is written down: what tool,
  what arguments, what happened, when. Ask *"what did you change today?"* and it
  tells you.
- **It can only do what you could do.** It talks to Live through the same
  official interface a person would use. It has no secret back door into your
  system.

For the bigger operations — generating a whole demo, say — it checkpoints
automatically before it begins. The worst realistic outcome is that you have to
say "undo that".

### Is my music private?

Yes, and this one matters. Everything runs **on your own computer**: the AI
assistant, this bridge, and Ableton. Your project is never uploaded anywhere, and
no account is needed with any AI company to use the bridge itself. Once
installed, it doesn't need an internet connection at all.

It's also free and open source (MIT) — you can read every line of it.

## What can I ask it?

Here's the kind of thing you might actually type.

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

Runs real audio analysis — not a guess — and tells you the key, the tempo, and how
confident it is. It can then turn the audio into editable MIDI notes.

### "Do any of my tracks clash?"

> *"do any of my tracks clash with each other?"*

Finds tracks fighting over the same frequencies at similar positions in the
stereo field, and suggests specific fixes: pan one away, EQ the collision, or
duck one a few dB.

### "Keep my computer fast"

> *"Ableton is getting heavy, freeze what I don't need"*

Finds the tracks that are heaviest right now, flattens them to audio, and checks
the result.

### "Remember how I like things"

> *"remember I always work at 124 BPM in F# minor"*

Stores it permanently. Tomorrow's session starts already knowing. Ask *"what did
you change today?"* any time.

### "Run my live show"

> *"fire scene 5, then automatically go to the next scene every 16 bars"*

Hands-free scene sequencing with per-section tempo changes — plus one-command
**emergency stop**, **panic mute** and **session backups**.

…and the everyday work: create tracks and clips, edit MIDI notes, warp and
quantize, write automation, set up sidechain, load any instrument or effect,
save presets, map MIDI controllers, drive video and DMX lighting, run timers and
setlists.

## What it can't do

Being straight about the limits, because a tool that overpromises is worse than
one that doesn't:

- It **cannot render or export audio** — Ableton doesn't allow that through its
  scripting interface.
- It **cannot hear your speakers** in real time, so it can't tell you how a mix
  actually sounds.
- **Key and BPM detection are estimates.** Always confirm by ear.
- It's built for **Live, not other DAWs**. Logic, Cubase, FL Studio and the rest
  aren't supported.
- Some deeper device controls need an optional extra piece (a Max for Live
  device) — everything important works without it.

---

## Getting started

**You'll need:**

| | |
|---|---|
| **Ableton Live** | 11 or 12 |
| **Python** | 3.10 or newer — one command installs it |
| **An AI assistant** | Claude Desktop, OpenCode, Cursor, or anything that supports MCP |
| **Time** | About 10 minutes, once |

Nothing to buy and no account to create. If you already use an AI assistant, you
already have everything you need.

📄 New to this? **[docs/INSTALLATION.md](docs/INSTALLATION.md)** has screenshots
and troubleshooting for each platform.

### 1. Install

```bash
git clone https://github.com/mhzsajan/AbleBridgePlus.git
cd AbleBridgePlus
uv sync                      # or: pip install -e .
```

### 2. Put the script inside Live

```bash
# from a GitHub release (recommended):
#   Windows     -> unzip the .zip, run install.bat
#   macOS/Linux -> untar the .tar.gz, ./install.sh

# or copy the AbleBridgePlus/ folder by hand:
#   Windows: %USERPROFILE%\Documents\Ableton\
#            User Library\Remote Scripts\
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
    "command": [
      "C:/path/AbleBridgePlus/.venv/Scripts/AbleBridgePlus.exe",
      "--transport", "stdio"
    ]
  }
}
```

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ablebridge": {
      "command": "python",
      "args": [
        "C:/path/AbleBridgePlus/mcp_stdio_launcher.py",
        "--transport", "stdio"
      ]
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
[Installation](docs/INSTALLATION.md) · [All 475 tools](docs/FEATURES.md)

---

## How it works

```
┌────────────────────────────┐
│  AI client (MCP host)      │
│  sees 475 tools            │
└─────────────┬──────────────┘
              │ MCP over stdio, or TCP :9891
              ▼
┌────────────────────────────┐
│  AbleBridgePlus            │
│  MCP server (MCP_Server/)  │
└─────────────┬──────────────┘
              │ TCP :9877  ·  UDP/OSC :9878–9882
              ▼
┌────────────────────────────┐
│  Ableton Live              │
│  Remote Script             │
│  + optional M4L bridge     │
└────────────────────────────┘
```

Three layers, and only the middle one talks to the outside world:

- **Inside Live**, a Remote Script listens on TCP :9877. Ableton's Live Object
  Model is not thread-safe, so every LOM call is dispatched onto Live's main
  thread — the UI never freezes and the session never corrupts. An optional Max
  for Live bridge on UDP/OSC :9878–9882 handles real-time parameter writes.
- **Outside Live**, the MCP server exposes 475 tools over stdio (what MCP clients
  spawn) or TCP :9891 for multiple local clients and the web dashboard. The stdio
  handshake answers `initialize` in under a second and dials Live lazily on the
  first tool call, so client startup is never blocked.
- **DSP is stdlib-only** — key/BPM detection, spectral analysis and loudness
  measurement are implemented in Python with no heavyweight dependencies.

More detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## What's inside

| Area | Tools | Highlights |
|---|--:|---|
| Session & transport | 61 | playback, tempo, loop, scenes, record, quantization settings |
| Clips | 56 | create / edit / fire, notes, warp modes, quantize, launch modes |
| M4L bridge | 40 | hidden device params, rack chains, batch set, chunked discovery |
| Tracks | 29 | create, route, group, freeze, arm, color, fold |
| Presets & templates | 32 | reverb / delay / comp / EQ, session / track / device templates |
| Setlist & clock | 24 | song lists, transitions, countdowns and timers |
| Creative & grid | 19 | progressions, drum patterns, Euclidean rhythms, polyrhythms |
| Snapshots | 19 | device + session snapshots, morph, compare |
| Arrangement | 17 | clip moves, time edits, locators, automation lanes |
| Show control | 17 | emergency stop, panic mute, session backup, scene macros |
| Video & lighting | 16 | Videosync2 timeline automation, Spout, DMX scenes |
| Analytics | 16 | CPU / memory / latency trends, exportable reports |
| MIDI | 11 | controller mappings, 100+ plugin CC maps (NI, Arturia) |
| Browser | 12 | cached tree, instant search, URI loading |

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

**Does it send my music anywhere?**
No. There is no upload, no telemetry and no account. Once installed it works
entirely offline.

**Which Live versions?**
Live 11+ for core features. Live 12 is required for audio→MIDI conversion. The
optional M4L bridge needs a Max for Live device (included in `M4L_Device/`).

**Which AI clients work?**
Anything that speaks MCP — Claude Desktop, OpenCode, Cursor, and others. It uses
the open standard, not a vendor API.

**Can it break or lose my project?**
It talks to Live's official scripting API and can only do what a human could do in
the UI. Checkpoints and the change journal make experimentation reversible. As
with any tool that edits a live project, saving your set is still sensible
practice.

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
