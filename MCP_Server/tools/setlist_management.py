"""
Setlist Management Tools for AbleBridgePlus MCP Server.

These tools provide AbleSet integration for setlist management during live shows.
"""

import json
import os
from typing import Any, Dict, List, Optional
from MCP_Server.tools import tool


# Setlist configuration file
SETLIST_CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".ablebridge", "setlist.json")


def _load_setlist() -> Dict[str, Any]:
    """Load setlist from file."""
    if os.path.exists(SETLIST_CONFIG_FILE):
        try:
            with open(SETLIST_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return _default_setlist()
    return _default_setlist()


def _save_setlist(setlist: Dict[str, Any]):
    """Save setlist to file."""
    os.makedirs(os.path.dirname(SETLIST_CONFIG_FILE), exist_ok=True)
    with open(SETLIST_CONFIG_FILE, 'w') as f:
        json.dump(setlist, f, indent=2)


def _default_setlist() -> Dict[str, Any]:
    """Get default setlist."""
    return {
        'name': 'Default Setlist',
        'songs': [],
        'current_song_index': -1,
        'next_song_index': -1,
        'mode': 'normal'
    }


@tool(
    name="get_setlist",
    description="Get current setlist",
    inputSchema={
        'type': 'object',
        'properties': {}
    }
)
async def get_setlist() -> Dict[str, Any]:
    """
    Get the current setlist.
    
    Returns:
        Dictionary with setlist information
    """
    setlist = _load_setlist()
    
    return {
        'name': setlist.get('name', 'Untitled'),
        'songs': setlist.get('songs', []),
        'song_count': len(setlist.get('songs', [])),
        'current_song_index': setlist.get('current_song_index', -1),
        'next_song_index': setlist.get('next_song_index', -1),
        'mode': setlist.get('mode', 'normal')
    }


@tool(
    name="load_setlist",
    description="Load a setlist file",
    inputSchema={
        'type': 'object',
        'properties': {
            'setlist_data': {
                'type': 'object',
                'description': 'Setlist data'
            }
        },
        'required': ['setlist_data']
    }
)
async def load_setlist(setlist_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load a setlist.
    
    Args:
        setlist_data: Setlist data
        
    Returns:
        Dictionary with result
    """
    _save_setlist(setlist_data)
    
    return {
        'success': True,
        'song_count': len(setlist_data.get('songs', [])),
        'message': 'Setlist loaded'
    }


@tool(
    name="set_next_song",
    description="Set next song to play",
    inputSchema={
        'type': 'object',
        'properties': {
            'song_index': {
                'type': 'integer',
                'description': 'Song index'
            },
            'song_name': {
                'type': 'string',
                'description': 'Song name (alternative to index)'
            }
        }
    }
)
async def set_next_song(
    song_index: Optional[int] = None,
    song_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Set the next song to play.
    
    Args:
        song_index: Song index
        song_name: Song name (alternative to index)
        
    Returns:
        Dictionary with result
    """
    setlist = _load_setlist()
    songs = setlist.get('songs', [])
    
    if song_name:
        # Find song by name
        for i, song in enumerate(songs):
            if song.get('name', '').lower() == song_name.lower():
                song_index = i
                break
    
    if song_index is None or song_index < 0 or song_index >= len(songs):
        return {'error': 'Invalid song index or name not found'}
    
    setlist['next_song_index'] = song_index
    _save_setlist(setlist)
    
    return {
        'success': True,
        'next_song_index': song_index,
        'next_song_name': songs[song_index].get('name', ''),
        'message': f'Next song set to: {songs[song_index].get("name", "")}'
    }


@tool(
    name="get_song_info",
    description="Get song details",
    inputSchema={
        'type': 'object',
        'properties': {
            'song_index': {
                'type': 'integer',
                'description': 'Song index'
            },
            'song_name': {
                'type': 'string',
                'description': 'Song name (alternative to index)'
            }
        }
    }
)
async def get_song_info(
    song_index: Optional[int] = None,
    song_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get song details.
    
    Args:
        song_index: Song index
        song_name: Song name
        
    Returns:
        Dictionary with song information
    """
    setlist = _load_setlist()
    songs = setlist.get('songs', [])
    
    if song_name:
        for i, song in enumerate(songs):
            if song.get('name', '').lower() == song_name.lower():
                song_index = i
                break
    
    if song_index is None or song_index < 0 or song_index >= len(songs):
        return {'error': 'Invalid song index or name not found'}
    
    return {
        'song': songs[song_index],
        'index': song_index
    }


@tool(
    name="get_current_song",
    description="Get currently playing song",
    inputSchema={
        'type': 'object',
        'properties': {}
    }
)
async def get_current_song() -> Dict[str, Any]:
    """
    Get the currently playing song.
    
    Returns:
        Dictionary with current song information
    """
    setlist = _load_setlist()
    current_index = setlist.get('current_song_index', -1)
    songs = setlist.get('songs', [])
    
    if current_index < 0 or current_index >= len(songs):
        return {
            'current_song': None,
            'message': 'No song currently playing'
        }
    
    return {
        'current_song': songs[current_index],
        'index': current_index
    }


@tool(
    name="set_setlist_mode",
    description="Switch setlist mode",
    inputSchema={
        'type': 'object',
        'properties': {
            'mode': {
                'type': 'string',
                'description': 'Setlist mode (normal, sound_check, rehearsal)',
                'enum': ['normal', 'sound_check', 'rehearsal']
            }
        },
        'required': ['mode']
    }
)
async def set_setlist_mode(mode: str) -> Dict[str, Any]:
    """
    Set the setlist mode.
    
    Args:
        mode: Setlist mode (normal, sound_check, rehearsal)
        
    Returns:
        Dictionary with result
    """
    setlist = _load_setlist()
    setlist['mode'] = mode
    _save_setlist(setlist)
    
    return {
        'success': True,
        'mode': mode,
        'message': f'Setlist mode set to: {mode}'
    }


@tool(
    name="add_song_to_setlist",
    description="Add a song to the setlist",
    inputSchema={
        'type': 'object',
        'properties': {
            'name': {
                'type': 'string',
                'description': 'Song name'
            },
            'tempo': {
                'type': 'number',
                'description': 'Song tempo in BPM'
            },
            'key': {
                'type': 'string',
                'description': 'Song key'
            },
            'scene_index': {
                'type': 'integer',
                'description': 'Associated scene index'
            },
            'sections': {
                'type': 'array',
                'description': 'Song sections',
                'items': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'start_time': {'type': 'number'},
                        'end_time': {'type': 'number'}
                    }
                }
            }
        },
        'required': ['name']
    }
)
async def add_song_to_setlist(
    name: str,
    tempo: Optional[float] = None,
    key: Optional[str] = None,
    scene_index: Optional[int] = None,
    sections: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Add a song to the setlist.
    
    Args:
        name: Song name
        tempo: Song tempo
        key: Song key
        scene_index: Associated scene index
        sections: Song sections
        
    Returns:
        Dictionary with result
    """
    setlist = _load_setlist()
    songs = setlist.get('songs', [])
    
    new_song = {
        'name': name,
        'tempo': tempo,
        'key': key,
        'scene_index': scene_index,
        'sections': sections or []
    }
    
    songs.append(new_song)
    setlist['songs'] = songs
    _save_setlist(setlist)
    
    return {
        'success': True,
        'song_name': name,
        'song_index': len(songs) - 1,
        'message': f'Song "{name}" added to setlist'
    }


@tool(
    name="remove_song_from_setlist",
    description="Remove a song from the setlist",
    inputSchema={
        'type': 'object',
        'properties': {
            'song_index': {
                'type': 'integer',
                'description': 'Song index'
            }
        },
        'required': ['song_index']
    }
)
async def remove_song_from_setlist(song_index: int) -> Dict[str, Any]:
    """
    Remove a song from the setlist.
    
    Args:
        song_index: Song index
        
    Returns:
        Dictionary with result
    """
    setlist = _load_setlist()
    songs = setlist.get('songs', [])
    
    if song_index < 0 or song_index >= len(songs):
        return {'error': 'Invalid song index'}
    
    removed_song = songs.pop(song_index)
    setlist['songs'] = songs
    
    # Adjust current/next song indices
    if setlist.get('current_song_index', -1) >= song_index:
        setlist['current_song_index'] = max(-1, setlist['current_song_index'] - 1)
    if setlist.get('next_song_index', -1) >= song_index:
        setlist['next_song_index'] = max(-1, setlist['next_song_index'] - 1)
    
    _save_setlist(setlist)
    
    return {
        'success': True,
        'song_name': removed_song.get('name', ''),
        'message': f'Song "{removed_song.get("name", "")}" removed from setlist'
    }
