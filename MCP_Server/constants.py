"""
Constants for Enhanced AbletonBridge MCP Server.
"""

# Server Configuration
SERVER_NAME = "AbleBridge++"
SERVER_VERSION = "0.3.0"
PROTOCOL_VERSION = "2024-11-05"

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
