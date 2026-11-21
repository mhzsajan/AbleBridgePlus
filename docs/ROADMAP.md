# AbleBridgePlus — Roadmap

> Living document. Updated after each release. Current version: **v0.9.6** (495 tools).

## Where the project is

| Layer | Status |
|---|---|
| **1 — Control** (remote-control everything in Live) | ✅ Shipped v0.1–v0.3 |
| **2 — Intelligence** (context engine, theory toolkit, doctor, autopilot) | ✅ Shipped v0.4 |
| **2.5 — Ears & Producer** (DSP key/BPM detection, one-prompt-to-demo, memory) | ✅ Shipped v0.5 |
| **3 — Collaboration** (AI listens, judges, contributes taste) | 🔜 The next frontier |

---

## v0.9.5 — device-adaptive master switching (2026-11-18)

- Master output resolution no longer depends on preset display names matching the local audio
  device; the in-Live handler falls back to adaptive resolution at click time.

## v0.9.4 — master output in audio presets (2026-11-18)

- Presets now capture/apply the Master track output routing (PC 1/2 ↔ WING 41/42), not just the
  49 regular tracks. Both MCP and the in-Live OSC handler verify it after writing.

## v0.9.3 — portable audio presets (2026-11-18)

- **Both sides resolve the same path.** MCP writer and in-Live reader share a
  resolver so `routing-presets.json` can live in the AbleSet project folder and
  travel to another Mac. Env vars / `~/.ableton-bridge/config.json` override the
  legacy home-path fallback; resolved on every call, no server restart needed.
- `tests/test_preset_store.py` locks the precedence and cross-side agreement.

## v0.9.2 — zero-AI audio profile switching (2026-11-17)

- **Remote-script OSC listener on UDP 9883** (`AbleBridgePlus/__init__.py` +
  `AbleBridgePlus/handlers/profile.py`) applies per-track output presets from the
  shared `~/.ableton-bridge/routing-presets.json` when an AbleSet Canvas button
  sends `/profile/pc`, `/profile/wing` or `/profile/<name>`. No AI or MCP server
  is involved at showtime. The global audio device remains a manual switch and
  the WING must be connected for its output names to resolve; presets must be
  regenerated after setlist edits. Tool count unchanged (488).

## v0.9.1 — show-control follow-ups (2026-11-17)

Small but high-value additions landed after v0.9.0:

- **AbleSet state** — `start_ableset_listener` / `get_ableset_state` and the
  `ableton://ableset/state` resource track AbleSet's song/section/start/end
  (listener binds UDP 39052, not AbleSet's own 39051; a human must point
  AbleSet's OSC output at it) so clients read state instead of polling a dead
  surface. The
  earlier "2-way dashboard / AbleSet state" gap is partially closed.
- **Tempo-driven WING delay helper** — `set_wing_delay_time_from_tempo` writes
  the delay effect time in ms from Live tempo. This closes the "external-device
  FX time helper" gap below; MIDI Clock sync to the WING remains impossible via
  LOM, so a tempo reader + OSC writer is the working path.
- **LOM capability probe** — `probe_lom_capability`, a safe read-only `dir()`
  probe over whitelisted roots (`song`/`track`/`clip`/`device`/`scene`/`return`).
- **Locator macro auto-fire** — a registered macro now fires automatically
  after a successful `jump_to_locator` (the v0.9.0 deferral is resolved).
- **Replay fixture + Python 3.14 test fixes** — the missing
  `tests/fixtures/replay.json` was added and all eight pre-existing Python 3.14
  test failures fixed in the test layer only.

---

## v0.6 — "Full Circle" (IN PROGRESS)

Theme: **trust and smarter clients**. The AI touches your set; you can undo it; clients get richer context.

### 1. Undo-safe experimentation  `high` — ✅ SHIPPED (unreleased)
Live's native undo is fragile with remote scripts (some operations bypass it). Build a
real safety net:

- [x] **Auto-checkpoint before every mutation** — hooked in `_tool_handler`
  (same choke point as the change journal): live-connection check, dedup,
  20-entry ring, never fires on tool failure or replay/CI runs.
- [x] **`rollback(steps_back)`** — one call restores the last (or Nth-last)
  auto checkpoint; returned report shows what was undone and the trigger.
- [x] **`safe_experiment(name, steps)`** — wrap a sequence of tool names;
  auto-rollback on failure with the attempt report. Documented patterns
  beat a callback API for MCP (no client code to install).
- [x] **Unified with the context-engine checkpoints** — `create_checkpoint`,
  `checkpoint_diff` and the new `restore_checkpoint` share one persistent
  store (`~/.ableton-bridge/checkpoints.json`), deep snapshots include
  scene names and per-slot clips, plus `list_checkpoints` / `delete_checkpoint`.
- Effort: ~2–3 days. Unlocks: users let the AI act freely.

### 2. MCP resources & prompts  `high` — ✅ SHIPPED (unreleased)
The server now serves all three MCP surfaces. MCP supports *resources*
(state the client can read) and *prompts* (reusable templates) alongside tools:

- **Resources** — expose live session state (`ableton://session/summary`,
  `ableton://track/{i}`, `ableton://journal`) so clients can read context without burning
  tool calls.
- **Prompts** — pre-built templates: "mix review", "song doctor", "arrange my ideas",
  "match my reference". One click in Claude Desktop / OpenCode gives the AI a full
  expert workflow.
- Note: both transports are wired. stdio is handled natively by FastMCP; the custom
  TCP transport routes `resources/list`, `resources/read`, `prompts/list` and
  `prompts/get` through `_handle_list_resources` / `_handle_read_resource` /
  `_handle_list_prompts` / `_handle_get_prompt` in `server.py`, backed by
  `tools/resources_prompts.py`.
- Effort: ~2 days.

### 3. Whole-mix reference matching  `medium` — ✅ SHIPPED (unreleased)
`match_reference_track` matches single tracks. Mix-level matching is here:

- `analyze_reference_mix` — server-side DSP fingerprint of a reference audio file
  (6-band tonal balance in relative dB, RMS/peak/crest loudness, key, BPM; reuses the
  audio_intelligence DSP core).
- `match_reference_mix` — samples Live's master output meters during playback
  (new `get_master_meters` remote handler; one Ableton restart, done) and reports
  loudness/crest gaps vs the reference with concrete, rollback-safe fix candidates.
- Honest scope: Live exposes broadband master meters only (no per-band spectrum),
  so the live side contributes loudness numbers; band-balance targets come from the
  reference analysis. The tools state this plainly instead of pretending.
- Effort: shipped. Unlocks: "make my mix sit like THAT track" at mix level.

### 4. Housekeeping  `low`
- Record fresh replay fixtures after v0.6 tools land (CI stays Ableton-free).
- If any remote-script handler is added, bump `SCRIPT_VERSION` and `EXPECTED_SCRIPT_VERSION`
  together (doctor catches drift). — Done for v0.6.x: `get_master_meters` added,
  both bumped to 0.6.1, live-verified with zero drift.
- Record fresh replay fixtures after v0.6 tools land (CI stays Ableton-free). — Still open.

---

## v0.7 — "Ears v2"

- **Spectral analysis** — ✅ SHIPPED (unreleased): real FFT in pure Python
  (iterative Cooley–Tukey, no numpy) in `MCP_Server/spectral.py`; spectral centroid,
  roll-off, flatness, ZCR, 6-band energies, peak frequency per clip. Tools:
  `analyze_clip_timbre`, `analyze_sample_timbre`, `compare_timbre` (cosine
  similarity over band shape + plain-language hints). Also fixed a silent v0.5
  regression: `get_clip_file_path` returned None on Live 12.4.2 (Clip.file_path
  is the path; `clip.sample` doesn't exist), which had quietly disabled the
  file-DSP half of key/BPM detection.
- **Per-clip loudness (LUFS approximation)** — ✅ SHIPPED (unreleased): mono
  BS.1770-4 approximation (`MCP_Server/loudness.py`, pure Python): K-weighting,
  gated blocks. Tools: `measure_clip_loudness` (integrated/momentary LUFS +
  gain-to-target hint) and `audit_mix_loudness` (median-based classification:
  jumping out ≥ +3 dB, buried ≤ −6 dB — the "who will jump out" report).
  Verified live with clips engineered ~10 dB apart.
- **Stem export** — ❌ SPIKE RESULT: not feasible as originally scoped on 12.4.2.
  Evidence from a live spike test: (1) the Live Object Model has **no export/render
  API** — `Application` exposes a dialog API (`open_dialog_count`,
  `current_dialog_message`, `press_current_dialog_button`) but nothing to trigger
  export; (2) the `Ctrl+Shift+R` hotkey did **not** open export when sent through a
  verified-working keyboard channel (Space toggled playback reliably through the
  same path); (3) the export dialog is not an OS window (no new top-level window on
  open attempt); (4) opening Live's native File menu (Alt+F) **blocks Live's main
  thread — starving the bridge itself** until dismissed. Feasible instead:
  a *guided* stem-export workflow (solo track via LOM → file-watcher on the export
  folder → prompt user to render → verify → un-solo → next). The proper long-term
  path is Ableton's **Extensions SDK** (public beta since June 2026) — revisit
  export automation there in v0.8. Probe handler kept: `get_export_capabilities`.
- **Downbeat-aware BPM refinement** — ✅ SHIPPED in v0.7.1. Onset-grid engine
  (`MCP_Server/downbeat.py`): musical-tempo preference window (±25 cents) +
  phase-sharpness tie-break. Verified live: 89.9 → 90.0 on a real Core Library
  groove; 121.6 → 120.0 on synthetic clicks. Also fixed two latent bugs the
  live test exposed: `analyze_audio_key_bpm` rejected every audio clip
  (`get_clip_info` never emitted `is_audio`), and warp-metadata BPM is now
  derived honestly (clip beats ÷ file duration) since Live 12.4.2 has no
  `clip.sample`; DSP/warp disagreement is surfaced, not hidden.

## v0.8 — "Collaboration"

- **Show navigation** — ✅ SHIPPED (first v0.8 feature): 6 locator tools built
  and live-verified on the real Videosync2 show set (56 locators, 18 tracks).
  The AI can list locators in show order, jump to any song by fuzzy name,
  walk next/prev, report the current section, and rename. Cue-point creation
  is possible: `set_or_delete_cue` (a server tool, `tools/session.py:275`)
  toggles one at the playhead, and v0.9.0 added `create_named_locator` to
  create one at an arbitrary beat with a best-effort name.
- **Show builder workflow** (in progress) — driving the actual Deepak Bajracharya
  & Rhythm Band show build: lyrics/chords clip generation per song (Ritu pilot
  pattern → all 28 songs), pre-show doctor (lyrics/tempo/locator-pair/click
  coverage audit), SECTIONS +CC expansion for lighting/TouchDesigner. Learnings
  feed StageCraft.
- **2-way web dashboard** — today it's read-only monitoring. Add click-to-control:
  select a track in the browser → AI receives it as context for the next prompt.
  **Partially addressed in v0.9.1** for show state: `start_ableset_listener` /
  `get_ableset_state` and the `ableton://ableset/state` resource expose AbleSet's
  song/section/start/end without a dashboard round-trip.
- **Journal replay** — the change journal already logs every AI mutation; add
  `replay_journal(range)` to re-apply a recorded pass onto another section
  ("redo yesterday's automation pass on the new chorus").
- **Taste profile v2** — studio memory grows into a profile: preferred progressions,
  synth choices per genre, mix references. Producer pipeline reads it automatically.

## Live-show gaps found 2026-11-16 (v0.9 candidates)

These came out of driving the WING console's vocal FX from an Ableton MIDI track during a real
show build. Full context in the private `StageCraft-Graphified` repo:
`docs/live-pipeline/bands/deepak-bajracharya-rhythm-band/hardware/WING-CONSOLE.md`.
Statuses below reflect v0.9.1 (2026-11-17).

- **MIDI CC envelope lanes** `high` — **capability probe added 2026-11-17** (`probe_midi_cc_envelope_surface`,
  read-only `dir()` introspection of a MIDI clip's envelope/CC/automation-target surface).
  API existence is **still unproven**; Arrangement red lanes remain impossible. `_find_parameter` in
  `handlers/automation.py` still only resolves Volume/Pan/Sends/device parameters, so
  `create_clip_automation` cannot create a "MIDI Ctrl → CC 12/13" envelope. MIDI CC envelopes are
  clip-envelope-only in Live and cannot be shown as Arrangement automation lanes; the working
  workaround for red lanes remains an M4L device with mapped macros (no M4L installed here).
- **Arrangement clip envelope clear** `medium` — **ADDRESSED in v0.9.0**: `clear_arrangement_clip_envelopes(track_index, clip_index)`
  resolves the clip directly from `track.arrangement_clips` (the old `clear_all_clip_envelopes` went through
  `get_clip()`, Session slots only), reports the pre-clear envelope count, and no longer requires
  deleting/recreating the clip.
- **MIDI port Sync (clock) toggle** `medium` — no tool to enable "Sync" on a specific MIDI output port
  in Live's MIDI Preferences. Needed to send MIDI Clock to external gear (WING delay test: tempo
  115→80→120, `/fx/5/time` never moved). A `set_midi_port_sync(port_name, sync, remote, track)` tool
  would let us test/compensate without manual Preferences clicking. Still open.
- **Cue-point creation** `low` — **ADDRESSED in v0.9.0**: `create_named_locator(beat, name)` moves the
  playhead to an absolute beat, creates a cue via `song.set_or_delete_cue()` (which *does* exist —
  server tool in `tools/session.py:275`), and best-effort renames it. Earlier claims that cue creation
  needs an M4L bridge were wrong. `list_arrangement_locators` (a.k.a. `list_cue_points`) also works.
- **External-device FX time helper** `low` — **ADDRESSED in v0.9.0/v0.9.1**: the generic
  `set_external_param` tool shipped in v0.9.0, and v0.9.1 added
  `set_wing_delay_time_from_tempo`, which reads Live tempo and writes the device's effect-time
  parameter in ms (`30000 / BPM` for 1/8 notes). MIDI Clock sync to the WING remains
  impossible via LOM. See the v0.9.1 note above.

## Backlog (unscheduled)

- **Template/preset marketplace** — shareable `.ablebridge` packs (producer pipeline
  templates, autopilot show structures).
- **Multi-instance Live routing** — run two Lives, each with its own MCP port; server
  auto-discovery. Also the fix for users running Live 11 + 12 side by side.
- **Live 11 compatibility audit** — v0.5 relies on Live 12 APIs (`audio_to_midi`,
  version marker). Enumerate and gracefully degrade.
- **Nightly live smoke-test in CI** — Windows runner + real Live + real script; catches
  Live-update breakage before users hit it. Needs license consideration on the runner.
- **Docs: video walkthrough** of the producer pipeline.

## Engineering notes for future sessions

- Replay fixtures (`tests/fixtures/`) must be regenerated whenever tool schemas change —
  `uv run --with pytest pytest tests/` runs entirely without Ableton.
- The installer now clean-replaces the Ableton script folder (v0.5.0-era fix); keep that
  behavior when editing `release/install.{bat,sh}`.
- Any new remote-script handler ⇒ bump `SCRIPT_VERSION` (handlers/session.py) **and**
  `EXPECTED_SCRIPT_VERSION` (MCP_Server/tools/doctor.py) together, then reinstall the
  script + restart Ableton.
- Sweep command pattern for live regression: `.venv/Scripts/python - <<EOF` against the
  TCP port 9877 with `{"type": ..., "params": ...}` protocol.
