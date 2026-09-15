"""
Global State Management for AbleBridge++ MCP Server.
"""

import json
import os
import socket
import threading
from collections import deque
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

# ---------------------------------------------------------------------------
# Module-level state (shared by the ported tool modules via
# ``import MCP_Server.state as state``).  Accessors like
# get_ableton_connection() / get_m4l_connection() read and write these.
# ---------------------------------------------------------------------------

# Connection state
ableton_connection: Optional[Any] = None  # AbletonConnection | None
m4l_connection: Optional[Any] = None      # M4LConnection | None

# Feature stores (in-memory, lost on restart)
snapshot_store: Dict[str, Dict[str, Any]] = {}
macro_store: Dict[str, Dict[str, Any]] = {}
param_map_store: Dict[str, Dict[str, Any]] = {}
effect_chain_store: Dict[str, Dict[str, Any]] = {}
store_lock: threading.Lock = threading.Lock()

# Dashboard / telemetry state
server_start_time: float = 0.0
tool_call_log: deque = deque(maxlen=500)
tool_call_counts: Dict[str, int] = {}
tool_call_lock: threading.Lock = threading.Lock()
dashboard_server: Optional[Any] = None  # uvicorn.Server | None
server_log_buffer: deque = deque(maxlen=1000)
server_log_lock: threading.Lock = threading.Lock()

# Browser cache
browser_cache_flat: List[Dict[str, Any]] = []           # flat list for fast substring search
browser_cache_by_category: Dict[str, List[Dict[str, Any]]] = {}  # display_name -> items
browser_cache_timestamp: float = 0.0
browser_cache_lock: threading.Lock = threading.Lock()
browser_cache_populating: bool = False                   # prevents duplicate scans
device_uri_map: Dict[str, str] = {}                      # lowercase name -> URI

# Events
browser_cache_ready: threading.Event = threading.Event()   # set when cache populated
ableton_connected_event: threading.Event = threading.Event()  # set on first connect

# M4L ping cache
m4l_ping_cache: Dict[str, Any] = {"result": False, "timestamp": 0.0}
M4L_PING_CACHE_TTL: float = 5.0

# M4L bridge version (populated after successful ping)
m4l_bridge_version: str = ""

# Config (from environment or defaults)
DASHBOARD_PORT: int = int(os.environ.get("ABLETON_BRIDGE_DASHBOARD_PORT", "9880"))
SINGLETON_LOCK_PORT: int = int(os.environ.get("ABLETON_BRIDGE_LOCK_PORT", "9881"))

# Singleton lock
singleton_lock_sock: Optional[socket.socket] = None

# MCP server instance (set by server.py after creating the FastMCP object)
mcp_instance: Optional[Any] = None  # FastMCP | None


@dataclass
class ConnectionState:
    """Connection state information."""
    ableton_connected: bool = False
    m4l_connected: bool = False
    ableton_host: str = "localhost"
    ableton_port: int = 9877
    m4l_host: str = "localhost"
    m4l_port: int = 9878
    last_connected: Optional[datetime] = None
    last_disconnected: Optional[datetime] = None


@dataclass
class SessionState:
    """Session state information."""
    session_name: str = ""
    tempo: float = 120.0
    time_signature_numerator: int = 4
    time_signature_denominator: int = 4
    is_playing: bool = False
    is_recording: bool = False
    current_time: float = 0.0
    track_count: int = 0
    scene_count: int = 0
    last_updated: Optional[datetime] = None


@dataclass
class PerformanceState:
    """Performance monitoring state."""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    latency: float = 0.0
    buffer_size: int = 0
    sample_rate: int = 44100
    last_measured: Optional[datetime] = None


class GlobalState:
    """Global state manager for the MCP server."""
    
    def __init__(self):
        """Initialize global state."""
        self.connection = ConnectionState()
        self.session = SessionState()
        self.performance = PerformanceState()
        
        # Cache directory
        self.cache_dir = os.path.join(os.path.expanduser("~"), ".ablebridge", "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load cached state if available
        self._load_cache()
    
    def _load_cache(self):
        """Load cached state from disk."""
        cache_file = os.path.join(self.cache_dir, "state.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    # Update state from cache
                    if 'session' in cache_data:
                        for key, value in cache_data['session'].items():
                            if hasattr(self.session, key):
                                setattr(self.session, key, value)
            except Exception as e:
                print(f"Warning: Could not load cache: {e}")
    
    def _save_cache(self):
        """Save state to disk cache."""
        cache_file = os.path.join(self.cache_dir, "state.json")
        try:
            cache_data = {
                'session': {
                    'session_name': self.session.session_name,
                    'tempo': self.session.tempo,
                    'time_signature_numerator': self.session.time_signature_numerator,
                    'time_signature_denominator': self.session.time_signature_denominator,
                    'last_updated': self.session.last_updated.isoformat() if self.session.last_updated else None
                }
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")
    
    def update_connection(self, ableton_connected: bool, m4l_connected: bool):
        """Update connection state."""
        self.connection.ableton_connected = ableton_connected
        self.connection.m4l_connected = m4l_connected
        
        if ableton_connected or m4l_connected:
            self.connection.last_connected = datetime.now()
        else:
            self.connection.last_disconnected = datetime.now()
    
    def update_session(self, **kwargs):
        """Update session state."""
        for key, value in kwargs.items():
            if hasattr(self.session, key):
                setattr(self.session, key, value)
        
        self.session.last_updated = datetime.now()
        self._save_cache()
    
    def update_performance(self, **kwargs):
        """Update performance state."""
        for key, value in kwargs.items():
            if hasattr(self.performance, key):
                setattr(self.performance, key, value)
        
        self.performance.last_measured = datetime.now()
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state as dictionary."""
        return {
            'connection': {
                'ableton_connected': self.connection.ableton_connected,
                'm4l_connected': self.connection.m4l_connected,
                'ableton_host': self.connection.ableton_host,
                'ableton_port': self.connection.ableton_port,
                'm4l_host': self.connection.m4l_host,
                'm4l_port': self.connection.m4l_port,
                'last_connected': self.connection.last_connected.isoformat() if self.connection.last_connected else None,
                'last_disconnected': self.connection.last_disconnected.isoformat() if self.connection.last_disconnected else None
            },
            'session': {
                'session_name': self.session.session_name,
                'tempo': self.session.tempo,
                'time_signature_numerator': self.session.time_signature_numerator,
                'time_signature_denominator': self.session.time_signature_denominator,
                'is_playing': self.session.is_playing,
                'is_recording': self.session.is_recording,
                'current_time': self.session.current_time,
                'track_count': self.session.track_count,
                'scene_count': self.session.scene_count,
                'last_updated': self.session.last_updated.isoformat() if self.session.last_updated else None
            },
            'performance': {
                'cpu_usage': self.performance.cpu_usage,
                'memory_usage': self.performance.memory_usage,
                'latency': self.performance.latency,
                'buffer_size': self.performance.buffer_size,
                'sample_rate': self.performance.sample_rate,
                'last_measured': self.performance.last_measured.isoformat() if self.performance.last_measured else None
            }
        }
    
    def is_ready(self) -> bool:
        """Check if the server is ready to accept requests."""
        return self.connection.ableton_connected or self.connection.m4l_connected
