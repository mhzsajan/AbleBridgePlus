"""
Audio/MIDI Preset Tools for AbleBridgePlus MCP Server.

Provides preset management for audio and MIDI effects.
"""

import json
import os
from typing import Any, Dict, List, Optional
from . import tool


class AudioPresets:
    """Audio/MIDI preset manager."""
    
    def __init__(self, presets_dir: str = None):
        """Initialize audio presets."""
        if presets_dir is None:
            presets_dir = os.path.join(os.path.expanduser("~"), ".ablebridge_presets")
        self.presets_dir = presets_dir
        os.makedirs(presets_dir, exist_ok=True)
        
        # Create subdirectories for different preset types
        for subdir in ["reverb", "delay", "compressor", "eq", "arpeggiator", "chord"]:
            os.makedirs(os.path.join(presets_dir, subdir), exist_ok=True)
    
    def save_preset(self, preset_type: str, name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Save a preset."""
        preset_path = os.path.join(self.presets_dir, preset_type, f"{name}.json")
        
        preset_data = {
            "name": name,
            "type": preset_type,
            "parameters": parameters,
            "created": __import__('datetime').datetime.now().isoformat()
        }
        
        with open(preset_path, 'w') as f:
            json.dump(preset_data, f, indent=2)
        
        return {
            "status": "preset_saved",
            "name": name,
            "type": preset_type,
            "path": preset_path
        }
    
    def load_preset(self, preset_type: str, name: str) -> Dict[str, Any]:
        """Load a preset."""
        preset_path = os.path.join(self.presets_dir, preset_type, f"{name}.json")
        
        if not os.path.exists(preset_path):
            return {
                "status": "error",
                "message": f"Preset '{name}' not found in {preset_type}"
            }
        
        with open(preset_path, 'r') as f:
            preset_data = json.load(f)
        
        return {
            "status": "preset_loaded",
            "preset": preset_data
        }
    
    def list_presets(self, preset_type: str) -> List[Dict[str, Any]]:
        """List presets of a specific type."""
        preset_dir = os.path.join(self.presets_dir, preset_type)
        
        if not os.path.exists(preset_dir):
            return []
        
        presets = []
        for filename in os.listdir(preset_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(preset_dir, filename)
                with open(filepath, 'r') as f:
                    preset_data = json.load(f)
                presets.append(preset_data)
        
        return presets
    
    def delete_preset(self, preset_type: str, name: str) -> Dict[str, Any]:
        """Delete a preset."""
        preset_path = os.path.join(self.presets_dir, preset_type, f"{name}.json")
        
        if not os.path.exists(preset_path):
            return {
                "status": "error",
                "message": f"Preset '{name}' not found in {preset_type}"
            }
        
        os.remove(preset_path)
        return {
            "status": "preset_deleted",
            "name": name,
            "type": preset_type
        }


# Global instance
_audio_presets = AudioPresets()


@tool(
    name="save_reverb_preset",
    description="Save a reverb effect preset",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Preset name"
            },
            "parameters": {
                "type": "object",
                "description": "Reverb parameters"
            }
        },
        "required": ["name", "parameters"]
    }
)
async def save_reverb_preset(name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Save a reverb effect preset."""
    return _audio_presets.save_preset("reverb", name, parameters)


@tool(
    name="load_reverb_preset",
    description="Load a reverb effect preset",
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
async def load_reverb_preset(name: str) -> Dict[str, Any]:
    """Load a reverb effect preset."""
    return _audio_presets.load_preset("reverb", name)


@tool(
    name="save_delay_preset",
    description="Save a delay effect preset",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Preset name"
            },
            "parameters": {
                "type": "object",
                "description": "Delay parameters"
            }
        },
        "required": ["name", "parameters"]
    }
)
async def save_delay_preset(name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Save a delay effect preset."""
    return _audio_presets.save_preset("delay", name, parameters)


@tool(
    name="load_delay_preset",
    description="Load a delay effect preset",
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
async def load_delay_preset(name: str) -> Dict[str, Any]:
    """Load a delay effect preset."""
    return _audio_presets.load_preset("delay", name)


@tool(
    name="save_compressor_preset",
    description="Save a compressor effect preset",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Preset name"
            },
            "parameters": {
                "type": "object",
                "description": "Compressor parameters"
            }
        },
        "required": ["name", "parameters"]
    }
)
async def save_compressor_preset(name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Save a compressor effect preset."""
    return _audio_presets.save_preset("compressor", name, parameters)


@tool(
    name="load_compressor_preset",
    description="Load a compressor effect preset",
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
async def load_compressor_preset(name: str) -> Dict[str, Any]:
    """Load a compressor effect preset."""
    return _audio_presets.load_preset("compressor", name)


@tool(
    name="save_eq_preset",
    description="Save an EQ effect preset",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Preset name"
            },
            "parameters": {
                "type": "object",
                "description": "EQ parameters"
            }
        },
        "required": ["name", "parameters"]
    }
)
async def save_eq_preset(name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Save an EQ effect preset."""
    return _audio_presets.save_preset("eq", name, parameters)


@tool(
    name="load_eq_preset",
    description="Load an EQ effect preset",
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
async def load_eq_preset(name: str) -> Dict[str, Any]:
    """Load an EQ effect preset."""
    return _audio_presets.load_preset("eq", name)


@tool(
    name="save_arpeggiator_preset",
    description="Save an arpeggiator effect preset",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Preset name"
            },
            "parameters": {
                "type": "object",
                "description": "Arpeggiator parameters"
            }
        },
        "required": ["name", "parameters"]
    }
)
async def save_arpeggiator_preset(name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Save an arpeggiator effect preset."""
    return _audio_presets.save_preset("arpeggiator", name, parameters)


@tool(
    name="load_arpeggiator_preset",
    description="Load an arpeggiator effect preset",
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
async def load_arpeggiator_preset(name: str) -> Dict[str, Any]:
    """Load an arpeggiator effect preset."""
    return _audio_presets.load_preset("arpeggiator", name)


@tool(
    name="save_chord_preset",
    description="Save a chord effect preset",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Preset name"
            },
            "parameters": {
                "type": "object",
                "description": "Chord parameters"
            }
        },
        "required": ["name", "parameters"]
    }
)
async def save_chord_preset(name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Save a chord effect preset."""
    return _audio_presets.save_preset("chord", name, parameters)


@tool(
    name="load_chord_preset",
    description="Load a chord effect preset",
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
async def load_chord_preset(name: str) -> Dict[str, Any]:
    """Load a chord effect preset."""
    return _audio_presets.load_preset("chord", name)


@tool(
    name="list_audio_presets",
    description="List all audio effect presets of a specific type",
    input_schema={
        "type": "object",
        "properties": {
            "preset_type": {
                "type": "string",
                "description": "Type of preset (reverb, delay, compressor, eq)",
                "enum": ["reverb", "delay", "compressor", "eq"]
            }
        },
        "required": ["preset_type"]
    }
)
async def list_audio_presets(preset_type: str) -> Dict[str, Any]:
    """List all audio effect presets of a specific type."""
    presets = _audio_presets.list_presets(preset_type)
    return {
        "presets": presets,
        "count": len(presets),
        "type": preset_type
    }


@tool(
    name="list_midi_presets",
    description="List all MIDI effect presets of a specific type",
    input_schema={
        "type": "object",
        "properties": {
            "preset_type": {
                "type": "string",
                "description": "Type of preset (arpeggiator, chord)",
                "enum": ["arpeggiator", "chord"]
            }
        },
        "required": ["preset_type"]
    }
)
async def list_midi_presets(preset_type: str) -> Dict[str, Any]:
    """List all MIDI effect presets of a specific type."""
    presets = _audio_presets.list_presets(preset_type)
    return {
        "presets": presets,
        "count": len(presets),
        "type": preset_type
    }
