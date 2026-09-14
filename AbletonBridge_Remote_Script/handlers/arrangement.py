"""
Arrangement Handler for AbleBridge++ Remote Script.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger('AbletonBridge_Remote_Script.handlers.arrangement')


class ArrangementHandler:
    """Handler for arrangement view operations."""
    
    def __init__(self, control_surface):
        """Initialize the arrangement handler."""
        self._control_surface = control_surface
        self._song = control_surface.song()
    
    def get_arrangement_overview(self) -> Dict[str, Any]:
        """Get arrangement overview."""
        try:
            return {
                'tempo': self._song.tempo,
                'time_signature_numerator': self._song.signature_numerator,
                'time_signature_denominator': self._song.signature_denominator,
                'track_count': len(self._song.tracks),
                'scene_count': len(self._song.scenes),
                'song_length': self._song.length
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_arrangement_clips(self, track_index: int) -> Dict[str, Any]:
        """Get arrangement clips for a track."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        try:
            clips = []
            for clip in track.arrangement_clips:
                clips.append({
                    'name': clip.name,
                    'start_time': clip.start_time,
                    'end_time': clip.end_time,
                    'length': clip.length
                })
            
            return {
                'track_index': track_index,
                'clips': clips,
                'count': len(clips)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def set_song_time(self, time: float) -> Dict[str, Any]:
        """Set the playback position."""
        try:
            self._song.current_song_time = time
            return {'success': True, 'message': f'Playback position set to {time}'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_song_time(self) -> Dict[str, Any]:
        """Get the current playback position."""
        try:
            return {
                'current_time': self._song.current_song_time,
                'is_playing': self._song.is_playing,
                'tempo': self._song.tempo
            }
        except Exception as e:
            return {'error': str(e)}
