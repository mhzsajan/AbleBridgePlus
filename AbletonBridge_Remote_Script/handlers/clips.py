"""
Clip Handler for AbleBridge++ Remote Script.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger('AbletonBridge_Remote_Script.handlers.clips')


class ClipHandler:
    """Handler for clip operations."""
    
    def __init__(self, control_surface):
        """Initialize the clip handler."""
        self._control_surface = control_surface
        self._song = control_surface.song()
    
    def get_clip_info(self, track_index: int, clip_index: int) -> Dict[str, Any]:
        """Get clip information."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        if clip_index < 0 or clip_index >= len(track.clip_slots):
            return {'error': f'Invalid clip index: {clip_index}'}
        
        clip_slot = track.clip_slots[clip_index]
        
        if not clip_slot.has_clip:
            return {'error': 'No clip in slot'}
        
        clip = clip_slot.clip
        
        return {
            'track_index': track_index,
            'clip_index': clip_index,
            'name': clip.name,
            'is_playing': clip.is_playing,
            'is_recording': clip.is_recording,
            'length': clip.length,
            'looping': clip.looping,
            'loop_start': clip.loop_start,
            'loop_end': clip.loop_end,
            'color_index': clip.color_index
        }
    
    def create_clip(self, track_index: int, clip_index: int, length: float = 4.0) -> Dict[str, Any]:
        """Create a new MIDI clip."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        if clip_index < 0 or clip_index >= len(track.clip_slots):
            return {'error': f'Invalid clip index: {clip_index}'}
        
        clip_slot = track.clip_slots[clip_index]
        
        try:
            clip_slot.create_clip(length)
            return {'success': True, 'message': 'Clip created'}
        except Exception as e:
            return {'error': str(e)}
    
    def delete_clip(self, track_index: int, clip_index: int) -> Dict[str, Any]:
        """Delete a clip."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        if clip_index < 0 or clip_index >= len(track.clip_slots):
            return {'error': f'Invalid clip index: {clip_index}'}
        
        clip_slot = track.clip_slots[clip_index]
        
        if not clip_slot.has_clip:
            return {'error': 'No clip in slot'}
        
        try:
            clip_slot.delete_clip()
            return {'success': True, 'message': 'Clip deleted'}
        except Exception as e:
            return {'error': str(e)}
    
    def fire_clip(self, track_index: int, clip_index: int) -> Dict[str, Any]:
        """Fire (launch) a clip."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        if clip_index < 0 or clip_index >= len(track.clip_slots):
            return {'error': f'Invalid clip index: {clip_index}'}
        
        clip_slot = track.clip_slots[clip_index]
        
        if not clip_slot.has_clip:
            return {'error': 'No clip in slot'}
        
        try:
            clip_slot.fire()
            return {'success': True, 'message': 'Clip fired'}
        except Exception as e:
            return {'error': str(e)}
    
    def stop_clip(self, track_index: int, clip_index: int) -> Dict[str, Any]:
        """Stop a clip."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        if clip_index < 0 or clip_index >= len(track.clip_slots):
            return {'error': f'Invalid clip index: {clip_index}'}
        
        clip_slot = track.clip_slots[clip_index]
        
        if not clip_slot.has_clip:
            return {'error': 'No clip in slot'}
        
        try:
            clip_slot.stop()
            return {'success': True, 'message': 'Clip stopped'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_clip_notes(self, track_index: int, clip_index: int) -> Dict[str, Any]:
        """Get MIDI notes from a clip."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        if clip_index < 0 or clip_index >= len(track.clip_slots):
            return {'error': f'Invalid clip index: {clip_index}'}
        
        clip_slot = track.clip_slots[clip_index]
        
        if not clip_slot.has_clip:
            return {'error': 'No clip in slot'}
        
        clip = clip_slot.clip
        
        if not clip.is_midi_clip:
            return {'error': 'Not a MIDI clip'}
        
        try:
            notes = []
            for note in clip.notes:
                notes.append({
                    'pitch': note.pitch,
                    'start_time': note.start_time,
                    'duration': note.duration,
                    'velocity': note.velocity,
                    'mute': note.mute
                })
            
            return {'notes': notes, 'count': len(notes)}
        except Exception as e:
            return {'error': str(e)}
    
    def add_notes_to_clip(self, track_index: int, clip_index: int, notes: List[Dict]) -> Dict[str, Any]:
        """Add MIDI notes to a clip."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        if clip_index < 0 or clip_index >= len(track.clip_slots):
            return {'error': f'Invalid clip index: {clip_index}'}
        
        clip_slot = track.clip_slots[clip_index]
        
        if not clip_slot.has_clip:
            return {'error': 'No clip in slot'}
        
        clip = clip_slot.clip
        
        if not clip.is_midi_clip:
            return {'error': 'Not a MIDI clip'}
        
        try:
            from Live.Clip import MidiNote
            midi_notes = []
            for note in notes:
                midi_notes.append(MidiNote(
                    note['pitch'],
                    note['start_time'],
                    note['duration'],
                    note['velocity'],
                    note.get('mute', False)
                ))
            
            clip.set_notes(midi_notes)
            return {'success': True, 'message': f'Added {len(notes)} notes'}
        except Exception as e:
            return {'error': str(e)}
    
    def clear_clip_notes(self, track_index: int, clip_index: int) -> Dict[str, Any]:
        """Clear all notes from a clip."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        if clip_index < 0 or clip_index >= len(track.clip_slots):
            return {'error': f'Invalid clip index: {clip_index}'}
        
        clip_slot = track.clip_slots[clip_index]
        
        if not clip_slot.has_clip:
            return {'error': 'No clip in slot'}
        
        clip = clip_slot.clip
        
        if not clip.is_midi_clip:
            return {'error': 'Not a MIDI clip'}
        
        try:
            clip.clear_all_notes()
            return {'success': True, 'message': 'Notes cleared'}
        except Exception as e:
            return {'error': str(e)}
    
    def duplicate_clip(self, track_index: int, clip_index: int, target_clip_index: int) -> Dict[str, Any]:
        """Duplicate a clip to another slot."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        if clip_index < 0 or clip_index >= len(track.clip_slots):
            return {'error': f'Invalid clip index: {clip_index}'}
        
        if target_clip_index < 0 or target_clip_index >= len(track.clip_slots):
            return {'error': f'Invalid target clip index: {target_clip_index}'}
        
        clip_slot = track.clip_slots[clip_index]
        
        if not clip_slot.has_clip:
            return {'error': 'No clip in slot'}
        
        try:
            clip_slot.duplicate_clip_to(target_clip_index)
            return {'success': True, 'message': 'Clip duplicated'}
        except Exception as e:
            return {'error': str(e)}
    
    def set_clip_name(self, track_index: int, clip_index: int, name: str) -> Dict[str, Any]:
        """Set clip name."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        if clip_index < 0 or clip_index >= len(track.clip_slots):
            return {'error': f'Invalid clip index: {clip_index}'}
        
        clip_slot = track.clip_slots[clip_index]
        
        if not clip_slot.has_clip:
            return {'error': 'No clip in slot'}
        
        try:
            clip_slot.clip.name = name
            return {'success': True, 'message': 'Clip name updated'}
        except Exception as e:
            return {'error': str(e)}
    
    def set_clip_color(self, track_index: int, clip_index: int, color_index: int) -> Dict[str, Any]:
        """Set clip color."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        if clip_index < 0 or clip_index >= len(track.clip_slots):
            return {'error': f'Invalid clip index: {clip_index}'}
        
        clip_slot = track.clip_slots[clip_index]
        
        if not clip_slot.has_clip:
            return {'error': 'No clip in slot'}
        
        if color_index < 0 or color_index > 69:
            return {'error': f'Invalid color index: {color_index}'}
        
        try:
            clip_slot.clip.color_index = color_index
            return {'success': True, 'message': 'Clip color updated'}
        except Exception as e:
            return {'error': str(e)}
