"""
Performance Analytics Tools for AbleBridgePlus MCP Server.

Provides session statistics, performance tracking, and analytics.
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from . import tool


class PerformanceAnalytics:
    """Performance analytics manager."""
    
    def __init__(self):
        """Initialize performance analytics."""
        self.session_start_time = None
        self.song_timings = []
        self.current_song_start = None
        self.mix_history = []
        self.peak_levels = {}
        self.average_levels = {}
        self.cpu_history = []
        self.memory_history = []
    
    def start_session(self) -> Dict[str, Any]:
        """Start tracking session."""
        self.session_start_time = time.time()
        return {
            "status": "session_started",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        if self.session_start_time is None:
            return {"status": "no_active_session"}
        
        elapsed = time.time() - self.session_start_time
        return {
            "session_duration": elapsed,
            "session_duration_formatted": self._format_time(elapsed),
            "songs_played": len(self.song_timings),
            "session_start": datetime.fromtimestamp(self.session_start_time).isoformat()
        }
    
    def start_song_timer(self, song_name: str) -> Dict[str, Any]:
        """Start timer for a song."""
        self.current_song_start = time.time()
        return {
            "status": "song_timer_started",
            "song_name": song_name,
            "timestamp": datetime.now().isoformat()
        }
    
    def stop_song_timer(self, song_name: str) -> Dict[str, Any]:
        """Stop timer for a song."""
        if self.current_song_start is None:
            return {"status": "no_song_timer_running"}
        
        duration = time.time() - self.current_song_start
        timing = {
            "song_name": song_name,
            "duration": duration,
            "duration_formatted": self._format_time(duration),
            "timestamp": datetime.now().isoformat()
        }
        self.song_timings.append(timing)
        self.current_song_start = None
        
        return {
            "status": "song_timer_stopped",
            "timing": timing
        }
    
    def get_song_timings(self) -> List[Dict[str, Any]]:
        """Get all song timings."""
        return self.song_timings
    
    def record_mix_change(self, change: Dict[str, Any]) -> Dict[str, Any]:
        """Record a mix change."""
        entry = {
            **change,
            "timestamp": datetime.now().isoformat()
        }
        self.mix_history.append(entry)
        return {"status": "mix_change_recorded", "entry": entry}
    
    def get_mix_history(self) -> List[Dict[str, Any]]:
        """Get mix change history."""
        return self.mix_history
    
    def record_peak_level(self, track_index: int, level: float) -> None:
        """Record peak level for a track."""
        if track_index not in self.peak_levels or level > self.peak_levels[track_index]:
            self.peak_levels[track_index] = level
    
    def get_peak_levels(self) -> Dict[int, float]:
        """Get peak levels for all tracks."""
        return self.peak_levels
    
    def record_cpu_usage(self, usage: float) -> None:
        """Record CPU usage."""
        self.cpu_history.append({
            "usage": usage,
            "timestamp": datetime.now().isoformat()
        })
        # Keep last 1000 entries
        if len(self.cpu_history) > 1000:
            self.cpu_history = self.cpu_history[-1000:]
    
    def get_cpu_history(self) -> List[Dict[str, Any]]:
        """Get CPU usage history."""
        return self.cpu_history
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# Global instance
_analytics = PerformanceAnalytics()


@tool(
    name="start_session_tracking",
    description="Start tracking session statistics",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def start_session_tracking() -> Dict[str, Any]:
    """Start tracking session statistics."""
    return _analytics.start_session()


@tool(
    name="get_session_stats",
    description="Get current session statistics",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def get_session_stats() -> Dict[str, Any]:
    """Get current session statistics."""
    return _analytics.get_session_stats()


@tool(
    name="start_performance_timer",
    description="Start timer for a specific song",
    input_schema={
        "type": "object",
        "properties": {
            "song_name": {
                "type": "string",
                "description": "Name of the song"
            }
        },
        "required": ["song_name"]
    }
)
async def start_performance_timer(song_name: str) -> Dict[str, Any]:
    """Start timer for a specific song."""
    return _analytics.start_song_timer(song_name)


@tool(
    name="stop_performance_timer",
    description="Stop timer for a specific song",
    input_schema={
        "type": "object",
        "properties": {
            "song_name": {
                "type": "string",
                "description": "Name of the song"
            }
        },
        "required": ["song_name"]
    }
)
async def stop_performance_timer(song_name: str) -> Dict[str, Any]:
    """Stop timer for a specific song."""
    return _analytics.stop_song_timer(song_name)


@tool(
    name="get_performance_timings",
    description="Get all recorded song timings",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def get_performance_timings() -> Dict[str, Any]:
    """Get all recorded song timings."""
    timings = _analytics.get_song_timings()
    return {
        "timings": timings,
        "count": len(timings)
    }


@tool(
    name="record_mix_change",
    description="Record a mix change for history tracking",
    input_schema={
        "type": "object",
        "properties": {
            "track_index": {
                "type": "integer",
                "description": "Track index"
            },
            "parameter": {
                "type": "string",
                "description": "Parameter changed"
            },
            "old_value": {
                "description": "Previous value"
            },
            "new_value": {
                "description": "New value"
            }
        },
        "required": ["track_index", "parameter", "new_value"]
    }
)
async def record_mix_change(track_index: int, parameter: str, new_value: Any, old_value: Any = None) -> Dict[str, Any]:
    """Record a mix change for history tracking."""
    return _analytics.record_mix_change({
        "track_index": track_index,
        "parameter": parameter,
        "old_value": old_value,
        "new_value": new_value
    })


@tool(
    name="get_mix_history",
    description="Get mix change history",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def get_mix_history() -> Dict[str, Any]:
    """Get mix change history."""
    history = _analytics.get_mix_history()
    return {
        "history": history,
        "count": len(history)
    }


@tool(
    name="get_peak_levels",
    description="Get peak levels for all tracked tracks",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def get_peak_levels() -> Dict[str, Any]:
    """Get peak levels for all tracked tracks."""
    return {"peak_levels": _analytics.get_peak_levels()}


@tool(
    name="record_cpu_usage",
    description="Record current CPU usage",
    input_schema={
        "type": "object",
        "properties": {
            "usage": {
                "type": "number",
                "description": "CPU usage percentage (0-100)"
            }
        },
        "required": ["usage"]
    }
)
async def record_cpu_usage(usage: float) -> Dict[str, Any]:
    """Record current CPU usage."""
    _analytics.record_cpu_usage(usage)
    return {"status": "cpu_usage_recorded", "usage": usage}


@tool(
    name="get_cpu_history",
    description="Get CPU usage history",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def get_cpu_history() -> Dict[str, Any]:
    """Get CPU usage history."""
    history = _analytics.get_cpu_history()
    return {
        "history": history,
        "count": len(history)
    }
