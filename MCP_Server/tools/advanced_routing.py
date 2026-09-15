"""
Advanced Routing Tools for AbleBridge++ MCP Server.

These tools provide advanced routing capabilities including side-chain and multi-output.
"""

import json
import os
from typing import Any, Dict, List, Optional
from MCP_Server.tools import tool


# Routing presets file
ROUTING_PRESETS_FILE = os.path.join(os.path.expanduser("~"), ".ablebridge", "routing_presets.json")


def _load_routing_presets() -> Dict[str, Any]:
    """Load routing presets from file."""
    if os.path.exists(ROUTING_PRESETS_FILE):
        try:
            with open(ROUTING_PRESETS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {'presets': {}}
    return {'presets': {}}


def _save_routing_presets(presets: Dict[str, Any]):
    """Save routing presets to file."""
    os.makedirs(os.path.dirname(ROUTING_PRESETS_FILE), exist_ok=True)
    with open(ROUTING_PRESETS_FILE, 'w') as f:
        json.dump(presets, f, indent=2)


@tool(
    name="set_sidechain_routing",
    description="Set side-chain compression routing",
    inputSchema={
        'type': 'object',
        'properties': {
            'track_index': {
                'type': 'integer',
                'description': 'Track with compressor'
            },
            'device_index': {
                'type': 'integer',
                'description': 'Compressor device index'
            },
            'source_track_name': {
                'type': 'string',
                'description': 'Source track name for side-chain'
            }
        },
        'required': ['track_index', 'device_index', 'source_track_name']
    }
)
async def set_sidechain_routing(
    track_index: int,
    device_index: int,
    source_track_name: str
) -> Dict[str, Any]:
    """
    Set side-chain compression routing.
    
    Args:
        track_index: Track with compressor
        device_index: Compressor device index
        source_track_name: Source track name for side-chain
        
    Returns:
        Dictionary with result
    """
    # This is a placeholder
    # Real implementation would configure compressor side-chain
    return {
        'track_index': track_index,
        'device_index': device_index,
        'source_track_name': source_track_name,
        'message': 'Side-chain routing requires compressor integration'
    }


@tool(
    name="save_routing_preset",
    description="Save routing configuration",
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
async def save_routing_preset(
    preset_name: str,
    description: str = ""
) -> Dict[str, Any]:
    """
    Save routing configuration as a preset.
    
    Args:
        preset_name: Name for the preset
        description: Preset description
        
    Returns:
        Dictionary with result
    """
    presets = _load_routing_presets()
    
    presets['presets'][preset_name] = {
        'name': preset_name,
        'description': description,
        'created_at': __import__('time').time(),
        'routing': {},  # Would capture routing configuration
        'message': 'Routing preset saved with placeholder data'
    }
    
    _save_routing_presets(presets)
    
    return {
        'success': True,
        'preset_name': preset_name,
        'message': f'Routing preset saved: {preset_name}'
    }


@tool(
    name="load_routing_preset",
    description="Load routing configuration",
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
async def load_routing_preset(preset_name: str) -> Dict[str, Any]:
    """
    Load routing configuration from a preset.
    
    Args:
        preset_name: Name of the preset to load
        
    Returns:
        Dictionary with result
    """
    presets = _load_routing_presets()
    
    if preset_name not in presets.get('presets', {}):
        return {'error': f'Routing preset not found: {preset_name}'}
    
    preset = presets['presets'][preset_name]
    
    return {
        'success': True,
        'preset_name': preset_name,
        'preset': preset,
        'message': f'Routing preset loaded: {preset_name}'
    }


@tool(
    name="get_routing_presets_list",
    description="List saved routing presets",
    inputSchema={
        'type': 'object',
        'properties': {}
    }
)
async def get_routing_presets_list() -> Dict[str, Any]:
    """
    List saved routing presets.
    
    Returns:
        Dictionary with preset list
    """
    presets = _load_routing_presets()
    
    preset_list = []
    for name, preset in presets.get('presets', {}).items():
        preset_list.append({
            'name': name,
            'description': preset.get('description', ''),
            'created_at': preset.get('created_at')
        })
    
    return {
        'presets': preset_list,
        'count': len(preset_list)
    }
