"""
Global State Management for AbleBridge++ MCP Server.
"""

import json
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


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
        self.cache_dir = os.path.join(os.path.expanduser("~"), ".enhanced-abletonbridge", "cache")
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
