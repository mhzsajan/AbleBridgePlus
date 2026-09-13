"""
Mixer Handler for Enhanced AbletonBridge Remote Script.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger('AbletonBridge_Remote_Script.handlers.mixer')


class MixerHandler:
    """Handler for mixer operations."""
    
    def __init__(self, control_surface):
        """Initialize the mixer handler."""
        self._control_surface = control_surface
        self._song = control_surface.song()
    
    def set_mixer(self, track_index: int, volume: Optional[float] = None,
                  pan: Optional[float] = None, mute: Optional[bool] = None,
                  solo: Optional[bool] = None) -> Dict[str, Any]:
        """Set mixer parameters for a track."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        try:
            if volume is not None:
                track.mixer_device.volume.value = volume
            
            if pan is not None and hasattr(track.mixer_device, 'panning'):
                track.mixer_device.panning.value = pan
            
            if mute is not None:
                track.mute = mute
            
            if solo is not None:
                track.solo = solo
            
            return {'success': True, 'message': 'Mixer parameters updated'}
        except Exception as e:
            return {'error': str(e)}
    
    def set_track_send(self, track_index: int, send_index: int, value: float) -> Dict[str, Any]:
        """Set a send level."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        if send_index < 0 or send_index >= len(track.mixer_device.sends):
            return {'error': f'Invalid send index: {send_index}'}
        
        try:
            track.mixer_device.sends[send_index].value = value
            return {'success': True, 'message': f'Send {send_index} set to {value}'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_track_meters(self, track_index: Optional[int] = None) -> Dict[str, Any]:
        """Get track meter levels."""
        if track_index is None:
            # Get all tracks
            meters = []
            for i, track in enumerate(self._song.tracks):
                meters.append({
                    'track_index': i,
                    'name': track.name,
                    'output_meter_left': track.output_meter_left,
                    'output_meter_right': track.output_meter_right
                })
            return {'meters': meters}
        else:
            if track_index < 0 or track_index >= len(self._song.tracks):
                return {'error': f'Invalid track index: {track_index}'}
            
            track = self._song.tracks[track_index]
            return {
                'track_index': track_index,
                'name': track.name,
                'output_meter_left': track.output_meter_left,
                'output_meter_right': track.output_meter_right
            }
