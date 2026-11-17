# AbleBridgePlus, the easy picture

This is a helper the engineer uses BEFORE the show to set up the music computer. Nobody uses it during the show.

```mermaid
flowchart TD
    A["Engineer"] --> B["asks the AI helper"]
    B --> C["AbleBridgePlus (this tool)"]
    C --> D["Ableton Live music computer"]
    D --> E["ready for the show"]
    D -. "at show time" .-> F["At the show, AbleSet (the setlist) takes over"]
    F --> G["Band member enjoys the show - no AI, no this tool"]

    classDef person fill:#d4f4dd,stroke:#2e8b57,color:#1b3a2a;
    classDef helper fill:#d9ecff,stroke:#2f6fed,color:#12294f;
    classDef computer fill:#ffe6cc,stroke:#e07b00,color:#4a2b00;
    classDef showtime fill:#eeeeee,stroke:#999999,color:#333333;

    class A person;
    class B,C helper;
    class D computer;
    class E,F,G showtime;
```

*Before the show: the engineer asks the AI helper, which uses this tool to get the music computer ready. At the show: the setlist app takes over, and neither the AI nor this tool is used.*

| Who | When | Uses this? |
| --- | --- | --- |
| Engineer | Before the show | Yes — sets it up |
| AI helper | Only before the show | Yes — helps the engineer |
| Band member | During the show | No — never touches it |

> **A note about safety:** This tool can change the music computer's settings. We made it careful — it shows a preview first and can undo.

Want more detail? See the [bigger diagram](BRIDGE-DIAGRAMS.md) and the [picture of how the pieces fit together](images/bridge-layers.svg).
