# Show setup tools: output-routing presets + AbleSet subscription

Two small, non-destructive tools solve recurring live-setup chores:

1. **Output-routing presets** — switch all tracks' audio outputs between the PC
   audio device and the WING console in one call.
2. **AbleSet subscription helpers** — ask AbleSet to push its show-state OSC to
   the bridge, and be honest when it refuses.

Neither tool restructures the Ableton set, changes input routing, changes
volume/mute/sends, or touches Live's global audio-device preference.

---

## 1. The problem, measured on the live set

Read-only inspection (2026-11-17) of the running set via `get_all_tracks_info`
and `get_track_routing`:

- **49 regular tracks** + **3 return tracks**
  (`A-Mastering - Gentle Limiter`, `B-Sloppy Delay`, `C-Concert Hall`).
- **12 distinct output destinations** are already in use: `Main` (6 tracks),
  `Live Tracks` (6), `Drums Rec` (9), `B.Tracking Group` (5), `Vocals` (4),
  `Percussions` (4), `VSync2 Group` (4), `Click n Cue` (3), `Guitars` (2),
  `Keys n FX` (2), `Grp Vocals` (2), and `No Output` (2 MIDI tracks).
- All output channels are currently blank (outputs go to `Main` or to track/group
  buses, not to `Ext. Out`). Every audio track does list `Ext. Out` as an
  available output type — that is the route used to reach a specific output
  pair of the active audio device. The two MIDI tracks list `WING MIDI Control`
  among their output options.
- A bus hierarchy already exists: child tracks feed buses (`Drums Rec`,
  `Guitars`, `Keys n FX`, `Grp Vocals`, `Percussions`, `Click n Cue`,
  `Live Tracks`, `VSync2 Group`), and only the top-level buses plus a few
  standalone tracks land on `Main`.

So the manual work is real: to move the whole show between PC and WING, each
track that goes to `Ext. Out` must be re-pointed to a different channel pair,
one track at a time.

### Approaches considered

- **(A) Bus architecture** — route all ~49 tracks to a handful of buses once,
  then switch only the buses' outputs. Lowest per-switch effort, and the set is
  already partly built this way, but completing it means rewiring a live set.
  **Not done** — too risky during a show. Recommended only as a future,
  scheduled restructure.
- **(B) Routing presets in the bridge** — capture the current per-track output
  routing as a named preset (`pc`, `wing`) and apply it atomically with one
  tool call. Uses the existing `set_track_routing` command underneath;
  non-destructive, testable, no set restructure. **Recommended and implemented.**
- **(C) Hybrid** — presets plus an easy assistant/automation call path. This is
  what shipped: the preset tools plus the honest AbleSet notes below.

---

## 2. Output-routing preset tools

| Tool | Signature | Purpose |
|---|---|---|
| `get_current_output_routing` | `()` | Read all tracks' output routing (read-only) + distinct-destination count |
| `save_output_preset` | `(name: str, description: str = "", overwrite: bool = False)` | Capture all tracks' output type/channel into a named preset |
| `list_output_presets` | `()` | List saved presets with track counts |
| `apply_output_preset` | `(name: str, dry_run: bool = True)` | Preview or apply + verify a preset |
| `delete_output_preset` | `(name: str)` | Remove a preset |

Presets live in one file shared by the MCP tools and the in-Live OSC listener.
From v0.9.3 that path is configurable so it can live **inside the AbleSet project**
and travel to another Mac. The resolver (both sides) picks the first of:

1. env `ABLETON_BRIDGE_PRESET_PATH` — full path to `routing-presets.json`
2. env `ABLETON_BRIDGE_PRESET_DIR` — folder holding that file
3. `~/.ableton-bridge/config.json` — `{"routing_presets_path": "..."}` or
   `{"routing_presets_dir": "..."}`
4. legacy `~/.ableton-bridge/routing-presets.json`

Recommended for a show: keep the file at
`<Project>/AbleSet/AudioProfiles/routing-presets.json` and have
`ableset-show-profile/scripts/setup.sh` write the config entry on each Mac.
Each preset stores only `{index, name, output_type, output_channel}` per track;
re-save after any setlist edit because indexes shift. **The preset file itself
must be a real file, not a symlink** — saves replace it atomically (`os.replace`);
symlinking the whole folder is safe.

`apply_output_preset` **defaults to `dry_run=True`**. A dry run performs reads
only. A real apply writes each changed track with `set_track_routing`, reads it
back immediately, and reports per-track `applied_and_verified`,
`already_matching`, `mismatches`, `skipped` (track no longer in set) and
`errors`. Because the tool name starts with `apply_`, the bridge's ordinary
auto-checkpoint safety net also snapshots the set before a real apply.

> Note: `save_routing_preset` / `load_routing_preset` / `get_routing_presets_list`
> in `advanced_routing.py` are older **placeholders** that save empty data to a
> different file (`~/.ablebridge/routing_presets.json`). Use the `*_output_preset`
> tools above instead.

### One-time setup on the real rig

1. In Live, with the **PC audio device** active, point every track's output at
   the PC device the way you want it (e.g. `Ext. Out` / `1/2`, `3/4`, ...).
2. Ask the assistant: `get_current_output_routing` — confirm the track count
   (49) and the destinations/channels look right.
3. Ask: `save_output_preset(name="pc", description="PC audio device")`.
4. Switch the rig to the **WING** configuration (WING USB outputs as Live's
   audio device) and re-point each track's output the way you want it.
5. Ask: `save_output_preset(name="wing", description="WING USB outputs")`.
6. Ask: `list_output_presets` — both should appear with 49 tracks each.

### Switching thereafter

1. Preview: `apply_output_preset(name="wing", dry_run=True)` — review
   `planned` / `would_change` (no writes).
2. Commit: `apply_output_preset(name="wing", dry_run=False)` — the report shows
   what was applied and verified. To go back, use `name="pc"`.

In plain language to the assistant: *"Switch all outputs to the WING preset —
show me the dry run first, then apply it."*

### What a Canvas button can and cannot do

**AbleSet Canvas buttons cannot call MCP tools.** The bridge has no inbound
OSC-to-tool dispatcher: OSC can go *out* of the bridge (`send_osc_macro`,
`set_external_param`) and AbleSet show-state OSC comes *in* to a fixed listener,
but an OSC message from a Canvas button cannot invoke `apply_output_preset`.
Do not wire a button expecting a routing switch to happen — it will not.

The honest paths are:

- **Assistant call (recommended):** say *"apply the wing output preset"*, which
  goes through the two-step dry-run/apply flow above.
- **AbleSet OSC Command Tester / a Canvas "send OSC" action:** only for things
  AbleSet genuinely triggers over OSC — the proven example is the
  `/subscribe` message in the next section.

If a true one-button routing switch is wanted later, it would need a new
inbound-OSC → preset-apply bridge (not implemented here).

---

## 3. AbleSet subscription tools

| Tool | Signature |
|---|---|
| `subscribe_ableset` | `(host="127.0.0.1", port=39051, name="AbleBridge", fine=False, listen_port=39052)` |
| `unsubscribe_ableset` | `(host="127.0.0.1", port=39051, name="AbleBridge")` |

`subscribe_ableset` ensures the bridge's state listener is running on
`listen_port`, sends `/subscribe <listen_port> <name>` (plus `true` when
`fine`) to AbleSet's OSC port, waits ~1.5 s and reads the listener snapshot.
If no state arrived it retries once with an integer-tagged port (the shared
OSC helper otherwise coerces numbers to floats for the WING), then reports the
result. **It does not claim success unless state actually arrived.** When
AbleSet ignores the message the result says so and gives this exact fallback:

> Open <http://127.0.0.1/settings/osc> → OSC Command Tester and send
> `/subscribe 127.0.0.1 39052 AbleBridgePC` manually; an OSC connection with
> Send Address `127.0.0.1:39052` may also be required.

This matches the recipe proven live on 2026-11-17: create an OSC connection
named `AbleBridgePC` with Send Address `127.0.0.1:39052`, then send
`/subscribe 127.0.0.1 39052 AbleBridgePC` from AbleSet's own UI. After that,
`get_ableset_state()` returned the real show data (song *Jam Na Maya*, 28 songs,
26 sections, tempo 115).

Remember the two ports: **39051** is AbleSet's OSC input (where we send
`/subscribe`); **39052** is the bridge's listener (where AbleSet pushes state).
Using 39052 as the target would collide with the listener.

`unsubscribe_ableset` sends `/unsubscribe <name>`; AbleSet's exact argument
shape for that message is not guaranteed — verify in its OSC Command Tester if
state keeps arriving.

---

## 4. Caveats

- **Live's global audio output device is not controllable from the bridge.**
  Selecting "PC speakers" vs "WING USB" in Live's Preferences → Audio (and the
  matching Windows playback device) is a global preference outside the Live
  Object Model and outside OSC. The presets switch per-track routing; the
  device itself must still be selected by hand.
- Output channel labels (e.g. `1/2`) depend on the currently active audio
  device. A preset captured with one device may contain channel names the
  other device does not offer — the apply report will show those as
  `mismatches` / `errors` rather than silently succeeding.
- Presets are keyed by **track index**, not name. If tracks are inserted,
  deleted or reordered between saving and applying, indices shift; the report
  flags missing tracks as `skipped`. Re-save the presets after any track-list
  change.
