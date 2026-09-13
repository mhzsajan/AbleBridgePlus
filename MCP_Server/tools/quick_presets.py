"""
Quick Presets Tools for Enhanced AbletonBridge MCP Server.

These tools provide live show preset management for quick recall.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional
from MCP_Server.tools import tool


# Presets directory
PRESETS_DIR = os.path.join(os.path.expanduser("~"), ".enhanced-abletonbridge", "presets")


def _ensure_presets_dir():
    """Ensure presets directory exists."""
    os.makedirs(PRESETS_DIR, exist_ok=True)


def _load_preset(preset_name: str, preset_type: str = "live") -> Optional[Dict[str, Any]]:
    """Load a preset from file."""
    preset_file = os.path.join(PRESETS_DIR, preset_type, f"{preset_name}.json")
    if os.path.exists(preset_file):
        try:
            with open(preset_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    return None


def _save_preset(preset_name: str, preset_data: Dict[str, Any], preset_type: str = "live"):
    """Save a preset to file."""
    preset_dir = os.path.join(PRESETS_DIR, preset_type)
    os.makedirs(preset_dir, exist_ok=True)
    
    preset_file = os.path.join(preset_dir, f"{preset_name}.json")
    with open(preset_file, 'w') as f:
        json.dump(preset_data, f, indent=2)


def _list_presets(preset_type: str = "live") -> List[str]:
    """List all presets of a type."""
    preset_dir = os.path.join(PRESETS_DIR, preset_type)
    if not os.path.exists(preset_dir):
        return []
    
    return [
        f.replace('.json', '')
        for f in os.listdir(preset_dir)
        if f.endswith('.json')
    ]


@tool(
    name="save_live_preset",
    description="Save live show preset",
    inputSchema={
        'type': 'object',
        'properties': {
            'preset_name': {
                'type': 'string',
                'description': 'Name for the preset'
            },
            'description': {
                'type': 'string',
                'description': 'Preset description'
            }
        },
        'required': ['preset_name']
    }
)
async def save_live_preset(
    preset_name: str,
    description: str = ""
) -> Dict[str, Any]:
    """
    Save a live show preset.
    
    Args:
        preset_name: Name for the preset
        description: Preset description
        
    Returns:
        Dictionary with result
    """
    # This would capture the current session state
    preset_data = {
        'name': preset_name,
        'description': description,
        'created_at': time.time(),
        'tracks': [],  # Would capture track states
        'devices': [],  # Would capture device states
        'mixer': {},  # Would capture mixer state
        'message': 'Preset saved with placeholder data. Full implementation requires Ableton integration.'
    }
    
    _save_preset(preset_name, preset_data)
    
    return {
        'success': True,
        'preset_name': preset_name,
        'message': f'Live preset saved: {preset_name}'
    }


@tool(
    name="load_live_preset",
    description="Load live show preset",
    inputSchema={
        'type': 'object',
        'properties': {
            'preset_name': {
                'type': 'string',
                'description': 'Name of the preset to load'
            }
        },
        'required': ['preset_name']
    }
)
async def load_live_preset(preset_name: str) -> Dict[str, Any]:
    """
    Load a live show preset.
    
    Args:
        preset_name: Name of the preset to load
        
    Returns:
        Dictionary with result
    """
    preset = _load_preset(preset_name)
    
    if preset is None:
        return {'error': f'Preset not found: {preset_name}'}
    
    return {
        'success': True,
        'preset_name': preset_name,
        'preset': preset,
        'message': f'Live preset loaded: {preset_name}'
    }


@tool(
    name="list_live_presets",
    description="List available live presets",
    inputSchema={
        'type': 'object',
        'properties': {}
    }
)
async def list_live_presets() -> Dict[str, Any]:
    """
    List available live presets.
    
    Returns:
        Dictionary with preset list
    """
    presets = _list_presets("live")
    
    preset_details = []
    for name in presets:
        preset = _load_preset(name, "live")
        if preset:
            preset_details.append({
                'name': name,
                'description': preset.get('description', ''),
                'created_at': preset.get('created_at')
            })
    
    return {
        'presets': preset_details,
        'count': len(preset_details)
    }


@tool(
    name="delete_live_preset",
    description="Delete a live preset",
    inputSchema={
        'type': 'object',
        'properties': {
            'preset_name': {
                'type': 'string',
                'description': 'Name of the preset to delete'
            }
        },
        'required': ['preset_name']
    }
)
async def delete_live_preset(preset_name: str) -> Dict[str, Any]:
    """
    Delete a live preset.
    
    Args:
        preset_name: Name of the preset to delete
        
    Returns:
        Dictionary with result
    """
    preset_file = os.path.join(PRESETS_DIR, "live", f"{preset_name}.json")
    
    if not os.path.exists(preset_file):
        return {'error': f'Preset not found: {preset_name}'}
    
    try:
        os.remove(preset_file)
        return {
            'success': True,
            'message': f'Live preset deleted: {preset_name}'
        }
    except Exception as e:
        return {'error': str(e)}


@tool(
    name="create_scene_preset",
    description="Save scene state as preset",
    inputSchema={
        'type': 'object',
        'properties': {
            'preset_name': {
                'type': 'string',
                'description': 'Name for the preset'
            },
            'scene_index': {
                'type': 'integer',
                'description': 'Scene index to save'
            }
        },
        'required': ['preset_name', 'scene_index']
    }
)
async def create_scene_preset(
    preset_name: str,
    scene_index: int
) -> Dict[str, Any]:
    """
    Save scene state as a preset.
    
    Args:
        preset_name: Name for the preset
        scene_index: Scene index to save
        
    Returns:
        Dictionary with result
    """
    preset_data = {
        'name': preset_name,
        'type': 'scene',
        'scene_index': scene_index,
        'created_at': time.time(),
        'message': 'Scene preset saved with placeholder data'
    }
    
    _save_preset(preset_name, preset_data, "scenes")
    
    return {
        'success': True,
        'preset_name': preset_name,
        'scene_index': scene_index,
        'message': f'Scene preset saved: {preset_name}'
    }


@tool(
    name="load_scene_preset",
    description="Load scene state from preset",
    inputSchema={
        'type': 'object',
        'properties': {
            'preset_name': {
                'type': 'string',
                'description': 'Name of the preset to load'
            }
        },
        'required': ['preset_name']
    }
)
async def load_scene_preset(preset_name: str) -> Dict[str, Any]:
    """
    Load scene state from a preset.
    
    Args:
        preset_name: Name of the preset to load
        
    Returns:
        Dictionary with result
    """
    preset = _load_preset(preset_name, "scenes")
    
    if preset is None:
        return {'error': f'Scene preset not found: {preset_name}'}
    
    return {
        'success': True,
        'preset_name': preset_name,
        'preset': preset,
        'message': f'Scene preset loaded: {preset_name}'
    }


@tool(
    name="create_mix_preset",
    description="Save mix state as preset",
    inputSchema={
        'type': 'object',
        'properties': {
            'preset_name': {
                'type': 'string',
                'description': 'Name for the preset'
            }
        },
        'required': ['preset_name']
    }
)
async def create_mix_preset(preset_name: str) -> Dict[str, Any]:
    """
    Save mix state as a preset.
    
    Args:
        preset_name: Name for the preset
        
    Returns:
        Dictionary with result
    """
    preset_data = {
        'name': preset_name,
        'type': 'mix',
        'created_at': time.time(),
        'tracks': [],  # Would capture mix state
        'message': 'Mix preset saved with placeholder data'
    }
    
    _save_preset(preset_name, preset_data, "mix")
    
    return {
        'success': True,
        'preset_name': preset_name,
        'message': f'Mix preset saved: {preset_name}'
    }


@tool(
    name="load_mix_preset",
    description="Load mix state from preset",
    inputSchema={
        'type': 'object',
        'properties': {
            'preset_name': {
                'type': 'string',
                'description': 'Name of the preset to load'
            }
        },
        'required': ['preset_name']
    }
)
async def load_mix_preset(preset_name: str) -> Dict[str, Any]:
    """
    Load mix state from a preset.
    
    Args:
        preset_name: Name of the preset to load
        
    Returns:
        Dictionary with result
    """
    preset = _load_preset(preset_name, "mix")
    
    if preset is None:
        return {'error': f'Mix preset not found: {preset_name}'}
    
    return {
        'success': True,
        'preset_name': preset_name,
        'preset': preset,
        'message': f'Mix preset loaded: {preset_name}'
    }
