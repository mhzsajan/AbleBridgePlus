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

## v0.6 — "Full Circle" (next release)

Theme: **trust and smarter clients**. The AI touches your set; you can undo it; clients get richer context.

### 1. Undo-safe experimentation  `high`
Live's native undo is fragile with remote scripts (some operations bypass it). Build a
real safety net:

- **Auto-checkpoint before every mutation** — hook the mutation path in
  `_tool_handler` (same choke point as the change journal) and snapshot before side-effects.
- **`rollback`** — one tool call restores the last checkpoint.
- **`safe_experiment(name, fn)`** — wrap any sequence of mutations; on failure, auto-rollback
  and report what was attempted.
- Combines with the existing checkpoint system (context engine) rather than duplicating it.
- Effort: ~2–3 days. Unlocks: users let the AI act freely.

### 2. MCP resources & prompts  `high`
The server currently serves **tools only** (448 of them). MCP also supports *resources*
(state the client can read) and *prompts* (reusable templates):

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

### 3. Whole-mix reference matching  `medium`
`match_reference_track` matches single tracks today. Extend to mix-level:

- Analyze a reference audio file (song you like, or your other track) server-side
  (reuse audio_intelligence DSP).
- Compare tonal balance vs. the current set's master output… *(needs a master-meter read —
  may require one small remote-script handler addition, which means one Ableton restart)*
- Report: "your mix is 3 dB light below 100 Hz vs reference; candidate fixes: …"
- Effort: ~2–3 days.

### 4. Housekeeping  `low`
- Record fresh replay fixtures after v0.6 tools land (CI stays Ableton-free).
- If any remote-script handler is added, bump `SCRIPT_VERSION` and `EXPECTED_SCRIPT_VERSION`
  together (doctor catches drift).

---

## v0.7 — "Ears v2"

- **Spectral analysis** — real FFT in pure Python (Cooley–Tukey); spectral centroid,
  roll-off, band energies per clip. Key/BPM already works; this adds timbre awareness.
- **Per-clip loudness (LUFS approximation)** — gated loudness on decoded clip audio;
  flag clips that will jump out of the mix.
- **Stem export mapping** — drive Live's export dialog programmatically (solo + export
  per track). Largest effort item; depends on Live's export being scriptable from a
  Control Surface (needs a spike/spike-test first).
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
