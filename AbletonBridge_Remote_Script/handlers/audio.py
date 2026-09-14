"""
Audio Handler for AbleBridge++ Remote Script.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger('AbletonBridge_Remote_Script.handlers.audio')


class AudioHandler:
    """Handler for audio operations."""
    
    def __init__(self, control_surface):
        """Initialize the audio handler."""
        self._control_surface = control_surface
        self._song = control_surface.song()
    
    def analyze_track_audio(self, track_index: int) -> Dict[str, Any]:
        """Analyze audio levels on a track."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        try:
            return {
                'track_index': track_index,
                'name': track.name,
                'output_meter_left': track.output_meter_left,
                'output_meter_right': track.output_meter_right,
                'peak_left': track.output_meter_left,
                'peak_right': track.output_meter_right
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_track_input_meters(self, track_index: int = None) -> Dict[str, Any]:
        """Get input meter levels."""
        if track_index is None:
            # Get all tracks
            meters = []
            for i, track in enumerate(self._song.tracks):
                if track.is_audio_track:
                    meters.append({
                        'track_index': i,
                        'name': track.name,
                        'input_meter_left': track.input_meter_left,
                        'input_meter_right': track.input_meter_right
                    })
            return {'meters': meters}
        else:
            if track_index < 0 or track_index >= len(self._song.tracks):
                return {'error': f'Invalid track index: {track_index}'}
            
            track = self._song.tracks[track_index]
            return {
                'track_index': track_index,
                'name': track.name,
                'input_meter_left': track.input_meter_left,
                'input_meter_right': track.input_meter_right
            }
