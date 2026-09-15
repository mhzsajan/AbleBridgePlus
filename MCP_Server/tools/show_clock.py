"""
Show Clock and Timer Tools for AbleBridgePlus MCP Server.

These tools provide timing, countdown, and show clock features for live performances.
"""

import time
import json
import os
from typing import Any, Dict, List, Optional
from MCP_Server.tools import tool


# Show clock state
_show_clock = {
    'start_time': None,
    'song_start_times': [],
    'is_running': False,
    'current_song': None,
    'tempo': 120
}


@tool(
    name="start_show_clock",
    description="Start the show clock timer",
    inputSchema={
        'type': 'object',
        'properties': {
            'tempo': {
                'type': 'number',
                'description': 'Show tempo in BPM (optional)'
            }
        }
    }
)
async def start_show_clock(tempo: float = 120) -> Dict[str, Any]:
    """
    Start the show clock timer.
    
    Args:
        tempo: Show tempo in BPM
        
    Returns:
        Dictionary with result
    """
    global _show_clock
    
    _show_clock['start_time'] = time.time()
    _show_clock['is_running'] = True
    _show_clock['tempo'] = tempo
    _show_clock['song_start_times'] = []
    
    return {
        'success': True,
        'message': 'Show clock started',
        'start_time': _show_clock['start_time'],
        'tempo': tempo
    }


@tool(
    name="stop_show_clock",
    description="Stop the show clock timer",
    inputSchema={
        'type': 'object',
        'properties': {}
    }
)
async def stop_show_clock() -> Dict[str, Any]:
    """
    Stop the show clock timer.
    
    Returns:
        Dictionary with result
    """
    global _show_clock
    
    if not _show_clock['is_running']:
        return {'error': 'Show clock is not running'}
    
    elapsed = time.time() - _show_clock['start_time']
    _show_clock['is_running'] = False
    
    return {
        'success': True,
        'message': 'Show clock stopped',
        'elapsed_seconds': elapsed,
        'elapsed_formatted': _format_time(elapsed)
    }


@tool(
    name="get_show_time",
    description="Get current show time",
    inputSchema={
        'type': 'object',
        'properties': {}
    }
)
async def get_show_time() -> Dict[str, Any]:
    """
    Get current show time.
    
    Returns:
        Dictionary with show time
    """
    if not _show_clock['is_running'] or _show_clock['start_time'] is None:
        return {
            'is_running': False,
            'elapsed_seconds': 0,
            'elapsed_formatted': '00:00:00'
        }
    
    elapsed = time.time() - _show_clock['start_time']
    
    return {
        'is_running': True,
        'elapsed_seconds': elapsed,
        'elapsed_formatted': _format_time(elapsed),
        'tempo': _show_clock['tempo']
    }


@tool(
    name="start_song_timer",
    description="Start timer for current song",
    inputSchema={
        'type': 'object',
        'properties': {
            'song_name': {
                'type': 'string',
                'description': 'Name of the song'
            }
        }
    }
)
async def start_song_timer(song_name: str) -> Dict[str, Any]:
    """
    Start timer for current song.
    
    Args:
        song_name: Name of the song
        
    Returns:
        Dictionary with result
    """
    global _show_clock
    
    _show_clock['song_start_times'].append({
        'name': song_name,
        'start_time': time.time(),
        'end_time': None
    })
    _show_clock['current_song'] = song_name
    
    return {
        'success': True,
        'message': f'Song timer started: {song_name}',
        'song_name': song_name
    }


@tool(
    name="stop_song_timer",
    description="Stop timer for current song",
    inputSchema={
        'type': 'object',
        'properties': {}
    }
)
async def stop_song_timer() -> Dict[str, Any]:
    """
    Stop timer for current song.
    
    Returns:
        Dictionary with result
    """
    global _show_clock
    
    if not _show_clock['song_start_times']:
        return {'error': 'No song timer running'}
    
    last_song = _show_clock['song_start_times'][-1]
    last_song['end_time'] = time.time()
    
    elapsed = last_song['end_time'] - last_song['start_time']
    _show_clock['current_song'] = None
    
    return {
        'success': True,
        'message': f'Song timer stopped: {last_song["name"]}',
        'song_name': last_song['name'],
        'elapsed_seconds': elapsed,
        'elapsed_formatted': _format_time(elapsed)
    }


@tool(
    name="get_song_timings",
    description="Get all song timings from the show",
    inputSchema={
        'type': 'object',
        'properties': {}
    }
)
async def get_song_timings() -> Dict[str, Any]:
    """
    Get all song timings from the show.
    
    Returns:
        Dictionary with song timings
    """
    timings = []
    for song in _show_clock['song_start_times']:
        elapsed = (song['end_time'] or time.time()) - song['start_time']
        timings.append({
            'name': song['name'],
            'elapsed_seconds': elapsed,
            'elapsed_formatted': _format_time(elapsed)
        })
    
    return {
        'songs': timings,
        'total_songs': len(timings),
        'total_time': _format_time(sum(s['elapsed_seconds'] for s in timings))
    }


@tool(
    name="set_show_tempo",
    description="Set the show tempo",
    inputSchema={
        'type': 'object',
        'properties': {
            'tempo': {
                'type': 'number',
                'description': 'Tempo in BPM'
            }
        },
        'required': ['tempo']
    }
)
async def set_show_tempo(tempo: float) -> Dict[str, Any]:
    """
    Set the show tempo.
    
    Args:
        tempo: Tempo in BPM
        
    Returns:
        Dictionary with result
    """
    global _show_clock
    
    _show_clock['tempo'] = tempo
    
    return {
        'success': True,
        'message': f'Show tempo set to {tempo} BPM',
        'tempo': tempo
    }


@tool(
    name="get_show_status",
    description="Get complete show status",
    inputSchema={
        'type': 'object',
        'properties': {}
    }
)
async def get_show_status() -> Dict[str, Any]:
    """
    Get complete show status.
    
    Returns:
        Dictionary with show status
    """
    elapsed = 0
    if _show_clock['is_running'] and _show_clock['start_time']:
        elapsed = time.time() - _show_clock['start_time']
    
    return {
        'is_running': _show_clock['is_running'],
        'elapsed_seconds': elapsed,
        'elapsed_formatted': _format_time(elapsed),
        'tempo': _show_clock['tempo'],
        'current_song': _show_clock['current_song'],
        'total_songs': len(_show_clock['song_start_times'])
    }


def _format_time(seconds: float) -> str:
    """Format seconds to HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
