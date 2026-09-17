# AbleBridgePlus — Roadmap

> Living document. Updated after each release. Current version: **v0.5.0** (448 tools, 37 tests, CI green).

## Where the project is

| Layer | Status |
|---|---|
| **1 — Control** (remote-control everything in Live) | ✅ Shipped v0.1–v0.3 |
| **2 — Intelligence** (context engine, theory toolkit, doctor, autopilot) | ✅ Shipped v0.4 |
| **2.5 — Ears & Producer** (DSP key/BPM detection, one-prompt-to-demo, memory) | ✅ Shipped v0.5 |
| **3 — Collaboration** (AI listens, judges, contributes taste) | 🔜 The next frontier |

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
- Note: stdio transport handled by FastMCP handles resources natively; the custom TCP
  transport needs the resource handlers wired through (skeleton exists:
  `_handle_list_resources` in server.py).
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
- **Downbeat-aware BPM refinement** — current autocorrelation is within ~1.5%; use
  onset-pattern matching to snap to exact values (120.0 not 121.6).

## v0.8 — "Collaboration"

- **2-way web dashboard** — today it's read-only monitoring. Add click-to-control:
  select a track in the browser → AI receives it as context for the next prompt.
- **Journal replay** — the change journal already logs every AI mutation; add
  `replay_journal(range)` to re-apply a recorded pass onto another section
  ("redo yesterday's automation pass on the new chorus").
- **Taste profile v2** — studio memory grows into a profile: preferred progressions,
  synth choices per genre, mix references. Producer pipeline reads it automatically.

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
