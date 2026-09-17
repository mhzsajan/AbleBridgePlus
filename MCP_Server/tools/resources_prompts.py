"""MCP resources & prompts for AbleBridgePlus (v0.6 theme 2).

The custom TCP transport originally served tools only. This module adds the
two other MCP surfaces:

- **Resources** — live session state readable via ``resources/read`` so clients
  can pull context without spending tool calls: session summary, per-track
  detail, the change journal, the checkpoint store, and studio memory.
- **Prompts** — reusable expert-workflow templates (mix review, song doctor,
  arrange my ideas, match my reference). One click in Claude Desktop /
  OpenCode hands the AI a full plan.

Resources are served directly by MCP_Server/server.py (which imports
list_resources / read_resource / list_prompts / get_prompt from here); they
deliberately bypass the FastMCP tool shim.
"""
import json
import logging
import os
import time
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _get_conn():
    """Return the live Ableton connection (never dials Live itself)."""
    from MCP_Server.connections.ableton import get_ableton_connection
    return get_ableton_connection()


def _call(conn, command: str, params: Dict[str, Any] = None) -> Any:
    """send_command returns the result payload directly and raises
    CommandError on handler failures — pass it through untouched."""
    return conn.send_command(command, params or {})


def _journal_path():
    return os.path.join(os.path.expanduser("~"), ".ablebridge", "journal.jsonl")


# --------------------------------------------------------------------------
# Resources
# --------------------------------------------------------------------------


def _res_session_summary() -> str:
    conn = _get_conn()
    info = _call(conn, "get_session_info")
    tracks = _call(conn, "get_all_tracks_info").get("tracks", [])
    compact = {
        "tempo": info.get("tempo"),
        "time_signature": info.get("time_signature", "4/4"),
        "track_count": len(tracks),
        "tracks": [
            {"index": i, "name": t.get("name"), "type": t.get("type", ""),
             "volume": t.get("volume"), "panning": t.get("panning"),
             "muted": t.get("muted"), "arm": t.get("arm")}
            for i, t in enumerate(tracks)
        ],
        "scenes": info.get("scene_count"),
    }
    return json.dumps(compact, indent=2)


def _res_track(index: int) -> str:
    conn = _get_conn()
    info = _call(conn, "get_track_info", {"track_index": index})
    try:
        meters = _call(conn, "get_track_meters", {"track_index": index})
        if isinstance(meters, dict):
            info["meters"] = {
                k: meters.get(k) for k in
                ("output_meter_left", "output_meter_right", "output_meter_level")
                if meters.get(k) is not None
            }
    except Exception:
        pass
    return json.dumps(info, indent=2)


def _res_journal() -> str:
    path = _journal_path()
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[-50:]
        entries = []
        for line in lines:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return json.dumps({"recent_changes": entries, "count": len(entries)}, indent=2)
    except FileNotFoundError:
        return json.dumps({"recent_changes": [], "count": 0,
                           "note": "no changes recorded yet"}, indent=2)


def _res_checkpoints() -> str:
    from MCP_Server import checkpoints
    return json.dumps(checkpoints.list_all(), indent=2)


def _res_memory() -> str:
    from MCP_Server.tools.studio_memory import load_memory
    return json.dumps(load_memory(), indent=2)


def _resource_descriptors() -> List[Dict[str, Any]]:
    return [
        {
            "uri": "ableton://session/summary",
            "name": "Session summary",
            "description": "Tempo, time signature, scene count and every track "
                           "(name, type, volume, pan, mute, arm) in one compact read.",
            "mimeType": "application/json",
        },
        {
            "uri": "ableton://journal",
            "name": "Change journal",
            "description": "The last 50 mutations made through AbleBridgePlus "
                           "(tool, arguments, status, timestamp).",
            "mimeType": "application/json",
        },
        {
            "uri": "ableton://checkpoints",
            "name": "Checkpoints",
            "description": "Named and automatic checkpoints available for rollback/restore.",
            "mimeType": "application/json",
        },
        {
            "uri": "ableton://memory",
            "name": "Studio memory",
            "description": "Persisted preferences and notes the AI has stored about your studio.",
            "mimeType": "application/json",
        },
        {
            "uriTemplate": "ableton://track/{index}",
            "name": "Track detail",
            "description": "Full info for one track by zero-based index: mixer, devices, "
                           "clip slots and live meters.",
            "mimeType": "application/json",
        },
    ]


def list_resources() -> List[Dict[str, Any]]:
    return _resource_descriptors()


def read_resource(uri: str) -> Dict[str, Any]:
    if uri == "ableton://session/summary":
        text = _res_session_summary()
    elif uri == "ableton://journal":
        text = _res_journal()
    elif uri == "ableton://checkpoints":
        text = _res_checkpoints()
    elif uri == "ableton://memory":
        text = _res_memory()
    elif uri.startswith("ableton://track/"):
        try:
            index = int(uri.rsplit("/", 1)[1])
        except ValueError:
            raise ValueError("track index must be an integer: " + uri)
        text = _res_track(index)
    else:
        raise ValueError("Unknown resource: " + uri)
    return {"contents": [{"uri": uri, "mimeType": "application/json", "text": text}]}


# --------------------------------------------------------------------------
# Prompts
# --------------------------------------------------------------------------


def _try_hydrate() -> str:
    """Best-effort current session snapshot for prompt text; '' when offline."""
    try:
        return _res_session_summary()
    except Exception:
        return ""


_PROMPTS: Dict[str, Dict[str, Any]] = {
    "mix-review": {
        "title": "Mix review",
        "description": "Full expert review of the current mix: balance, stereo, "
                       "frequency, dynamics — with concrete fixes you can apply.",
        "arguments": [
            {"name": "focus", "description": "Optional focus, e.g. 'low end', 'vocals'",
             "required": False},
        ],
        "build": lambda a: (
            "You are an experienced mix engineer working inside Ableton Live via AbleBridgePlus.\n"
            "Review the current mix"
            + (" with special focus on: %s." % a["focus"] if a.get("focus") else "")
            + "\n\nSteps:\n"
              "1. Read the session overview (get_session_info, get_all_tracks_info) to understand the set.\n"
              "2. For each important track call get_track_meters while playing to see real levels.\n"
              "3. Check for: tracks clipping or far too quiet, level imbalance between similar "
              "elements, mono/stereo issues, muted or unaccounted-for tracks, extreme panning.\n"
              "4. Propose concrete fixes as tool calls (set_track_volume, set_track_panning, "
              "device parameter tweaks) — one batch of small, reversible moves.\n"
              "5. Automatic checkpoints are on: mutations are reversible via rollback, so act "
              "confidently but explain each change.\n\n"
            "Deliver: findings (with numbers), then the exact fixes you applied or propose.\n"
            + ("\nCurrent session snapshot:\n```json\n%s\n```" % _try_hydrate()
               if _try_hydrate() else "(Live offline — ask to connect first.)")
        ),
    },
    "song-doctor": {
        "title": "Song doctor",
        "description": "Diagnose why the track isn't working: arrangement, energy, "
                       "mix and 'something feels off' complaints.",
        "arguments": [
            {"name": "complaint",
             "description": "What feels wrong, e.g. 'chorus has no energy'",
             "required": False},
        ],
        "build": lambda a: (
            "You are a song doctor inside Ableton Live via AbleBridgePlus.\n"
            "The patient complaint: "
            + (a.get("complaint") or "it just doesn't grab me — find out why")
            + "\n\nSteps:\n"
              "1. Run the doctor tool first — rule out technical problems (connection, drift, ports).\n"
              "2. Map the material: get_all_tracks_info, get_scenes, arrangement overview if used.\n"
              "3. Diagnose across layers: arrangement (does anything change every 8–16 bars?), "
              "energy curve (what plays in the busiest section vs. the chorus?), "
              "tonal (clashing keys/scales), and mix (masking, mud, missing glue).\n"
              "4. Give a ranked list of the 3 most likely causes with the evidence you saw.\n"
              "5. Offer to fix the top cause right now via tools (checkpoints make it safe) and "
              "name the exact calls you would make.\n"
            + ("\nCurrent session snapshot:\n```json\n%s\n```" % _try_hydrate()
               if _try_hydrate() else "(Live offline — ask to connect first.)")
        ),
    },
    "arrange-my-ideas": {
        "title": "Arrange my ideas",
        "description": "Turn loose clips and scenes into a structured arrangement "
                       "with intro / verses / chorus / drop / outro.",
        "arguments": [
            {"name": "genre", "description": "Target genre or vibe", "required": False},
            {"name": "length_bars", "description": "Target length in bars, e.g. 128",
             "required": False},
        ],
        "build": lambda a: (
            "You are a producer/arranger working inside Ableton Live via AbleBridgePlus.\n"
            "Turn the user's existing clips and scenes into a finished arrangement"
            + (" in a %s style" % a["genre"] if a.get("genre") else "")
            + (" of about %s bars." % a["length_bars"] if a.get("length_bars") else ".")
            + "\n\nSteps:\n"
              "1. Inventory the material: get_all_tracks_info and every scene/clip name.\n"
              "2. Group clips by function (drums / bass / chords / lead / fx) by listening "
              "structure: which are loopable bodies, which are transitions, which are one-shots.\n"
              "3. Propose a section map (intro, verse, build, drop/chorus, break, outro) with "
              "bar counts totalling the target length.\n"
              "4. Build it with tools: create/rename scenes, duplicate_clip_to_arrangement or "
              "fire_scenes in order; set scene tempo changes if the style wants them.\n"
              "5. Finish with the first 2 sections actually placed in the arrangement and a "
              "summary of what the user should listen for.\n"
            + ("\nCurrent session snapshot:\n```json\n%s\n```" % _try_hydrate()
               if _try_hydrate() else "(Live offline — ask to connect first.)")
        ),
    },
    "match-my-reference": {
        "title": "Match my reference",
        "description": "Compare the mix against a reference track and close the "
                       "tonal/loudness gap with concrete fixes.",
        "arguments": [
            {"name": "reference_path", "description": "Path to the reference audio file",
             "required": True},
            {"name": "track_index", "description": "Optional: match one track instead of the whole mix",
             "required": False},
        ],
        "build": lambda a: (
            "You are a mastering-savvy mix engineer inside Ableton Live via AbleBridgePlus.\n"
            "Goal: make the user's mix"
            + (" (track %s)" % a["track_index"] if a.get("track_index") else "")
            + " sit closer to their reference: " + str(a.get("reference_path"))
            + "\n\nSteps:\n"
              "1. Analyze the reference with analyze_reference_track (or analyze_reference_mix "
              "for whole-mix comparison) to get its tonal balance and loudness profile.\n"
              "2. Measure the user's side: play the section and read meters "
              "(get_track_meters / get_master_meters sampling over ~10 seconds).\n"
              "3. Report the gaps in plain numbers ('3 dB light below 100 Hz', 'vocal 2 dB hot').\n"
              "4. Propose and apply small EQ/gain moves via tools to close the biggest gaps — "
              "checkpoints and rollback make it safe; re-measure after applying.\n"
              "5. Summarize what changed and what remains for the user's ears to judge.\n"
            + ("\nCurrent session snapshot:\n```json\n%s\n```" % _try_hydrate()
               if _try_hydrate() else "(Live offline — ask to connect first.)")
        ),
    },
}


def list_prompts() -> List[Dict[str, Any]]:
    out = []
    for name, spec in _PROMPTS.items():
        out.append({
            "name": name,
            "title": spec["title"],
            "description": spec["description"],
            "arguments": spec["arguments"],
        })
    return out


def get_prompt(name: str, arguments: Dict[str, str] = None) -> Dict[str, Any]:
    spec = _PROMPTS.get(name)
    if not spec:
        raise ValueError("Unknown prompt: " + name)
    arguments = arguments or {}
    known = {a["name"] for a in spec["arguments"]}
    for key in arguments:
        if key not in known:
            raise ValueError("Unknown argument '%s' for prompt %s" % (key, name))
    for a in spec["arguments"]:
        if a.get("required") and not arguments.get(a["name"]):
            raise ValueError("Missing required argument '%s'" % a["name"])
    text = spec["build"](arguments)
    return {"description": spec["description"],
            "messages": [{"role": "user",
                          "content": {"type": "text", "text": text}}]}
