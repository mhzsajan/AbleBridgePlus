"""
Template System Tools for AbleBridgePlus MCP Server.

These tools provide template management for sessions, tracks, and devices.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional
from MCP_Server.tools import tool


# Templates directory
TEMPLATES_DIR = os.path.join(os.path.expanduser("~"), ".ablebridge", "templates")


def _ensure_templates_dir():
    """Ensure templates directory exists."""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)


def _load_template(template_name: str, template_type: str) -> Optional[Dict[str, Any]]:
    """Load a template from file."""
    template_file = os.path.join(TEMPLATES_DIR, template_type, f"{template_name}.json")
    if os.path.exists(template_file):
        try:
            with open(template_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    return None


def _save_template(template_name: str, template_data: Dict[str, Any], template_type: str):
    """Save a template to file."""
    template_dir = os.path.join(TEMPLATES_DIR, template_type)
    os.makedirs(template_dir, exist_ok=True)
    
    template_file = os.path.join(template_dir, f"{template_name}.json")
    with open(template_file, 'w') as f:
        json.dump(template_data, f, indent=2)


def _list_templates(template_type: str) -> List[str]:
    """List all templates of a type."""
    template_dir = os.path.join(TEMPLATES_DIR, template_type)
    if not os.path.exists(template_dir):
        return []
    
    return [
        f.replace('.json', '')
        for f in os.listdir(template_dir)
        if f.endswith('.json')
    ]


@tool(
    name="save_session_template",
    description="Save session as template",
    inputSchema={
        'type': 'object',
        'properties': {
            'template_name': {
                'type': 'string',
                'description': 'Name for the template'
            },
            'description': {
                'type': 'string',
                'description': 'Template description'
            }
        },
        'required': ['template_name']
    }
)
async def save_session_template(
    template_name: str,
    description: str = ""
) -> Dict[str, Any]:
    """
    Save session as a template.
    
    Args:
        template_name: Name for the template
        description: Template description
        
    Returns:
        Dictionary with result
    """
    template_data = {
        'name': template_name,
        'description': description,
        'created_at': time.time(),
        'type': 'session',
        'tracks': [],  # Would capture track structure
        'scenes': [],  # Would capture scene structure
        'message': 'Session template saved with placeholder data'
    }
    
    _save_template(template_name, template_data, "session")
    
    return {
        'success': True,
        'template_name': template_name,
        'message': f'Session template saved: {template_name}'
    }


@tool(
    name="load_session_template",
    description="Load session from template",
    inputSchema={
        'type': 'object',
        'properties': {
            'template_name': {
                'type': 'string',
                'description': 'Name of the template to load'
            }
        },
        'required': ['template_name']
    }
)
async def load_session_template(template_name: str) -> Dict[str, Any]:
    """
    Load session from a template.
    
    Args:
        template_name: Name of the template to load
        
    Returns:
        Dictionary with result
    """
    template = _load_template(template_name, "session")
    
    if template is None:
        return {'error': f'Template not found: {template_name}'}
    
    return {
        'success': True,
        'template_name': template_name,
        'template': template,
        'message': f'Session template loaded: {template_name}'
    }


@tool(
    name="save_track_template",
    description="Save track as template",
    inputSchema={
        'type': 'object',
        'properties': {
            'template_name': {
                'type': 'string',
                'description': 'Name for the template'
            },
            'track_index': {
                'type': 'integer',
                'description': 'Track index to save'
            },
            'description': {
                'type': 'string',
                'description': 'Template description'
            }
        },
        'required': ['template_name', 'track_index']
    }
)
async def save_track_template(
    template_name: str,
    track_index: int,
    description: str = ""
) -> Dict[str, Any]:
    """
    Save track as a template.
    
    Args:
        template_name: Name for the template
        track_index: Track index to save
        description: Template description
        
    Returns:
        Dictionary with result
    """
    template_data = {
        'name': template_name,
        'description': description,
        'created_at': time.time(),
        'type': 'track',
        'track_index': track_index,
        'devices': [],  # Would capture device chain
        'routing': {},  # Would capture routing
        'message': 'Track template saved with placeholder data'
    }
    
    _save_template(template_name, template_data, "track")
    
    return {
        'success': True,
        'template_name': template_name,
        'track_index': track_index,
        'message': f'Track template saved: {template_name}'
    }


@tool(
    name="load_track_template",
    description="Load track from template",
    inputSchema={
        'type': 'object',
        'properties': {
            'template_name': {
                'type': 'string',
                'description': 'Name of the template to load'
            },
            'track_index': {
                'type': 'integer',
                'description': 'Track index to load into (optional)'
            }
        },
        'required': ['template_name']
    }
)
async def load_track_template(
    template_name: str,
    track_index: Optional[int] = None
) -> Dict[str, Any]:
    """
    Load track from a template.
    
    Args:
        template_name: Name of the template to load
        track_index: Track index to load into
        
    Returns:
        Dictionary with result
    """
    template = _load_template(template_name, "track")
    
    if template is None:
        return {'error': f'Template not found: {template_name}'}
    
    return {
        'success': True,
        'template_name': template_name,
        'template': template,
        'target_track_index': track_index,
        'message': f'Track template loaded: {template_name}'
    }


@tool(
    name="save_device_template",
    description="Save device chain as template",
    inputSchema={
        'type': 'object',
        'properties': {
            'template_name': {
                'type': 'string',
                'description': 'Name for the template'
            },
            'track_index': {
                'type': 'integer',
                'description': 'Track index'
            },
            'description': {
                'type': 'string',
                'description': 'Template description'
            }
        },
        'required': ['template_name', 'track_index']
    }
)
async def save_device_template(
    template_name: str,
    track_index: int,
    description: str = ""
) -> Dict[str, Any]:
    """
    Save device chain as a template.
    
    Args:
        template_name: Name for the template
        track_index: Track index
        description: Template description
        
    Returns:
        Dictionary with result
    """
    template_data = {
        'name': template_name,
        'description': description,
        'created_at': time.time(),
        'type': 'device',
        'track_index': track_index,
        'devices': [],  # Would capture device chain
        'message': 'Device template saved with placeholder data'
    }
    
    _save_template(template_name, template_data, "device")
    
    return {
        'success': True,
        'template_name': template_name,
        'track_index': track_index,
        'message': f'Device template saved: {template_name}'
    }


@tool(
    name="list_templates",
    description="List available templates",
    inputSchema={
        'type': 'object',
        'properties': {
            'template_type': {
                'type': 'string',
                'description': 'Template type (session, track, device, mix)',
                'enum': ['session', 'track', 'device', 'mix']
            }
        }
    }
)
async def list_templates(template_type: str = "session") -> Dict[str, Any]:
    """
    List available templates.
    
    Args:
        template_type: Template type
        
    Returns:
        Dictionary with template list
    """
    templates = _list_templates(template_type)
    
    return {
        'template_type': template_type,
        'templates': templates,
        'count': len(templates)
    }


@tool(
    name="delete_template",
    description="Delete a template",
    inputSchema={
        'type': 'object',
        'properties': {
            'template_name': {
                'type': 'string',
                'description': 'Name of the template to delete'
            },
            'template_type': {
                'type': 'string',
                'description': 'Template type'
            }
        },
        'required': ['template_name', 'template_type']
    }
)
async def delete_template(
    template_name: str,
    template_type: str
) -> Dict[str, Any]:
    """
    Delete a template.
    
    Args:
        template_name: Name of the template to delete
        template_type: Template type
        
    Returns:
        Dictionary with result
    """
    template_file = os.path.join(TEMPLATES_DIR, template_type, f"{template_name}.json")
    
    if not os.path.exists(template_file):
        return {'error': f'Template not found: {template_name}'}
    
    try:
        os.remove(template_file)
        return {
            'success': True,
            'message': f'Template deleted: {template_name}'
        }
    except Exception as e:
        return {'error': str(e)}
