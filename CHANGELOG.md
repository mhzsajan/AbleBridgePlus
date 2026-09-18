# Changelog

All notable changes to AbleBridgePlus will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0] - 2026-09-18 (unreleased)

Starts v0.8 "Collaboration" with the show-navigation layer, built and
live-verified against the real Videosync2 show set (Deepak Bajracharya
& The Rhythm Band — 18 tracks, 56 locators, arrangement-driven).

### Added
- **Show navigation** (6 tools, 462 → 468) — the AI can finally see and
  drive the arrangement locators that organize live shows:
  `list_arrangement_locators`, `jump_to_locator` (index or fuzzy song
  name), `jump_to_next_locator` / `jump_to_prev_locator`,
  `get_current_show_section` ("we're in Man Magan, N bars to SONG END"),
  and `rename_locator`. Fuzzy resolution handles your song-name style:
  exact match first, unique substring second, honest ambiguity errors.
- Read-only `probe_song_locator_surface` handler kept for future LOM
  surface checks.

### Fixed
- **Cue points arrive in creation order, not timeline order** — Live's
  `song.cue_points` Vector is unsorted (found live: a SONG END locator
  far ahead of the timeline sat at index 1). All locator handlers now
  sort by time, so indexes mean *show order*.

### Verified live on the real show set
- 56/56 locators listed in show order; fuzzy jump to "Man Magan" landed
  the playhead at bar 1690 exactly; next-cue walk reported SONG END;
  rename works on Live 12.4.2 (tested + reverted in memory).

## [0.7.1] - 2026-09-18

Closes v0.7 "Ears v2": downbeat-aware BPM refinement is live, and the
end-to-end test exposed (and fixed) two bugs that had silently crippled
`analyze_audio_key_bpm` since v0.5.

### Added
- **Downbeat-aware BPM refinement** (`MCP_Server/downbeat.py`) — snaps the
  raw autocorrelation tempo (±1.5% error) to exact musical values by scoring
  onset energy on the beat/half/quarter grid across musical tempi. Prefers a
  musical tempo within ~25 cents of the raw estimate, then falls back to
  phase-sharpness tie-breaking; non-musical audio (sustained tones, silence)
  is honestly left unrefined. Verified live: a real Core Library groove's
  89.9 estimate snaps to 90.0 (1.9 cents); synthetic clicks at 121.6 snap to
  120.0. `analyze_audio_key_bpm` now also reports `bpm_dsp_estimate`,
  `bpm_refinement`, and a `bpm_note` when DSP disagrees with warp metadata —
  warp stays authoritative instead of being silently hidden.
- **Warp-metadata BPM for Live 12.4.2** — `bpm_from_warp_metadata` was dead
  on this Live version (no `clip.sample`); it is now derived from the clip's
  beat length over the file's true sample-count duration.
- Regression test for the near-tie snap (89.9 → 90.0) and the suite now
  covers 108 checks.

### Fixed
- **`analyze_audio_key_bpm` rejected every audio clip** — it gated on an
  `is_audio` field that `get_clip_info` never returned (only
  `is_midi_clip`), so the key/BPM tool always errored with "not an audio
  clip". `get_clip_info` now reports `is_audio` explicitly. Found on the
  very first live verification of the refinement engine.

### Changed
- `SCRIPT_VERSION` / `EXPECTED_SCRIPT_VERSION` bumped together to 0.7.1
  (a remote handler changed — doctor catches drift).

## [0.5.3] - 2026-09-17

Patch release hardening the tool layer against Live-API reality: three
handlers assumed properties were writable that Live 12.4.2 exposes as
read-only. Every fix was verified live against a running set.

### Fixed
- **`set_clip_slot_properties` no longer crashes on slot color** —
  `ClipSlot.color_index` has no setter in Live 12.4.2; the tool now returns a
  clear error pointing to `set_clip_color` instead of an internal error.
  `has_stop_button` handling verified working.
- **`move_arrangement_clip` actually works now** — it tried to set
  `Clip.start_time` (read-only). It now snapshots the clip's settable
  properties, duplicates it at the new position, deletes the original, and
  restores the snapshot — name, color, and other properties survive the move
  (verified live: named colored clip moved 32 → 48 beats intact).
- **`set_clip_start_time` gives an honest answer** — session clips are
  definitionally at start_time 0 and arrangement clips cannot be moved via a
  setter, so the tool now explains that and routes to `move_arrangement_clip`.
  The property snapshot also guards `.gain` on MIDI clips (reads raise).

### Changed
- Release workflow can now cut releases from a release branch: the Codeberg
  mirror push pushes the tag first and tolerates a master fast-forward miss
  (patch releases carved from master with unreleased feature work).

## [0.7.0] - 2026-09-17

v0.7 "Ears v2": the AI can now describe HOW things sound, not just what
key they're in — and put loudness numbers on it. 457 → 462 tools (468 by v0.8.0).

### Added
- **Pure-Python FFT spectral engine** (`MCP_Server/spectral.py`) — iterative
  radix-2 Cooley–Tukey FFT (verified against a naive DFT), Hann windowing,
  frame-averaged features, no numpy dependency: spectral centroid (brightness),
  roll-off (85% energy point), flatness (0 = pure tone, 1 = white noise),
  zero-crossing rate, 6-band balance (relative dB), peak frequency and a
  loudness snapshot.
- **`analyze_clip_timbre`** — full timbre fingerprint of an audio clip in the
  set, with warp metadata for context ("dark sub-heavy bass", "bright airy
  hat" — numbers instead of adjectives).
- **`analyze_sample_timbre`** — the same fingerprint for any wav/aiff on disk
  (candidate samples, stems, renders).
- **`compare_timbre`** — sample vs clip: cosine similarity over the band shape
  (scale-invariant), centroid/flatness deltas, largest band gap, and
  plain-language verdict hints for the layering/blending question.
- **LUFS loudness engine** (`MCP_Server/loudness.py`) — mono ITU-R BS.1770-4
  approximation in pure Python: K-weighting biquads designed per sample rate
  (pyloudnorm-style), 400 ms gated blocks with 100 ms hop, absolute + relative
  gates. Reports integrated/momentary LUFS, loudness range, and a
  gain-to-target hint (streaming −14 LUFS).
- **`measure_clip_loudness`** — integrated LUFS for one audio clip in the set,
  with clip context and the gain-to-target hint.
- **`audit_mix_loudness`** — the "who will jump out" report: measures the first
  audio clip of every track and classifies the set against its median —
  jumping out (≥ +3 dB), buried (≤ −6 dB), balanced — with per-track skip
  reporting. Median-based so one screaming clip can't skew the reference.
  Verified live: two clips engineered ~10 dB apart flagged exactly as designed.
- **Stem-export spike verdict** — not feasible via Control Surface on 12.4.2
  (no LOM export trigger; export hotkey doesn't open a tracked dialog; native
  menus block the bridge's own thread). Feasible alternative documented:
  guided stem export; Extensions SDK revisit queued for v0.8.
  New read-only `get_export_capabilities` probe handler.

### Fixed
- **`get_clip_file_path` returned None on Live 12.4.2** — the handler read
  `clip.sample.file_path`, but this Live version has no `Clip.sample`
  attribute; the path lives on `Clip.file_path` directly. The handler now tries
  `clip.file_path` first with the old path as a fallback. This had **silently
  disabled the file-DSP half of `analyze_audio_key_bpm` since v0.5** (warp
  metadata still worked, so the regression went unnoticed). Verified live:
  a browser-loaded sample analyzes at its exact 100 Hz tone (flatness 0.0) and
  self-compares at similarity 1.0 through the full
  browser → clip → path → DSP stack.
- **Sample reader couldn't decode WAVE_FORMAT_EXTENSIBLE wav files** —
  stdlib `wave` refuses format tag 0xFFFE, which modern sample packs use
  widely; found when the spectral engine failed on 86 of 3,015 real Core
  Library samples during a layering study. Added a minimal RIFF chunk parser
  for the extensible container (16/24/32-bit PCM subformat) plus IEEE float32
  decoding with proper stereo-to-mono mixing. All DSP tools (timbre, key/BPM,
  LUFS) benefit automatically.

### Changed
- `SCRIPT_VERSION` / `EXPECTED_SCRIPT_VERSION` bumped together to 0.7.0
  (a remote handler changed — doctor catches drift).

## [0.6.1] - 2026-09-17

Completes the v0.6 "Full Circle" roadmap: the MCP server now serves all
three surfaces (tools, resources, prompts), and mix matching goes whole-mix.
455 → 457 tools.

### Added
- **MCP resources** — clients can read live session state via `resources/read`
  without burning tool calls: `ableton://session/summary` (compact set overview),
  `ableton://track/{index}` (full track detail + meters), `ableton://journal`
  (last 50 mutations), `ableton://checkpoints`, `ableton://memory`. Wired through
  the custom TCP transport (`_handle_list_resources` / `_handle_read_resource`);
  errors return proper JSON-RPC codes (unknown URI → −32602).
- **MCP prompts** — four reusable expert workflows served via `prompts/list` and
  `prompts/get`, each self-hydrating with the current session snapshot when Live
  is connected: `mix-review`, `song-doctor`, `arrange-my-ideas`,
  `match-my-reference`.
- **`analyze_reference_mix`** — server-side DSP fingerprint of a reference audio
  file: 6-band tonal balance (dB relative to the loudest band), loudness profile
  (RMS/peak/crest), key and BPM estimates. Reuses the audio_intelligence DSP core.
- **`match_reference_mix`** — whole-mix comparison: analyzes the reference, then
  samples Live's master output meters during playback and reports loudness/crest
  gaps with concrete rollback-safe fix candidates. Meters are linear in Live's
  API — converted to dBFS with a −70 dB floor; refuses to report on a silent
  master instead of producing garbage numbers.
- **`get_master_meters`** remote-script handler — snapshots the master track's
  output meters (needed by the tools above).

### Fixed
- `analyze_reference_mix` now rejects nonexistent paths with a clear error
  instead of leaking `FileNotFoundError`.

### Changed
- `SCRIPT_VERSION` / `EXPECTED_SCRIPT_VERSION` bumped together to 0.6.1
  (a remote handler was added — doctor catches drift).

## [0.6.0] - 2026-09-17

### Added
- **Undo-safety layer (v0.6 theme 1)** — the AI can now act freely and be fully undone:
  - **Automatic checkpoints** — every mutating tool call snapshots the set *before*
    its side effects (hooked in the same choke point as the change journal).
    Best-effort and deduplicated: never fires without a live connection, never on
    replay/CI runs, never blocks the tool, never leaves a checkpoint behind on failure.
  - **`rollback(steps_back=1)`** — one call restores the last (or Nth-last) automatic
    checkpoint; the report shows tempo/track/clip repairs and the triggering tool.
  - **`safe_experiment(name, steps)`** — run a sequence of tools under protection:
    on failure the set auto-rolls-back and the report shows what was attempted.
  - **`restore_checkpoint(name)`** — revert to a named checkpoint (the previously
    documented-but-missing tool now really exists); restores tempo, scene names,
    track names/types/mixer/color, and which clip slots hold clips.
  - **`list_checkpoints` / `delete_checkpoint`** — inspect and manage both layers
    (20-entry auto ring, up to 50 persistent named checkpoints).
- **Persistent named checkpoints** — stored at `~/.ableton-bridge/checkpoints.json`,
  hydrated at server startup so checkpoints survive MCP server restarts.
- **Deeper snapshots** — capture now includes scene names and per-slot clip presence
  (name/length); `checkpoint_diff` reports added/removed/renamed tracks, mixer and
  clip changes, and scene changes.
- **Unified checkpoint store** — the context engine's `create_checkpoint` /
  `checkpoint_diff` now use the same persistent store as the undo-safety tools
  (previously a separate in-memory dict invisible to `restore_checkpoint`).
- Tool count: 450 → **455**.

### Changed
- `create_checkpoint` snapshots are deeper (scenes + clips) and persist across restarts.
- `checkpoint_diff` reports clip and scene changes in addition to track/mixer changes.

### Tests
- New offline replay suite `tests/test_checkpoints.py` (8 tests): capture/restore
  round-trip, diff semantics, auto-ring pruning, persistence round-trip, named-limit
  pruning, auto-checkpoint hook behavior (fires on mutation, skips reads/failures),
  and safe-experiment rollback.

## [0.5.2] - 2026-09-17

Patch release fixing a startup inefficiency found during post-release verification.

### Fixed
- **Browser cache is now loaded from disk at startup** — `populate_browser_cache` wrote every scan to `~/.ableton-bridge/browser_cache.json.gz` but nothing ever called `load_browser_cache_from_disk`, so each new process (MCP server, OpenCode session, test run) started with an empty cache. Consequences of the old behavior:
  - `search_browser` and `load_instrument_or_effect` name resolution unavailable until a full ~70-second rescan
  - the `doctor` tool flagged `browser_cache: empty` even when a perfectly fresh disk cache existed
  - every MCP client restart paid the rescan cost again

### Added
- **Startup hydration** — server init now loads the disk cache when present and fresh (max age 7 days, unchanged), logging `Browser cache hydrated from disk`. Verified: fresh process reports 4502 items instantly, doctor reports `healthy` with `browser_cache: 4502 items`.

### Also in this cycle
- **Release pipeline hardening** — the release workflow's trailer-append step hit a GitHub API propagation race (404 immediately after release creation); it now retries for up to 60 seconds.

**Upgrade note:** the only behavioral change is MCP-side, but the control-surface script's version marker moves to 0.5.2 as well. Reinstall (`install.bat` / `install.sh`) and restart Ableton once so the `doctor` tool reports clean alignment.

## [0.5.1] - 2026-09-17

Hardening release: a full tool-by-tool bug hunt against live Ableton Live 12.4.2 surfaced and fixed seven real bridge bugs, including a connection-killer.

### Fixed
- **Socket layer hardening** — Live objects (Groove instances, enums) leaking into tool results crashed `json.dumps`, which **disconnected the client mid-session**. Every response is now sanitized through a JSON fallback converter (enum `.value` unwrapping, bytes/set handling, object-name placeholders), so one rogue value can never tear down a session again
- **`get_clip_properties` no longer crashes** — groove is reported by name (`clip.groove` is a live Groove object, not a string), enum properties are unwrapped to plain values
- **`set_clip_properties` groove by name** — resolves a groove name against the song's groove pool with a helpful "available grooves" error instead of raising a raw TypeError; validates signature numerator/denominator
- **`clip_to_grid` / `grid_to_clip` unblocked** — they imported a `MCP_Server.grid_notation` module that never existed. New module renders drum grids (`KK|o---o---|`) and melodic grids (`G4|----o---|`) with velocity characters (X/x/O/o/*) and round-trip parsing (verified)
- **`get_track_delay` / `set_track_delay`** — Live 12.4.2's Python API does not expose `MixerDevice.track_delay` (confirmed via Live's Log.txt); both tools now feature-detect and return a clear limitation message instead of "Internal error"
- **Error messages no longer masked** — 12 capability checks ("Device is not a Drum Rack", "Track is not a group track", "Clip is not a MIDI clip", ...) raised `TypeError`, which the dispatcher hid behind "Invalid parameter type". They now raise `ValueError`, so the real message reaches the agent
- **`set_clip_start_time`** — clear Live 12.2+ requirement message, rejects negative times; **`set_clip_slot_properties`** — validates color_index range
- **`get_session_info` now reports `scene_count`** — song-builder scripts were appending duplicate scenes on every run because they couldn't count scenes (commit a963a82)

### Added
- **`get_track_devices` MCP tool** — agents can finally inspect which instruments/effects are loaded on a track; it was referenced in docs but never registered (commit 7242084)
- **`load_instrument_or_effect` MCP tool** — same story: documented everywhere, registered nowhere. Now registered with browser-cache name resolution (commit a857875). Tool count: 448 → 450
- **Test harness refresh** — 16 stale `SAFE_ARGS` entries updated to current parameter names, eliminating false "unexpected keyword argument" failures

### Verified live (Ableton Live 12.4.2 Suite)
- 450 tools registered; quick sweep passes with only intentional validation errors remaining
- Connection survives property probes that previously reset it
- `get_clip_properties` returns groove names on real clips; grid notation round-trips

**Upgrade note:** the control-surface script changed — reinstall (or run `install.bat`/`install.sh`) and restart Ableton once. The `doctor` tool will confirm script version 0.5.1.

## [0.5.0] - 2026-09-15

### Added — Audio Intelligence ("Ears")
- `analyze_audio_key_bpm` — key + BPM detection of audio samples: Live warp metadata plus server-side DSP (Goertzel chroma with Krumhansl-Schmuckler profiles, onset autocorrelation for tempo). The AI can now *hear* the key it's writing in
- `audio_clip_to_midi` — one-call Live 12 audio->MIDI (melody/harmony/drums) with a report of where the MIDI landed
- `find_mix_clashes` — heuristic frequency/mask clash finder across tracks with suggestions
- `hum_to_clip` — capture what you just played, quantize it, and add chord pads in-key

### Added — Producer Pipeline
- `produce_idea_from_prompt` — one sentence to a playable demo: parses BPM/key/genre, sets tempo, builds skeleton scenes, writes chord/bass/drum/lead clips per scene, checkpoints first, fault-tolerant at every step
- `smart_freeze` — CPU guardian: ranks tracks by device load and playing state, freezes the heaviest (dry-run supported)
- `match_reference_track` — copy a reference track's pan/volume/send levels/device on-off pattern onto a target

### Added — Studio Memory (Taste & Accountability)
- `remember_preference` / `recall_preferences` / `forget_preference` — persistent taste across sessions (~/.ablebridge/memory.json), with session-start suggestions
- Automatic **change journal** — every mutating tool call is recorded to ~/.ablebridge/journal.jsonl; `get_change_journal` answers "what did the AI change?"; `clear_change_journal` resets

### Added — Platform
- **Replay-based CI tests** (tests/test_replay.py): the full tool layer runs against recorded responses — no Ableton needed in CI
- **Web dashboard now starts in TCP mode** with a live `/api/session` endpoint (tempo, transport, per-track levels)
- Claude Desktop setup guide (docs/CLAUDE_DESKTOP.md)
- Remote script: `get_clip_file_path`, `get_track_sends` (read-only) and a SCRIPT_VERSION marker the doctor uses for drift detection

### Fixed
- `produce_idea_from_prompt` called the skeleton tool as a remote handler (wrong layer) — skeleton logic now runs against the live connection
- Note format in the producer lead melody used "start" instead of "start_time"
- Duplicate demo tracks: skeleton now matches the newest MIDI track by name and verifies it accepts MIDI clips
- `get_track_meters` called with an invalid index -1 by smart_freeze

### Verified live
- 448 tools registered; sweep 260 OK, 0 exceptions, 0 timeouts; 37/37 tests
- Key/BPM DSP: A-minor triad -> "A minor" (conf 0.68), 120 BPM clicks -> 121.6
- Full producer pipeline ran against the live set: 7/7 steps, 0 errors, scenes + clips + lead hook created
- Journal, preferences, doctor (version-drift check working), smart_freeze, mix clashes all verified

**Upgrade note:** the remote script changed — reinstall and restart Ableton once; the doctor will confirm version 0.5.0.

## [0.4.0] - 2026-09-15

### Added — AI Music Toolkit
- `generate_clip_from_prompt` — "4-bar acid bassline in F# minor" becomes a real MIDI clip in one call (style presets: acid bass, chords, arp, melody, pluck)
- `build_chord_progression` — genre-aware progressions (pop, jazz, edm, blues, epic) with optional sevenths, auto voice-leading
- `build_bassline_for_progression` — bassline following a chord degree pattern (styles: roots, octave, walking, 808)
- `generate_advanced_drum_pattern` — house/techno/trap/dnb/rock/pop/lofi templates with fills and humanization
- `build_song_skeleton` — "intro 4, verse 8, chorus 8" builds named, colored scenes + clips, ready to produce

### Added — Project Context Engine
- `get_project_context` — the whole session map (tracks, devices, clips, routing, key) in one compact call instead of 20 small ones
- `get_clip_context` — clip name, length, key scale, and note summary in one call
- `create_checkpoint` / `list_checkpoints` / `diff_checkpoint` / `restore_checkpoint` — snapshot the session structure before experimenting, diff after, restore if unwanted

### Added — Doctor & Monitoring
- `doctor` — one-call diagnosis: connection health, control-surface script version drift, port conflicts, browser-cache staleness, with plain-language fixes
- `session_integrity_report` — empty routings, clips on muted tracks, missing devices and other real-world gotchas
- `watch_session` — lightweight monitor of tempo, playing position, CPU, and clip levels the AI can poll

### Added — Show Autopilot
- `start_show_autopilot` / `stop_show_autopilot` / `autopilot_status` — hands-free timed scene sequencing for live sets: fire a scene, auto-advance after N bars (follows live tempo), per-step tempo changes, loop the whole sequence forever or N times

### Fixed
- Autopilot's invalid-JSON error message crashed itself via a str.format brace collision with the JSON example in the message
- `build_song_skeleton` missing json import
- `analyze_arrangement_*` burned ~10s per call probing a silent Max for Live bridge; now probes with a 0.75s timeout (also available to all tools via `m4l.ping(timeout=...)`)
- Test harness: setup phase creates a real MIDI clip on a dynamically discovered track; generators and destructive tools excluded from sweeps; M4L-only tools (need a running Max device) validated separately

### Verified live
- 436 tools registered; sweep 211 -> 224 OK, 0 exceptions, 0 timeouts
- Music generators wrote a real F# minor acid bassline (30 notes) and chord progression into a live Ableton 12 session
- Doctor correctly flagged version drift, port status, and a stale browser cache; autopilot fired scenes and shut down cleanly against the live set

## [0.3.4] - 2026-09-15

### Fixed (critical for MCP clients)
- **JSON-RPC envelope bug**: responses were missing the required `"result"` wrapper, so OpenCode and other strict MCP clients timed out on connect. Both stdio and TCP transports now emit spec-compliant envelopes
- **Instant handshake**: stdio no longer pre-connects to Ableton/M4L before serving — the MCP handshake answers in <1s and Ableton connects lazily on first tool use
- `create_midi_track(-1)` (append at end) crashed on a validation signature mismatch — fixed

### Added
- `mcp_stdio_launcher.py` — absolute-path entry point recommended for MCP client configs (see docs/OPENCODE.md); supports `ABLEBRIDGE_TRACE=1` file tracing for spawn debugging

### Verified end-to-end
- `opencode mcp list` -> `ablebridge connected`
- Chat-driven control of a live Ableton 12 session: session info reads and a MIDI track created from a chat prompt

## [0.3.2] - 2026-09-15

### Renamed
- **Remote script folder is now `AbleBridgePlus`** — this is the name shown in Ableton's Preferences → Link/Tempo/MIDI → Control Surface list (was "AbleBridgePlus")
- Python package renamed to `AbleBridgePlus`; console command `AbleBridgePlus`
- Persistent data directory moved from `~/.AbleBridgePlus` to `~/.ablebridge`
- Installer now removes the legacy `AbleBridgePlus` folder automatically
- Brand string **AbleBridgePlus** is kept in display messages and the dashboard title

### Note
- After upgrading, restart Ableton once and select **AbleBridgePlus** as the control surface (the old entry no longer exists once the old folder is removed)

## [0.3.1] - 2026-09-15

### Added
- **MCP transports** — AI clients can now actually connect:
  - `stdio` (default): newline-delimited JSON-RPC on stdin/stdout for OpenCode, Claude Desktop, and any MCP client
  - `tcp`: per-connection JSON-RPC on `127.0.0.1:9891` for the dashboard and multiple local clients
  - `python -m MCP_Server.server --transport stdio|tcp --tcp-port N`
- `get_browser_cache_status` tool to monitor background browser scans

### Fixed
- **Every tool now advertises its real parameters**: input schemas are derived from function signatures (the source of truth), with hand-written param descriptions merged in — fixes 167 tools that clients could not call correctly
- **Connection stability**: handler-level errors no longer tear down the shared Ableton socket (introduced `CommandError`), eliminating cascading "Could not connect" failures after any error
- **Browser cache refresh no longer blocks**: `refresh_browser_cache` runs the scan in a background thread and returns immediately (was a multi-minute synchronous block)
- **Duplicate tool names**: `start/stop_song_timer` and `get_song_timings` existed twice (show clock vs performance analytics) and silently overwrote each other; analytics variants renamed to `start/stop_performance_timer` and `get_performance_timings`
- `get_arrangement_suggestions` accepts sections as strings or dicts (crashed on strings)
- Added missing `psutil` dependency (`get_memory_usage` crashed without it)
- Remote script: fixed absolute imports that prevented the control surface from loading under its installed folder name (`AbleBridgePlus`)

### Improved
- Systematic test sweep against live Ableton: **154 → 211 tools passing, 0 exceptions, 0 timeouts** (421 tools registered)
- Test harness creates a real MIDI clip (on a dynamically discovered MIDI track) so clip tools exercise real content

## [0.3.0] - 2026-09-14

### Changed
- **Renamed project** from "Enhanced AbletonBridge" to "AbleBridgePlus"
  - Updated all references across codebase
  - Cleaner, more memorable name

### Added
- **Live Show Control** (15 tools)
  - Show clock & timer
  - Emergency stop / panic mute
  - Backup scene activation
  - Scene macros
- **Performance Analytics** (12 tools)
  - Session & track statistics
  - Mix history tracking
  - CPU/memory history
- **Session Management** (10 tools)
  - Auto-backup & restore
  - Session comparison
- **Audio/MIDI Presets** (12 tools)
  - Reverb, delay, compressor, EQ presets
  - Arpeggiator & chord presets
- **Video/Lighting** (10 tools)
  - Video effect presets
  - DMX lighting control
- **AI Enhancement** (8 tools)
  - Genre-based mixing suggestions
  - Auto gain staging
- **Advanced Show Control** (8 tools)
  - Scene macros
  - Backup presets

## [0.3.0] - 2026-09-14

### Added
- **Full core toolset port** from original AbletonBridge (293 new-style tools)
  - Clips (56), Session (51), M4L Bridge (40), Tracks (29), Snapshots (19)
  - Creative (17), Arrangement (17), Mixer (13), Browser (12), Automation (12)
  - Workflows (10), Scenes (10), MIDI CC (5), Grid (2)
- **Live Show Control categories** (from the 75-tool roadmap)
  - Emergency control (5): `emergency_stop`, `panic_mute`, `panic_unmute`, `activate_backup_scene`, `get_emergency_status`
  - Performance analytics (10): session/track stats, trends, peak/average levels, export report
  - Session backup (4): `backup_session`, `restore_session`, `list_backups`, `delete_backup`
  - Audio presets (14): reverb, delay, compressor, EQ save/load
  - Video/Lighting (10): video presets, transitions, DMX channel control, lighting scenes
  - AI enhancement (5): genre suggestions, auto gain staging, mix optimization, sound design help
  - Scene macros (4): create/fire/delete/list scene macros
  - Backup presets (4): save/load/activate backup presets
- **Browser cache** — BFS scan of Ableton's browser tree, disk cache (gzip), instant search, URI resolution for samples/devices
- **Robust connection layer** — sync TCP with newline-delimited JSON, automatic retry/reconnect, command delay tiers, per-command timeouts
- **Shared module-level state** (`MCP_Server.state`) — connections, stores, browser cache, M4L ping cache
- **Tests** — 29 validation tests (all passing)

### Changed
- Tool registration now supports both `register_tools(mcp)` modules and `@tool()` decorators via a FastMCP-compatible adapter
- `requires-python` >= 3.10 (mcp package requirement)
- `mcp<2` pinned (v1 API — FastMCP import)
- Server now registers **417 tools** (verified via `tools/list`)

### Fixed
- Server failed to boot: missing connection accessors, validation aliases, browser cache functions, state attributes, command tables
- `tool()` decorator rejected `inputSchema` keyword
- `get_m4l_status` missing from dashboard
- `_m4l_batch_set_params` missing from devices

---

## [0.2.1] - 2026-09-14

### Fixed
- **Remote Script loading in Ableton Live 12.4.1**
  - Renamed class from `AbletonBridge` to `AbleBridgePlus` to avoid conflict with original
  - Fixed Unicode encoding corruption in `__init__.py` (em-dash mojibake `â??` → ASCII `-`)
  - Added missing `_helpers.py` handler module
  - Installation now works from User Library: `Documents/Ableton/User Library/Remote Scripts/AbleBridgePlus`

### Changed
- Log messages now show "AbleBridgePlus" instead of "AbletonBridge"
- `create_instance()` returns `AbleBridgePlus` instance

## [0.2.0] - 2026-09-13

### Added
- **MIDI CC Plugin Control** (PR #8 from original AbletonBridge)
  - 5 new tools: `set_plugin_parameter_cc`, `get_cc_map`, `list_cc_maps`, `assign_cc_channel`, `send_raw_cc`
  - 100 MIDI CC maps: 45 Arturia V Collection + 55 NI Komplete Collector's Edition
  - Files: `MCP_Server/tools/midi_cc.py`, `midi_cc/*.json`
- **track_type Support** (PR #14 from original AbletonBridge)
  - Load devices onto master and return tracks via `load_instrument_or_effect(track_type="master")`
  - Files: `MCP_Server/tools/devices.py`, `AbletonBridge_Remote_Script/handlers/browser.py`
- **Extensions SDK Bridge** (PR #11 from original AbletonBridge)
  - Third parameter transport tier (M4L → _Framework → SDK)
  - Requires Live 12.4.5+ Suite + Node.js
  - Files: `MCP_Server/connections/extensions_sdk.py`
- **Show Clock Tool**
  - Show timer and clock display
  - Files: `MCP_Server/tools/show_clock.py`
- **Tests**
  - Validation tests
  - Files: `tests/test_validation.py`
- **Examples**
  - Usage examples
  - Files: `examples/README.md`
- **M4L Device README**
  - Files: `M4L_Device/README.md`
- **Release Infrastructure**
  - GitHub Actions release workflow
  - Windows installer (`release/install.bat`)
  - macOS/Linux installer (`release/install.sh`)
  - Python package config (`pyproject.toml`)
  - Files: `.github/workflows/release.yml`, `release/*`

### Changed
- Updated README with 450+ tool count
- Updated comparison table with new features
- Moved Roadmap section up in README
- Moved Quick Install section down in README
- Description now says "MCP bridge connecting AI/LLM tools to Ableton Live"
- Author changed to "Sajan Maharjan"
- Wording changed to "Inspiration from AbletonBridge by hidingwill"

### Fixed
- CS-80 Brilliance CC collision (CC 23 → CC 81) in Arturia V Collection maps
- Device iteration in `_get_plugin_name_from_track()` now iterates all devices

## [0.1.0] - 2026-09-13

### Added
- Core MCP Server architecture (from AbletonBridge)
- TCP connection to Ableton Remote Script
- UDP connection for real-time updates
- M4L Bridge integration
- Basic tool set (tracks, clips, devices, mixer, browser)

### Enhanced
- Routing channels exposure in `get_track_routing`
- Added `available_input_routing_channels` to response
- Added `available_output_routing_channels` to response

### Added (New Tools)
- MIDI mapping tools (get, create, delete, save/load)
- Plugin management tools (scan, list, configure, presets)
- Video routing tools for Videosync2
- Setlist management tools for AbleSet
- Performance monitoring tools (CPU, memory, latency)
- Quick presets tools for live shows
- AI integration tools (snapshots, suggestions)
- Audio analysis tools (spectrum, levels, chords)
- Template system tools
- Advanced routing tools (side-chain, multi-output)
- Automation enhancement tools

## [0.0.1] - 2026-09-13

### Added
- Project planning and documentation
- Feature roadmap
- Memory file for project tracking

---

## Version History

- **0.2.0** — Added MIDI CC maps, track_type support, Extensions SDK, show clock, tests, release infrastructure
- **0.1.0** — First working release with core features and 10 enhanced tool categories
- **0.0.1** — Initial planning and documentation

## Upgrade Guide

### From 0.1.0 to 0.2.0
1. Pull latest changes: `git pull origin master`
2. Run `uv sync` to update dependencies
3. Install MIDI CC dependencies: `pip install mido python-rtmidi`
4. Copy updated Remote Script to Ableton
5. Restart Ableton Live
6. Restart MCP Server

### From 0.0.1 to 0.1.0
1. Pull latest changes
2. Run `uv sync` to update dependencies
3. Copy Remote Script to Ableton
4. Restart Ableton Live
5. Restart MCP Server

## Known Issues

- Grouping tracks requires manual UI interaction (Ableton limitation)
- Some VST/AU plugins may not expose all parameters
- M4L Bridge requires Max for Live to be installed
- Extensions SDK requires Live 12.4.5+ Suite + Node.js
- MIDI CC maps may not cover all plugin parameters

## Future Plans

- LIA plugin integration (when available)
- TouchDesigner integration
- Automated show control
- Multi-DAW support
- Advanced AI features
- 75+ new tools (see docs/NEW-FEATURES-PLAN.md)
