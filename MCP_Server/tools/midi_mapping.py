"""
MIDI Mapping Tools for Enhanced AbletonBridge MCP Server.

These tools provide MIDI controller integration for mapping physical controllers
to Ableton parameters.
"""

import json
import os
from typing import Any, Dict, List, Optional
from MCP_Server.tools import tool
from MCP_Server.validation import validate_track_index, validate_cc, validate_value


# MIDI mapping storage file
MIDI_MAPPINGS_FILE = os.path.join(os.path.expanduser("~"), ".enhanced-abletonbridge", "midi_mappings.json")


def _load_midi_mappings() -> Dict[str, Any]:
    """Load MIDI mappings from file."""
    if os.path.exists(MIDI_MAPPINGS_FILE):
        try:
            with open(MIDI_MAPPINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_midi_mappings(mappings: Dict[str, Any]):
    """Save MIDI mappings to file."""
    os.makedirs(os.path.dirname(MIDI_MAPPINGS_FILE), exist_ok=True)
    with open(MIDI_MAPPINGS_FILE, 'w') as f:
        json.dump(mappings, f, indent=2)


@tool(
    name="get_midi_mappings",
    description="List all MIDI controller mappings",
    inputSchema={
        'type': 'object',
        'properties': {
            'controller_name': {
                'type': 'string',
                'description': 'Filter by controller name (optional)'
            }
        }
    }
)
async def get_midi_mappings(controller_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get all MIDI controller mappings.
    
    Args:
        controller_name: Filter by controller name (optional)
        
    Returns:
        Dictionary with MIDI mappings
    """
    mappings = _load_midi_mappings()
    
    if controller_name:
        filtered = {}
        for key, mapping in mappings.items():
            if mapping.get('controller_name') == controller_name:
                filtered[key] = mapping
        mappings = filtered
    
    return {
        'mappings': mappings,
        'count': len(mappings)
    }


@tool(
    name="create_midi_mapping",
    description="Map a MIDI controller to an Ableton parameter",
    inputSchema={
        'type': 'object',
        'properties': {
            'controller_name': {
                'type': 'string',
                'description': 'Name of the MIDI controller'
            },
            'channel': {
                'type': 'integer',
                'description': 'MIDI channel (0-15)'
            },
            'cc': {
                'type': 'integer',
                'description': 'MIDI CC number (0-127)'
            },
            'track_index': {
                'type': 'integer',
                'description': 'Target track index'
            },
            'parameter_name': {
                'type': 'string',
                'description': 'Target parameter name'
            },
            'min_value': {
                'type': 'number',
                'description': 'Minimum parameter value (default: 0.0)'
            },
            'max_value': {
                'type': 'number',
                'description': 'Maximum parameter value (default: 1.0)'
            }
        },
        'required': ['controller_name', 'channel', 'cc', 'track_index', 'parameter_name']
    }
)
async def create_midi_mapping(
    controller_name: str,
    channel: int,
    cc: int,
    track_index: int,
    parameter_name: str,
    min_value: float = 0.0,
    max_value: float = 1.0
) -> Dict[str, Any]:
    """
    Create a MIDI mapping from a controller to an Ableton parameter.
    
    Args:
        controller_name: Name of the MIDI controller
        channel: MIDI channel (0-15)
        cc: MIDI CC number (0-127)
        track_index: Target track index
        parameter_name: Target parameter name
        min_value: Minimum parameter value
        max_value: Maximum parameter value
        
    Returns:
        Dictionary with result
    """
    # Validate inputs
    if channel < 0 or channel > 15:
        return {'error': 'Channel must be between 0 and 15'}
    
    validate_cc(cc)
    validate_track_index(track_index)
    
    if min_value >= max_value:
        return {'error': 'min_value must be less than max_value'}
    
    # Create mapping key
    mapping_key = f"{controller_name}:{channel}:{cc}"
    
    # Load existing mappings
    mappings = _load_midi_mappings()
    
    # Add new mapping
    mappings[mapping_key] = {
        'controller_name': controller_name,
        'channel': channel,
        'cc': cc,
        'track_index': track_index,
        'parameter_name': parameter_name,
        'min_value': min_value,
        'max_value': max_value,
        'created_at': __import__('datetime').datetime.now().isoformat()
    }
    
    # Save mappings
    _save_midi_mappings(mappings)
    
    return {
        'success': True,
        'message': f'MIDI mapping created: {mapping_key}',
        'mapping': mappings[mapping_key]
    }


@tool(
    name="delete_midi_mapping",
    description="Remove a MIDI mapping",
    inputSchema={
        'type': 'object',
        'properties': {
            'controller_name': {
                'type': 'string',
                'description': 'Name of the MIDI controller'
            },
            'channel': {
                'type': 'integer',
                'description': 'MIDI channel (0-15)'
            },
            'cc': {
                'type': 'integer',
                'description': 'MIDI CC number (0-127)'
            }
        },
        'required': ['controller_name', 'channel', 'cc']
    }
)
async def delete_midi_mapping(
    controller_name: str,
    channel: int,
    cc: int
) -> Dict[str, Any]:
    """
    Delete a MIDI mapping.
    
    Args:
        controller_name: Name of the MIDI controller
        channel: MIDI channel (0-15)
        cc: MIDI CC number (0-127)
        
    Returns:
        Dictionary with result
    """
    mapping_key = f"{controller_name}:{channel}:{cc}"
    
    mappings = _load_midi_mappings()
    
    if mapping_key not in mappings:
        return {'error': f'Mapping not found: {mapping_key}'}
    
    del mappings[mapping_key]
    _save_midi_mappings(mappings)
    
    return {
        'success': True,
        'message': f'MIDI mapping deleted: {mapping_key}'
    }


@tool(
    name="get_midi_controllers",
    description="List connected MIDI controllers",
    inputSchema={
        'type': 'object',
        'properties': {}
    }
)
async def get_midi_controllers() -> Dict[str, Any]:
    """
    Get list of connected MIDI controllers.
    
    Returns:
        Dictionary with MIDI controllers
    """
    # This is a placeholder
    # Real implementation would query the system for MIDI devices
    return {
        'controllers': [
            {
                'name': 'Minilab3',
                'type': 'MIDI Controller',
                'manufacturer': 'Arturia',
                'status': 'connected'
            }
        ],
        'message': 'MIDI controller detection requires platform-specific implementation'
    }


@tool(
    name="save_midi_mapping",
    description="Save MIDI mapping preset",
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
async def save_midi_mapping(preset_name: str) -> Dict[str, Any]:
    """
    Save current MIDI mappings as a preset.
    
    Args:
        preset_name: Name for the preset
        
    Returns:
        Dictionary with result
    """
    mappings = _load_midi_mappings()
    
    # Save as preset
    preset_dir = os.path.join(os.path.expanduser("~"), ".enhanced-abletonbridge", "presets", "midi")
    os.makedirs(preset_dir, exist_ok=True)
    
    preset_file = os.path.join(preset_dir, f"{preset_name}.json")
    with open(preset_file, 'w') as f:
        json.dump(mappings, f, indent=2)
    
    return {
        'success': True,
        'message': f'MIDI mapping preset saved: {preset_name}',
        'mapping_count': len(mappings)
    }


@tool(
    name="load_midi_mapping",
    description="Load MIDI mapping preset",
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
async def load_midi_mapping(preset_name: str) -> Dict[str, Any]:
    """
    Load MIDI mappings from a preset.
    
    Args:
        preset_name: Name of the preset to load
        
    Returns:
        Dictionary with result
    """
    preset_file = os.path.join(os.path.expanduser("~"), ".enhanced-abletonbridge", "presets", "midi", f"{preset_name}.json")
    
    if not os.path.exists(preset_file):
        return {'error': f'Preset not found: {preset_name}'}
    
    try:
        with open(preset_file, 'r') as f:
            mappings = json.load(f)
        
        _save_midi_mappings(mappings)
        
        return {
            'success': True,
            'message': f'MIDI mapping preset loaded: {preset_name}',
            'mapping_count': len(mappings)
        }
    except Exception as e:
        return {'error': str(e)}
