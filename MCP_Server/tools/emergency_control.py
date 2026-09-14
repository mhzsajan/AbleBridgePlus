"""
Emergency Control Tools for AbleBridge++ MCP Server.

Provides emergency stop, panic mute, and backup scene activation for live shows.
"""

import json
from typing import Any, Dict, List, Optional
from . import tool


class EmergencyControl:
    """Emergency control manager for live shows."""
    
    def __init__(self):
        """Initialize emergency control."""
        self.emergency_active = False
        self.backup_scene_index = None
        self.original_mute_states = {}
    
    def activate_emergency_stop(self) -> Dict[str, Any]:
        """Activate emergency stop - stop all clips and playback."""
        self.emergency_active = True
        return {
            "status": "emergency_stop_activated",
            "message": "All clips stopped and playback halted"
        }
    
    def panic_mute(self, tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mute all tracks instantly."""
        muted_tracks = []
        for track in tracks:
            track_index = track.get("index")
            if track_index is not None:
                self.original_mute_states[track_index] = track.get("mute", False)
                muted_tracks.append(track_index)
        
        return {
            "status": "panic_mute_activated",
            "muted_tracks": muted_tracks,
            "message": f"Muted {len(muted_tracks)} tracks"
        }
    
    def panic_unmute(self) -> Dict[str, Any]:
        """Unmute all tracks."""
        unmuted_tracks = list(self.original_mute_states.keys())
        self.original_mute_states.clear()
        
        return {
            "status": "panic_unmute_activated",
            "unmuted_tracks": unmuted_tracks,
            "message": f"Unmuted {len(unmuted_tracks)} tracks"
        }
    
    def activate_backup_scene(self, scene_index: int) -> Dict[str, Any]:
        """Activate backup scene."""
        self.backup_scene_index = scene_index
        return {
            "status": "backup_scene_activated",
            "scene_index": scene_index,
            "message": f"Backup scene {scene_index} activated"
        }
    
    def get_emergency_status(self) -> Dict[str, Any]:
        """Get emergency status."""
        return {
            "emergency_active": self.emergency_active,
            "backup_scene_index": self.backup_scene_index,
            "muted_tracks_count": len(self.original_mute_states)
        }


# Global instance
_emergency_control = EmergencyControl()


@tool(
    name="emergency_stop",
    description="Emergency stop - stop all clips and playback instantly",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def emergency_stop() -> Dict[str, Any]:
    """Emergency stop - stop all clips and playback instantly."""
    return _emergency_control.activate_emergency_stop()


@tool(
    name="panic_mute",
    description="Mute all tracks instantly for emergency situations",
    input_schema={
        "type": "object",
        "properties": {
            "tracks": {
                "type": "array",
                "description": "List of track objects with index and mute state"
            }
        },
        "required": ["tracks"]
    }
)
async def panic_mute(tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Mute all tracks instantly for emergency situations."""
    return _emergency_control.panic_mute(tracks)


@tool(
    name="panic_unmute",
    description="Unmute all tracks after panic mute",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def panic_unmute() -> Dict[str, Any]:
    """Unmute all tracks after panic mute."""
    return _emergency_control.panic_unmute()


@tool(
    name="activate_backup_scene",
    description="Activate a backup scene in case of emergency",
    input_schema={
        "type": "object",
        "properties": {
            "scene_index": {
                "type": "integer",
                "description": "Index of the backup scene to activate"
            }
        },
        "required": ["scene_index"]
    }
)
async def activate_backup_scene(scene_index: int) -> Dict[str, Any]:
    """Activate a backup scene in case of emergency."""
    return _emergency_control.activate_backup_scene(scene_index)


@tool(
    name="get_emergency_status",
    description="Get current emergency control status",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def get_emergency_status() -> Dict[str, Any]:
    """Get current emergency control status."""
    return _emergency_control.get_emergency_status()
