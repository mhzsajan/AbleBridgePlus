"""
Video/Lighting Tools for AbleBridge++ MCP Server.

Provides video preset management and lighting control integration.
"""

import json
import os
from typing import Any, Dict, List, Optional
from . import tool


class VideoLightingControl:
    """Video/Lighting control manager."""
    
    def __init__(self, presets_dir: str = None):
        """Initialize video/lighting control."""
        if presets_dir is None:
            presets_dir = os.path.join(os.path.expanduser("~"), ".ablebridge_video_lighting")
        self.presets_dir = presets_dir
        os.makedirs(presets_dir, exist_ok=True)
        
        # Create subdirectories
        for subdir in ["video", "transitions", "lighting"]:
            os.makedirs(os.path.join(presets_dir, subdir), exist_ok=True)
        
        # DMX state
        self.dmx_channels = {}
    
    def save_video_preset(self, name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Save a video effect preset."""
        preset_path = os.path.join(self.presets_dir, "video", f"{name}.json")
        
        preset_data = {
            "name": name,
            "type": "video",
            "parameters": parameters,
            "created": __import__('datetime').datetime.now().isoformat()
        }
        
        with open(preset_path, 'w') as f:
            json.dump(preset_data, f, indent=2)
        
        return {
            "status": "video_preset_saved",
            "name": name,
            "path": preset_path
        }
    
    def load_video_preset(self, name: str) -> Dict[str, Any]:
        """Load a video effect preset."""
        preset_path = os.path.join(self.presets_dir, "video", f"{name}.json")
        
        if not os.path.exists(preset_path):
            return {
                "status": "error",
                "message": f"Video preset '{name}' not found"
            }
        
        with open(preset_path, 'r') as f:
            preset_data = json.load(f)
        
        return {
            "status": "video_preset_loaded",
            "preset": preset_data
        }
    
    def save_transition_preset(self, name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Save a video transition preset."""
        preset_path = os.path.join(self.presets_dir, "transitions", f"{name}.json")
        
        preset_data = {
            "name": name,
            "type": "transition",
            "parameters": parameters,
            "created": __import__('datetime').datetime.now().isoformat()
        }
        
        with open(preset_path, 'w') as f:
            json.dump(preset_data, f, indent=2)
        
        return {
            "status": "transition_preset_saved",
            "name": name,
            "path": preset_path
        }
    
    def load_transition_preset(self, name: str) -> Dict[str, Any]:
        """Load a video transition preset."""
        preset_path = os.path.join(self.presets_dir, "transitions", f"{name}.json")
        
        if not os.path.exists(preset_path):
            return {
                "status": "error",
                "message": f"Transition preset '{name}' not found"
            }
        
        with open(preset_path, 'r') as f:
            preset_data = json.load(f)
        
        return {
            "status": "transition_preset_loaded",
            "preset": preset_data
        }
    
    def list_video_presets(self) -> List[Dict[str, Any]]:
        """List all video presets."""
        video_dir = os.path.join(self.presets_dir, "video")
        
        if not os.path.exists(video_dir):
            return []
        
        presets = []
        for filename in os.listdir(video_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(video_dir, filename)
                with open(filepath, 'r') as f:
                    preset_data = json.load(f)
                presets.append(preset_data)
        
        return presets
    
    def set_dmx_channel(self, channel: int, value: int) -> Dict[str, Any]:
        """Set a DMX channel value."""
        if not (1 <= channel <= 512):
            return {"status": "error", "message": "DMX channel must be 1-512"}
        if not (0 <= value <= 255):
            return {"status": "error", "message": "DMX value must be 0-255"}
        
        self.dmx_channels[channel] = value
        return {
            "status": "dmx_channel_set",
            "channel": channel,
            "value": value
        }
    
    def get_dmx_status(self) -> Dict[str, Any]:
        """Get DMX channel status."""
        return {
            "channels": self.dmx_channels,
            "active_channels": len(self.dmx_channels)
        }
    
    def save_lighting_scene(self, name: str, channels: Dict[int, int]) -> Dict[str, Any]:
        """Save a lighting scene."""
        preset_path = os.path.join(self.presets_dir, "lighting", f"{name}.json")
        
        preset_data = {
            "name": name,
            "type": "lighting",
            "channels": channels,
            "created": __import__('datetime').datetime.now().isoformat()
        }
        
        with open(preset_path, 'w') as f:
            json.dump(preset_data, f, indent=2)
        
        return {
            "status": "lighting_scene_saved",
            "name": name,
            "path": preset_path
        }
    
    def load_lighting_scene(self, name: str) -> Dict[str, Any]:
        """Load a lighting scene."""
        preset_path = os.path.join(self.presets_dir, "lighting", f"{name}.json")
        
        if not os.path.exists(preset_path):
            return {
                "status": "error",
                "message": f"Lighting scene '{name}' not found"
            }
        
        with open(preset_path, 'r') as f:
            preset_data = json.load(f)
        
        # Apply the lighting scene
        for channel, value in preset_data.get("channels", {}).items():
            self.dmx_channels[int(channel)] = value
        
        return {
            "status": "lighting_scene_loaded",
            "preset": preset_data
        }
    
    def list_lighting_presets(self) -> List[Dict[str, Any]]:
        """List all lighting presets."""
        lighting_dir = os.path.join(self.presets_dir, "lighting")
        
        if not os.path.exists(lighting_dir):
            return []
        
        presets = []
        for filename in os.listdir(lighting_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(lighting_dir, filename)
                with open(filepath, 'r') as f:
                    preset_data = json.load(f)
                presets.append(preset_data)
        
        return presets


# Global instance
_video_lighting = VideoLightingControl()


@tool(
    name="save_video_preset",
    description="Save a video effect preset",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Preset name"
            },
            "parameters": {
                "type": "object",
                "description": "Video effect parameters"
            }
        },
        "required": ["name", "parameters"]
    }
)
async def save_video_preset(name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Save a video effect preset."""
    return _video_lighting.save_video_preset(name, parameters)


@tool(
    name="load_video_preset",
    description="Load a video effect preset",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Preset name"
            }
        },
        "required": ["name"]
    }
)
async def load_video_preset(name: str) -> Dict[str, Any]:
    """Load a video effect preset."""
    return _video_lighting.load_video_preset(name)


@tool(
    name="save_transition_preset",
    description="Save a video transition preset",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Preset name"
            },
            "parameters": {
                "type": "object",
                "description": "Transition parameters"
            }
        },
        "required": ["name", "parameters"]
    }
)
async def save_transition_preset(name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Save a video transition preset."""
    return _video_lighting.save_transition_preset(name, parameters)


@tool(
    name="load_transition_preset",
    description="Load a video transition preset",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Preset name"
            }
        },
        "required": ["name"]
    }
)
async def load_transition_preset(name: str) -> Dict[str, Any]:
    """Load a video transition preset."""
    return _video_lighting.load_transition_preset(name)


@tool(
    name="get_video_presets_list",
    description="List all video presets",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def get_video_presets_list() -> Dict[str, Any]:
    """List all video presets."""
    presets = _video_lighting.list_video_presets()
    return {
        "presets": presets,
        "count": len(presets)
    }


@tool(
    name="set_dmx_channel",
    description="Set a DMX lighting channel value",
    input_schema={
        "type": "object",
        "properties": {
            "channel": {
                "type": "integer",
                "description": "DMX channel (1-512)"
            },
            "value": {
                "type": "integer",
                "description": "Channel value (0-255)"
            }
        },
        "required": ["channel", "value"]
    }
)
async def set_dmx_channel(channel: int, value: int) -> Dict[str, Any]:
    """Set a DMX lighting channel value."""
    return _video_lighting.set_dmx_channel(channel, value)


@tool(
    name="get_dmx_status",
    description="Get DMX channel status",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def get_dmx_status() -> Dict[str, Any]:
    """Get DMX channel status."""
    return _video_lighting.get_dmx_status()


@tool(
    name="save_lighting_scene",
    description="Save a lighting scene",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Scene name"
            },
            "channels": {
                "type": "object",
                "description": "DMX channel values (channel: value)"
            }
        },
        "required": ["name", "channels"]
    }
)
async def save_lighting_scene(name: str, channels: Dict[int, int]) -> Dict[str, Any]:
    """Save a lighting scene."""
    return _video_lighting.save_lighting_scene(name, channels)


@tool(
    name="load_lighting_scene",
    description="Load and apply a lighting scene",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Scene name"
            }
        },
        "required": ["name"]
    }
)
async def load_lighting_scene(name: str) -> Dict[str, Any]:
    """Load and apply a lighting scene."""
    return _video_lighting.load_lighting_scene(name)


@tool(
    name="get_lighting_presets",
    description="List all lighting presets",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def get_lighting_presets() -> Dict[str, Any]:
    """List all lighting presets."""
    presets = _video_lighting.list_lighting_presets()
    return {
        "presets": presets,
        "count": len(presets)
    }
