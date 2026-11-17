# AbleBridgePlus, in pictures

A few short diagrams to go with the words in the
[README](../README.md). Each one has a plain-language caption, so you can
read the caption and skip the boxes if that's easier. Nothing here is a hard
rule — it's a map of how the pieces normally fit together.

> These are schematic illustrations, not photos and not exact wiring diagrams.

---

## 1. The layers

The path from you to your music is four boxes long: an AI client calls the
bridge, the bridge calls a small script living inside Live, and that script
moves the real tracks, devices and clips.

```mermaid
flowchart TD
    AI["AI client<br/>Claude · OpenCode · Cursor<br/>speaks MCP"]
    MCP["AbleBridgePlus MCP server<br/>Python · stdio or TCP :9891<br/>hundreds of tools, resources, prompts"]
    RS["Remote script<br/>runs inside Ableton · TCP :9877 / UDP :9882"]
    LOM["Live Object Model (LOM)<br/>tracks · devices · clips · mixer"]

    AI -->|"MCP"| MCP
    MCP -->|"JSON commands"| RS
    RS -->|"on Live's main thread"| LOM
```

---

## 2. Build time vs. show time

The AI is a **build-time** helper: you use it to set up, edit and rehearse the
set, then it steps aside — once the show starts, AbleSet is the brain and the
bridge's tools just sit there ready if you need them.

```mermaid
flowchart LR
    subgraph BUILD["BUILD TIME — you and the AI"]
        direction TB
        B1["You describe a change"]
        B2["AI plans it"]
        B3["AbleBridgePlus does it in Live"]
        B4["Set / preset is saved"]
        B1 --> B2 --> B3 --> B4
    end

    subgraph SHOW["SHOW TIME — no AI needed"]
        direction TB
        S1["AbleSet = show brain<br/>song · section · tempo"]
        S2["Band presses Canvas buttons"]
        S3["Ableton · WING · visuals<br/>run the show"]
        S1 --> S2 --> S3
    end

    B4 -.->|"hand over the prepared set"| S1
```

---

## 3. One-click audio profiles (no AI in the loop)

A single AbleSet Canvas click sends one OSC message straight to a listener
inside Live, which reads a saved preset and re-routes every track — no AI, no
Python and no MCP server anywhere in that path.

```mermaid
sequenceDiagram
    participant C as AbleSet Canvas button
    participant R as Remote script :9883
    participant P as Preset file
    participant T as Live tracks

    C->>R: UDP OSC /profile/wing (or /profile/pc)
    R->>P: read ~/.ableton-bridge/routing-presets.json
    P-->>R: saved per-track outputs
    loop about 49 tracks
        R->>T: set_track_routing
        T-->>R: get_track_routing (read-back)
    end
    Note over R,T: Result is reported in Ableton's status bar / Log.txt,<br/>not sent back to the button (OSC is fire-and-forget).
```

---

## 4. The safety idea

The guardrails are: ask before acting, preview a risky change, verify what
actually stuck, keep a diary, and leave an undo ready — with an extra
"show mode" gate on gear that can be heard by an audience.

```mermaid
flowchart LR
    SM["Show mode<br/>extra care during a show"] --> CF["Confirm<br/>you approve it"]
    CF --> DR["Dry run<br/>preview, change nothing"]
    DR --> W["Write + read-back<br/>check what really happened"]
    W --> J["Journal<br/>every change written down"]
    J --> U["Undo / rollback<br/>one word puts it back"]
```

A note on that first pair: **show mode** and **confirm** are the guardrails used
by live-show gear such as the WING mixer's own MCP server. Inside AbleBridgePlus
the safety features you'll actually meet are **dry run** (for example on
`apply_output_preset`), the verified **write + read-back**, the **change
journal**, and **rollback**.

---

## 5. The ports map

Only a handful of ports are involved: `:9891` is AI-to-bridge, `:9877`/`:9882`
and `:9883` reach Live, `:39051`/`:39052` carry AbleSet's song state, and
`:2223` reaches the WING console.

```mermaid
flowchart TB
    subgraph AISIDE["AI side (build time)"]
        AI2["AI client"]
        MCP2["MCP server<br/>stdio · TCP :9891"]
        AI2 --- MCP2
    end

    subgraph LIVESIDE["Ableton / show rig"]
        RS2["Remote script<br/>TCP :9877 commands<br/>UDP :9882 real-time params"]
        PROF["Profile listener<br/>UDP :9883 — zero-AI OSC"]
        ABL["AbleSet<br/>own OSC :39051<br/>sends to bridge :39052"]
    end

    subgraph RIG["Show network"]
        WING["WING console<br/>OSC UDP :2223<br/>own MCP server"]
    end

    MCP2 -->|"commands / params"| RS2
    PROF --> RS2
    ABL -->|"song + section state"| MCP2
    MCP2 -->|"external OSC"| WING
```

A couple of practical notes, because they trip people up:

- AbleSet forgets its subscription when it restarts. If song state goes
  missing, re-subscribe by hand from AbleSet's OSC settings page
  (`/subscribe 127.0.0.1 39052 AbleBridgePC`). The `subscribe_ableset` tool is
  not reliable for this — the manual step is the dependable one.
- `:39051` is **AbleSet's own** listen port; the bridge listens on `:39052` so
  the two never collide.
- `doctor` is the quickest way to spot version drift between the installed remote
  script and the MCP server.

---

Back to the [README](../README.md), or see
[docs/ARCHITECTURE.md](ARCHITECTURE.md) for the deeper protocol details.
