"""
Constants for Enhanced AbletonBridge MCP Server.
"""

import os
from typing import Dict, List, Tuple

# Server Configuration
# Version lives in one place (MCP_Server.version) and is imported here so the
# MCP handshake, the `get_server_capabilities` tool and the packaged metadata
# can never disagree. They previously reported 0.3.0 / 0.5.0 / 0.7.0 from the
# same process.
from MCP_Server.version import __version__ as _VERSION  # noqa: E402

SERVER_NAME = "AbleBridgePlus"
SERVER_VERSION = _VERSION
# Newest MCP revision this server implements. _handle_initialize negotiates
# against this instead of hardcoding a literal.
PROTOCOL_VERSION = "2024-11-05"
# Revisions we can still speak if the client asks for something newer.
SUPPORTED_PROTOCOL_VERSIONS = ("2024-11-05", "2025-03-26", "2025-06-18")

# Default Ports
ABLETON_TCP_PORT = 9877
ABLETON_UDP_PORT = 9882
M4L_OSC_IN_PORT = 9878
M4L_OSC_OUT_PORT = 9879
WEB_DASHBOARD_PORT = 9880

# Default Hosts
LOCALHOST = "localhost"
LOCALHOST_IP = "127.0.0.1"

# Connection Settings
TCP_TIMEOUT = 5.0
UDP_TIMEOUT = 1.0
RECONNECT_DELAY = 2.0
MAX_RECONNECT_ATTEMPTS = 5

# Chunked Response Settings
MAX_CHUNK_SIZE = 32000  # 32KB per chunk
CHUNK_OVERHEAD = 100  # Overhead for JSON metadata

# Tool Settings
MAX_NOTES_PER_CALL = 10000
MAX_AUTOMATION_POINTS = 500
MAX_BATCH_PARAMETERS = 200
MAX_BATCH_TRACKS = 50

# Time Settings
BEATS_PER_QUARTER = 1.0
SECONDS_PER_MINUTE = 60.0

# MIDI Settings
MIDI_NOTE_MIN = 0
MIDI_NOTE_MAX = 127
MIDI_VELOCITY_MIN = 1
MIDI_VELOCITY_MAX = 127
MIDI_CC_MIN = 0
MIDI_CC_MAX = 127

# Track Types
TRACK_TYPE_AUDIO = "audio"
TRACK_TYPE_MIDI = "midi"
TRACK_TYPE_RETURN = "return"
TRACK_TYPE_MASTER = "master"
TRACK_TYPE_GROUP = "group"

# Clip States
CLIP_STATE_STOPPED = "stopped"
CLIP_STATE_PLAYING = "playing"
CLIP_STATE_TRIGGERED = "triggered"
CLIP_STATE_QUEUED = "queued"

# Device Types
DEVICE_TYPE_INSTRUMENT = "instrument"
DEVICE_TYPE_AUDIO_EFFECT = "audio_effect"
DEVICE_TYPE_MIDI_EFFECT = "midi_effect"
DEVICE_TYPE_PLUGIN = "plugin"
DEVICE_TYPE_MAX_FOR_LIVE = "max_for_live"

# Warp Modes
WARP_MODE_BEATS = "beats"
WARP_MODE_TONES = "tones"
WARP_MODE_TEXTURE = "texture"
WARP_MODE_RE_PITCH = "re_pitch"
WARP_MODE_COMPLEX = "complex"
WARP_MODE_COMPLEX_PRO = "complex_pro"

# Automation Modes
AUTOMATION_MODE_NONE = 0
AUTOMATION_MODE_ACTIVE = 1
AUTOMATION_MODE_OVERRIDDEN = 2

# Pan Modes
PAN_MODE_STEREO = 0
PAN_MODE_SPLIT_STEREO = 1

# Monitoring Modes
MONITORING_MODE_IN = 0
MONITORING_MODE_AUTO = 1
MONITORING_MODE_OFF = 2

# Launch Modes
LAUNCH_MODE_TRIGGER = 0
LAUNCH_MODE_GATE = 1
LAUNCH_MODE_TOGGLE = 2
LAUNCH_MODE_REPEAT = 3

# Quantization Values
QUANTIZATION_NONE = 0
QUANTIZATION_8_BARS = 1
QUANTIZATION_4_BARS = 2
QUANTIZATION_2_BARS = 3
QUANTIZATION_BAR = 4
QUANTIZATION_HALF = 5
QUANTIZATION_HALF_TRIPLET = 6
QUANTIZATION_QUARTER = 7
QUANTIZATION_QUARTER_TRIPLET = 8
QUANTIZATION_EIGHTH = 9
QUANTIZATION_EIGHTH_TRIPLET = 10
QUANTIZATION_SIXTEENTH = 11
QUANTIZATION_SIXTEENTH_TRIPLET = 12
QUANTIZATION_THIRTYSECOND = 13
QUANTIZATION_GLOBAL = 14

# Follow Action Types
FOLLOW_ACTION_NONE = 0
FOLLOW_ACTION_STOP = 1
FOLLOW_ACTION_AGAIN = 2
FOLLOW_ACTION_PREVIOUS = 3
FOLLOW_ACTION_NEXT = 4
FOLLOW_ACTION_FIRST = 5
FOLLOW_ACTION_LAST = 6
FOLLOW_ACTION_ANY = 7
FOLLOW_ACTION_OTHER = 8
FOLLOW_ACTION_JUMP = 9

# Colors (Ableton color palette indices)
COLORS = {
    'none': -1,
    'dark_gray': 0,
    'medium_gray': 1,
    'light_gray': 2,
    'white': 3,
    'red': 4,
    'orange': 5,
    'yellow': 6,
    'green': 7,
    'cyan': 8,
    'blue': 9,
    'purple': 10,
    'pink': 11,
    'brown': 12,
    'dark_red': 13,
    'dark_orange': 14,
    'dark_yellow': 15,
    'dark_green': 16,
    'dark_cyan': 17,
    'dark_blue': 18,
    'dark_purple': 19,
    'dark_pink': 20,
    'dark_brown': 21,
    'light_red': 22,
    'light_orange': 23,
    'light_yellow': 24,
    'light_green': 25,
    'light_cyan': 26,
    'light_blue': 27,
    'light_purple': 28,
    'light_pink': 29,
    'light_brown': 30,
    'red_orange': 31,
    'orange_yellow': 32,
    'yellow_green': 33,
    'green_cyan': 34,
    'cyan_blue': 35,
    'blue_purple': 36,
    'purple_pink': 37,
    'pink_red': 38,
    'red_purple': 39,
    'orange_red': 40,
    'yellow_orange': 41,
    'green_yellow': 42,
    'cyan_green': 43,
    'blue_cyan': 44,
    'purple_blue': 45,
    'pink_purple': 46,
    'red_pink': 47,
    'red_brown': 48,
    'orange_brown': 49,
    'yellow_brown': 50,
    'green_brown': 51,
    'cyan_brown': 52,
    'blue_brown': 53,
    'purple_brown': 54,
    'pink_brown': 55,
    'red_dark': 56,
    'orange_dark': 57,
    'yellow_dark': 58,
    'green_dark': 59,
    'cyan_dark': 60,
    'blue_dark': 61,
    'purple_dark': 62,
    'pink_dark': 63,
    'red_light': 64,
    'orange_light': 65,
    'yellow_light': 66,
    'green_light': 67,
    'cyan_light': 68,
    'blue_light': 69,
}

# Error Codes
ERROR_CODE_INVALID_PARAMS = -32602
ERROR_CODE_METHOD_NOT_FOUND = -32601
ERROR_CODE_INTERNAL_ERROR = -32603
ERROR_CODE_CONNECTION_ERROR = -32000
ERROR_CODE_TIMEOUT_ERROR = -32001

# Error Messages
ERROR_MESSAGES = {
    ERROR_CODE_INVALID_PARAMS: "Invalid parameters",
    ERROR_CODE_METHOD_NOT_FOUND: "Method not found",
    ERROR_CODE_INTERNAL_ERROR: "Internal error",
    ERROR_CODE_CONNECTION_ERROR: "Connection error",
    ERROR_CODE_TIMEOUT_ERROR: "Timeout error",
}

# Cache Settings
CACHE_EXPIRY_SECONDS = 300  # 5 minutes
MAX_CACHE_SIZE_MB = 100

# Performance Settings
MAX_CPU_WARNING = 80.0
MAX_MEMORY_WARNING = 80.0
MAX_LATENCY_WARNING = 50.0

# Video Integration (Videosync2)
VIDEOSYNC_DEFAULT_PORT = 9881
VIDEOSYNC_SPOUT_PORT = 5000

# Setlist Integration (AbleSet)
ABLESET_DEFAULT_PORT = 9882
ABLESET_SETLIST_FILE = "setlist.json"

# Live Show Settings
LIVE_SHOW_PRESETS_DIR = "presets"
LIVE_SHOW_TEMPLATE_DIR = "templates"

# ---------------------------------------------------------------------------
# Command delay tiers (used by AbletonConnection.send_command)
# ---------------------------------------------------------------------------

# Tier 0: No delay -- simple state changes
TIER_0_COMMANDS: frozenset = frozenset([
    "set_tempo", "set_track_name", "rename_return", "set_clip_name", "set_track_color",
    "set_clip_color", "set_track_mute", "set_track_solo", "set_track_arm",
    "set_metronome", "set_track_pan", "set_track_volume",
    "set_return_track_volume", "set_return_track_pan", "set_track_send",
    "set_master_volume", "start_playback", "stop_playback",
    "undo", "redo", "set_song_time", "set_song_loop",
    "set_clip_looping", "set_device_parameter", "set_device_enabled",
    "fire_clip", "stop_clip", "fire_scene",
    "select_scene", "select_track", "set_detail_clip",
    "set_track_fold", "set_crossfade_assign",
    "set_track_monitoring", "set_clip_launch_mode",
    "set_clip_launch_quantization", "set_clip_legato",
    "set_scene_name", "set_scene_tempo", "tap_tempo",
    "set_arrangement_overdub", "set_track_routing", "navigate_playback",
    "set_clip_pitch", "set_groove_settings", "set_song_settings",
    "trigger_session_record", "set_or_delete_cue", "jump_to_cue",
    "preview_browser_item", "move_clip_playing_pos",
    "set_transmute_properties", "rack_variation_action",
    "set_return_track_mute", "set_return_track_solo", "set_clip_grid",
])

# Tier 1: Light delay (50ms post-delay only) -- note/clip/automation operations
TIER_1_COMMANDS: frozenset = frozenset([
    "add_notes_to_clip", "add_notes_extended", "remove_notes_range",
    "add_notes_to_arrangement_clip", "create_arrangement_midi_clip",
    "clear_clip_notes", "quantize_clip_notes", "transpose_clip_notes",
    "set_clip_loop_points", "set_clip_start_end",
    "create_clip_automation", "clear_clip_automation",
    "create_track_automation", "clear_track_automation",
    "duplicate_clip", "duplicate_clip_loop", "duplicate_clip_region",
    "crop_clip", "reverse_clip", "set_clip_warp", "set_warp_mode",
    "apply_groove", "set_drum_pad", "copy_drum_pad", "capture_midi",
    "set_compressor_sidechain", "set_eq8_properties",
    "set_simpler_properties", "simpler_sample_action", "manage_sample_slices",
    "set_hybrid_reverb_ir", "duplicate_clip_to_arrangement",
    # v0.8: Videosync2 show automation (arrangement mixer envelopes)
    "set_arrangement_mixer_automation", "clear_arrangement_mixer_automation",
    "program_song_video_automation", "video_failover", "set_video_layer",
])

# Tier 2: Heavy delay (100ms pre + 100ms post) -- structural/loading changes
TIER_2_COMMANDS: frozenset = frozenset([
    "create_midi_track", "create_audio_track", "create_clip",
    "delete_clip", "delete_track", "duplicate_track",
    "create_return_track", "create_scene", "delete_scene",
    "load_instrument_or_effect", "load_sample", "load_drum_kit",
    "load_browser_item", "load_device_on_return",
    "group_tracks", "freeze_track", "unfreeze_track",
    "audio_to_midi", "create_midi_track_with_simpler",
    "sliced_simpler_to_drum_rack", "delete_device",
    "delete_time", "duplicate_time", "insert_silence",
    "arm_track", "disarm_track",
    "start_arrangement_recording", "stop_arrangement_recording",
    "set_loop_start", "set_loop_end", "set_loop_length", "set_playback_position",
    "save_song",
])

# Combined set of all modifying commands (union of all tiers)
MODIFYING_COMMANDS: frozenset = TIER_0_COMMANDS | TIER_1_COMMANDS | TIER_2_COMMANDS

# Per-command timeout overrides for legitimately slow operations.
# Used by send_command() when the caller doesn't specify a timeout.
SLOW_COMMAND_TIMEOUTS: Dict[str, float] = {
    "load_instrument_or_effect": 30.0,
    "load_sample": 30.0,
    "load_drum_kit": 30.0,
    "freeze_track": 60.0,
    "unfreeze_track": 30.0,
    "audio_to_midi": 30.0,
    "get_browser_items_at_path": 20.0,
}

# ---------------------------------------------------------------------------
# Browser categories
# ---------------------------------------------------------------------------

# Root browser categories: (path_root, display_name)
# path_root uses the lowercase attribute name so paths work directly with
# get_browser_items_at_path (which lowercases the first component).
BROWSER_CATEGORIES: List[Tuple[str, str]] = [
    ("instruments", "Instruments"),
    ("drums", "Drums"),
    ("audio_effects", "Audio Effects"),
    ("midi_effects", "MIDI Effects"),
    ("max_for_live", "Max for Live"),
    ("plugins", "Plug-ins"),
    ("user_library", "User Library"),
]

BROWSER_CACHE_MAX_DEPTH: int = 3    # category/device/subcategory (skip preset files)
BROWSER_CACHE_MAX_ITEMS: int = 1500

# Maps category keys to display names (used by search_browser and get_browser_tree)
CATEGORY_DISPLAY: Dict[str, str] = {
    "instruments": "Instruments",
    "sounds": "Sounds",
    "drums": "Drums",
    "audio_effects": "Audio Effects",
    "midi_effects": "MIDI Effects",
    "max_for_live": "Max for Live",
    "plugins": "Plug-ins",
    "clips": "Clips",
    "samples": "Samples",
    "packs": "Packs",
    "user_library": "User Library",
}

# Category priority for resolving name collisions in device_uri_map.
# Lower number = higher priority (stock devices beat preset folders).
CATEGORY_PRIORITY: Dict[str, int] = {
    "Instruments": 0,
    "Audio Effects": 1,
    "MIDI Effects": 2,
    "Max for Live": 3,
    "Plug-ins": 4,
    "Sounds": 5,
    "Drums": 6,
    "Clips": 7,
    "Samples": 8,
    "Packs": 9,
    "User Library": 10,
}

# ---------------------------------------------------------------------------
# Browser disk cache
# ---------------------------------------------------------------------------

BROWSER_CACHE_TTL: float = 604800.0          # 7 days -- only refresh_browser_cache forces a rescan
BROWSER_DISK_CACHE_MAX_AGE: float = 604800.0  # 7 days -- disk cache ignored if older

BROWSER_DISK_CACHE_DIR: str = os.path.join(os.path.expanduser("~"), ".ableton-bridge")
BROWSER_DISK_CACHE_PATH: str = os.path.join(BROWSER_DISK_CACHE_DIR, "browser_cache.json.gz")
BROWSER_DISK_CACHE_PATH_LEGACY: str = os.path.join(BROWSER_DISK_CACHE_DIR, "browser_cache.json")
CHAIN_TEMPLATES_PATH: str = os.path.join(BROWSER_DISK_CACHE_DIR, "chain_templates.json")
