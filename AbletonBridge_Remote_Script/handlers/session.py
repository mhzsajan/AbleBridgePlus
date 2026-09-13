"""
Session Handler for Enhanced AbletonBridge Remote Script.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger('AbletonBridge_Remote_Script.handlers.session')


class SessionHandler:
    """Handler for session operations."""
    
    def __init__(self, control_surface):
        """Initialize the session handler."""
        self._control_surface = control_surface
        self._song = control_surface.song()
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get session information."""
        try:
            return {
                'tempo': self._song.tempo,
                'time_signature_numerator': self._song.signature_numerator,
                'time_signature_denominator': self._song.signature_denominator,
                'is_playing': self._song.is_playing,
                'is_recording': self._song.is_recording,
                'current_time': self._song.current_song_time,
                'track_count': len(self._song.tracks),
                'scene_count': len(self._song.scenes),
                'song_length': self._song.length
            }
        except Exception as e:
            return {'error': str(e)}
    
    def set_tempo(self, tempo: float) -> Dict[str, Any]:
        """Set the tempo."""
        try:
            self._song.tempo = tempo
            return {'success': True, 'message': f'Tempo set to {tempo}'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_tempo(self) -> Dict[str, Any]:
        """Get the tempo."""
        try:
            return {'tempo': self._song.tempo}
        except Exception as e:
            return {'error': str(e)}
    
    def start_playback(self) -> Dict[str, Any]:
        """Start playback."""
        try:
            self._song.start_playing()
            return {'success': True, 'message': 'Playback started'}
        except Exception as e:
            return {'error': str(e)}
    
    def stop_playback(self) -> Dict[str, Any]:
        """Stop playback."""
        try:
            self._song.stop_playing()
            return {'success': True, 'message': 'Playback stopped'}
        except Exception as e:
            return {'error': str(e)}
    
    def continue_playing(self) -> Dict[str, Any]:
        """Continue playback."""
        try:
            self._song.continue_playing()
            return {'success': True, 'message': 'Playback continued'}
        except Exception as e:
            return {'error': str(e)}
    
    def set_metronome(self, enabled: bool) -> Dict[str, Any]:
        """Enable or disable metronome."""
        try:
            self._song.metronome = enabled
            return {'success': True, 'message': f'Metronome {"enabled" if enabled else "disabled"}'}
        except Exception as e:
            return {'error': str(e)}
    
    def set_song_loop(self, enabled: bool) -> Dict[str, Any]:
        """Enable or disable arrangement loop."""
        try:
            self._song.loop = enabled
            return {'success': True, 'message': f'Loop {"enabled" if enabled else "disabled"}'}
        except Exception as e:
            return {'error': str(e)}
    
    def undo(self) -> Dict[str, Any]:
        """Undo last action."""
        try:
            self._song.undo()
            return {'success': True, 'message': 'Undo performed'}
        except Exception as e:
            return {'error': str(e)}
    
    def redo(self) -> Dict[str, Any]:
        """Redo last undone action."""
        try:
            self._song.redo()
            return {'success': True, 'message': 'Redo performed'}
        except Exception as e:
            return {'error': str(e)}
