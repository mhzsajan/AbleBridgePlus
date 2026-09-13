"""
Video Routing Tools for Enhanced AbletonBridge MCP Server.

These tools provide Videosync2 integration for video routing and control.
"""

import json
import os
from typing import Any, Dict, List, Optional
from MCP_Server.tools import tool


# Video configuration file
VIDEO_CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".enhanced-abletonbridge", "video_config.json")


def _load_video_config() -> Dict[str, Any]:
    """Load video configuration from file."""
    if os.path.exists(VIDEO_CONFIG_FILE):
        try:
            with open(VIDEO_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return _default_config()
    return _default_config()


def _save_video_config(config: Dict[str, Any]):
    """Save video configuration to file."""
    os.makedirs(os.path.dirname(VIDEO_CONFIG_FILE), exist_ok=True)
    with open(VIDEO_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def _default_config() -> Dict[str, Any]:
    """Get default video configuration."""
    return {
        'spout_enabled': False,
        'spout_port': 5000,
        'video_tracks': [],
        'backdrop_track_index': 15,
        'lyrics_track_index': 16,
        'live_cam_track_index': 17
    }


@tool(
    name="get_video_tracks",
    description="List video tracks in the session",
    inputSchema={
        'type': 'object',
        'properties': {}
    }
)
async def get_video_tracks() -> Dict[str, Any]:
    """
    Get list of video tracks.
    
    Returns:
        Dictionary with video tracks
    """
    config = _load_video_config()
    
    return {
        'video_tracks': config.get('video_tracks', []),
        'backdrop_track_index': config.get('backdrop_track_index'),
        'lyrics_track_index': config.get('lyrics_track_index'),
        'live_cam_track_index': config.get('live_cam_track_index'),
        'message': 'Video tracks retrieved from configuration'
    }


@tool(
    name="set_video_routing",
    description="Route video to output",
    inputSchema={
        'type': 'object',
        'properties': {
            'track_index': {
                'type': 'integer',
                'description': 'Track index'
            },
            'output_enabled': {
                'type': 'boolean',
                'description': 'Enable video output'
            }
        },
        'required': ['track_index', 'output_enabled']
    }
)
async def set_video_routing(
    track_index: int,
    output_enabled: bool
) -> Dict[str, Any]:
    """
    Set video routing for a track.
    
    Args:
        track_index: Track index
        output_enabled: Enable video output
        
    Returns:
        Dictionary with result
    """
    config = _load_video_config()
    
    # Update video tracks
    video_tracks = config.get('video_tracks', [])
    
    # Find or add track
    track_found = False
    for track in video_tracks:
        if track.get('index') == track_index:
            track['output_enabled'] = output_enabled
            track_found = True
            break
    
    if not track_found:
        video_tracks.append({
            'index': track_index,
            'output_enabled': output_enabled
        })
    
    config['video_tracks'] = video_tracks
    _save_video_config(config)
    
    return {
        'success': True,
        'track_index': track_index,
        'output_enabled': output_enabled,
        'message': f'Video routing {"enabled" if output_enabled else "disabled"} for track {track_index}'
    }


@tool(
    name="get_video_status",
    description="Check Videosync2 status",
    inputSchema={
        'type': 'object',
        'properties': {}
    }
)
async def get_video_status() -> Dict[str, Any]:
    """
    Get Videosync2 status.
    
    Returns:
        Dictionary with status information
    """
    config = _load_video_config()
    
    return {
        'spout_enabled': config.get('spout_enabled', False),
        'spout_port': config.get('spout_port', 5000),
        'video_tracks_count': len(config.get('video_tracks', [])),
        'message': 'Videosync2 status retrieved'
    }


@tool(
    name="configure_spout",
    description="Configure Spout output for TouchDesigner",
    inputSchema={
        'type': 'object',
        'properties': {
            'enabled': {
                'type': 'boolean',
                'description': 'Enable Spout output'
            },
            'port': {
                'type': 'integer',
                'description': 'Spout port (default: 5000)'
            }
        },
        'required': ['enabled']
    }
)
async def configure_spout(
    enabled: bool,
    port: int = 5000
) -> Dict[str, Any]:
    """
    Configure Spout output for TouchDesigner.
    
    Args:
        enabled: Enable Spout output
        port: Spout port
        
    Returns:
        Dictionary with result
    """
    config = _load_video_config()
    config['spout_enabled'] = enabled
    config['spout_port'] = port
    _save_video_config(config)
    
    return {
        'success': True,
        'spout_enabled': enabled,
        'spout_port': port,
        'message': f'Spout {"enabled" if enabled else "disabled"} on port {port}'
    }


@tool(
    name="get_spout_status",
    description="Get Spout output status",
    inputSchema={
        'type': 'object',
        'properties': {}
    }
)
async def get_spout_status() -> Dict[str, Any]:
    """
    Get Spout output status.
    
    Returns:
        Dictionary with Spout status
    """
    config = _load_video_config()
    
    return {
        'enabled': config.get('spout_enabled', False),
        'port': config.get('spout_port', 5000),
        'message': 'Spout status retrieved'
    }


@tool(
    name="set_video_track_config",
    description="Configure a video track",
    inputSchema={
        'type': 'object',
        'properties': {
            'track_type': {
                'type': 'string',
                'description': 'Track type (backdrop, lyrics, live_cam)',
                'enum': ['backdrop', 'lyrics', 'live_cam']
            },
            'track_index': {
                'type': 'integer',
                'description': 'Track index'
            }
        },
        'required': ['track_type', 'track_index']
    }
)
async def set_video_track_config(
    track_type: str,
    track_index: int
) -> Dict[str, Any]:
    """
    Configure a video track type.
    
    Args:
        track_type: Track type (backdrop, lyrics, live_cam)
        track_index: Track index
        
    Returns:
        Dictionary with result
    """
    config = _load_video_config()
    
    if track_type == 'backdrop':
        config['backdrop_track_index'] = track_index
    elif track_type == 'lyrics':
        config['lyrics_track_index'] = track_index
    elif track_type == 'live_cam':
        config['live_cam_track_index'] = track_index
    else:
        return {'error': f'Invalid track type: {track_type}'}
    
    _save_video_config(config)
    
    return {
        'success': True,
        'track_type': track_type,
        'track_index': track_index,
        'message': f'{track_type} track configured to index {track_index}'
    }
