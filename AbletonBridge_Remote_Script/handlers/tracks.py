"""
Track Handler for AbleBridge++ Remote Script.

This handler provides track management functionality including:
- Track information
- Track creation/deletion
- Track routing (with enhanced channel exposure)
- Track properties
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger('AbletonBridge_Remote_Script.handlers.tracks')


class TrackHandler:
    """Handler for track operations."""
    
    def __init__(self, control_surface):
        """
        Initialize the track handler.
        
        Args:
            control_surface: Ableton control surface
        """
        self._control_surface = control_surface
        self._song = control_surface.song()
    
    def get_all_tracks_info(self) -> Dict[str, Any]:
        """
        Get information about all tracks.
        
        Returns:
            Dictionary with track information
        """
        tracks = []
        
        for i, track in enumerate(self._song.tracks):
            track_info = self._get_track_info(track, i)
            tracks.append(track_info)
        
        return {
            'tracks': tracks,
            'count': len(tracks)
        }
    
    def get_track_info(self, track_index: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific track.
        
        Args:
            track_index: Track index
            
        Returns:
            Dictionary with track information
        """
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        return self._get_track_info(track, track_index)
    
    def _get_track_info(self, track, index: int) -> Dict[str, Any]:
        """
        Get track information dictionary.
        
        Args:
            track: Ableton track object
            index: Track index
            
        Returns:
            Dictionary with track information
        """
        # Get routing information with enhanced channel exposure
        routing_info = self._get_routing_info(track)
        
        return {
            'index': index,
            'name': track.name,
            'is_audio_track': track.is_audio_track,
            'is_midi_track': track.is_midi_track,
            'is_return_track': track.is_return_track,
            'is_master_track': track.is_master_track,
            'is_group_track': track.is_group_track,
            'is_foldable': track.is_foldable,
            'fold_state': track.fold_state,
            'color_index': track.color_index,
            'mute': track.mute,
            'solo': track.solo,
            'arm': track.arm,
            'volume': track.mixer_device.volume.value,
            'panning': track.mixer_device.panning.value if hasattr(track.mixer_device, 'panning') else None,
            'input_routing_type': track.input_routing_type,
            'input_routing_channel': track.input_routing_channel,
            'output_routing_type': track.output_routing_type,
            'output_routing_channel': track.output_routing_channel,
            'routing': routing_info,
            'devices_count': len(track.devices),
            'clips_count': len(track.clip_slots)
        }
    
    def _get_routing_info(self, track) -> Dict[str, Any]:
        """
        Get routing information for a track with enhanced channel exposure.
        
        This is the key enhancement - we now expose all available routing channels.
        
        Args:
            track: Ableton track object
            
        Returns:
            Dictionary with routing information
        """
        routing_info = {
            'available_input_routing_types': [],
            'available_input_routing_channels': [],
            'available_output_routing_types': [],
            'available_output_routing_channels': []
        }
        
        # Get available input routing types
        try:
            if hasattr(track, 'available_input_routing_types'):
                routing_info['available_input_routing_types'] = [
                    {'name': rt.display_name, 'type': rt.type}
                    for rt in track.available_input_routing_types
                ]
        except Exception as e:
            logger.warning(f"Could not get input routing types: {e}")
        
        # Get available input routing channels (NEW - this was missing in original AbletonBridge)
        try:
            if hasattr(track, 'available_input_routing_channels'):
                routing_info['available_input_routing_channels'] = [
                    {'name': rc.display_name, 'type': rc.type}
                    for rc in track.available_input_routing_channels
                ]
        except Exception as e:
            logger.warning(f"Could not get input routing channels: {e}")
        
        # Get available output routing types
        try:
            if hasattr(track, 'available_output_routing_types'):
                routing_info['available_output_routing_types'] = [
                    {'name': rt.display_name, 'type': rt.type}
                    for rt in track.available_output_routing_types
                ]
        except Exception as e:
            logger.warning(f"Could not get output routing types: {e}")
        
        # Get available output routing channels (NEW - this was missing in original AbletonBridge)
        try:
            if hasattr(track, 'available_output_routing_channels'):
                routing_info['available_output_routing_channels'] = [
                    {'name': rc.display_name, 'type': rc.type}
                    for rc in track.available_output_routing_channels
                ]
        except Exception as e:
            logger.warning(f"Could not get output routing channels: {e}")
        
        return routing_info
    
    def get_track_routing(self, track_index: int) -> Dict[str, Any]:
        """
        Get routing information for a track.
        
        Args:
            track_index: Track index
            
        Returns:
            Dictionary with routing information
        """
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        return self._get_routing_info(track)
    
    def set_track_routing(self, track_index: int, input_type: Optional[str] = None,
                         input_channel: Optional[str] = None, output_type: Optional[str] = None,
                         output_channel: Optional[str] = None) -> Dict[str, Any]:
        """
        Set routing for a track.
        
        Args:
            track_index: Track index
            input_type: Input routing type name
            input_channel: Input routing channel name
            output_type: Output routing type name
            output_channel: Output routing channel name
            
        Returns:
            Dictionary with result
        """
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        try:
            # Set input routing type
            if input_type:
                for rt in track.available_input_routing_types:
                    if rt.display_name == input_type:
                        track.input_routing_type = rt
                        break
            
            # Set input routing channel
            if input_channel:
                for rc in track.available_input_routing_channels:
                    if rc.display_name == input_channel:
                        track.input_routing_channel = rc
                        break
            
            # Set output routing type
            if output_type:
                for rt in track.available_output_routing_types:
                    if rt.display_name == output_type:
                        track.output_routing_type = rt
                        break
            
            # Set output routing channel
            if output_channel:
                for rc in track.available_output_routing_channels:
                    if rc.display_name == output_channel:
                        track.output_routing_channel = rc
                        break
            
            return {'success': True, 'message': 'Routing updated'}
            
        except Exception as e:
            return {'error': str(e)}
    
    def create_midi_track(self, index: int = -1) -> Dict[str, Any]:
        """
        Create a new MIDI track.
        
        Args:
            index: Position to insert the track (-1 = end)
            
        Returns:
            Dictionary with result
        """
        try:
            self._song.create_midi_track(index)
            return {'success': True, 'message': 'MIDI track created'}
        except Exception as e:
            return {'error': str(e)}
    
    def create_audio_track(self, index: int = -1) -> Dict[str, Any]:
        """
        Create a new audio track.
        
        Args:
            index: Position to insert the track (-1 = end)
            
        Returns:
            Dictionary with result
        """
        try:
            self._song.create_audio_track(index)
            return {'success': True, 'message': 'Audio track created'}
        except Exception as e:
            return {'error': str(e)}
    
    def delete_track(self, track_index: int) -> Dict[str, Any]:
        """
        Delete a track.
        
        Args:
            track_index: Track index
            
        Returns:
            Dictionary with result
        """
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        try:
            track = self._song.tracks[track_index]
            self._song.delete_track(track)
            return {'success': True, 'message': 'Track deleted'}
        except Exception as e:
            return {'error': str(e)}
    
    def duplicate_track(self, track_index: int) -> Dict[str, Any]:
        """
        Duplicate a track.
        
        Args:
            track_index: Track index
            
        Returns:
            Dictionary with result
        """
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        try:
            track = self._song.tracks[track_index]
            self._song.duplicate_track(track)
            return {'success': True, 'message': 'Track duplicated'}
        except Exception as e:
            return {'error': str(e)}
    
    def set_track_name(self, track_index: int, name: str) -> Dict[str, Any]:
        """
        Set track name.
        
        Args:
            track_index: Track index
            name: New track name
            
        Returns:
            Dictionary with result
        """
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        try:
            track = self._song.tracks[track_index]
            track.name = name
            return {'success': True, 'message': 'Track name updated'}
        except Exception as e:
            return {'error': str(e)}
    
    def set_track_color(self, track_index: int, color_index: int) -> Dict[str, Any]:
        """
        Set track color.
        
        Args:
            track_index: Track index
            color_index: Color index (0-69)
            
        Returns:
            Dictionary with result
        """
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        if color_index < 0 or color_index > 69:
            return {'error': f'Invalid color index: {color_index}'}
        
        try:
            track = self._song.tracks[track_index]
            track.color_index = color_index
            return {'success': True, 'message': 'Track color updated'}
        except Exception as e:
            return {'error': str(e)}
    
    def select_track(self, track_index: int) -> Dict[str, Any]:
        """
        Select a track.
        
        Args:
            track_index: Track index
            
        Returns:
            Dictionary with result
        """
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        try:
            track = self._song.tracks[track_index]
            self._view.selected_track = track
            return {'success': True, 'message': 'Track selected'}
        except Exception as e:
            return {'error': str(e)}
    
    def set_track_arm(self, track_index: int, arm: bool) -> Dict[str, Any]:
        """
        Set track arm state.
        
        Args:
            track_index: Track index
            arm: Arm state
            
        Returns:
            Dictionary with result
        """
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        try:
            track = self._song.tracks[track_index]
            track.arm = arm
            return {'success': True, 'message': f'Track arm set to {arm}'}
        except Exception as e:
            return {'error': str(e)}
    
    def set_track_monitoring(self, track_index: int, state: int) -> Dict[str, Any]:
        """
        Set track monitoring state.
        
        Args:
            track_index: Track index
            state: 0=IN, 1=AUTO, 2=OFF
            
        Returns:
            Dictionary with result
        """
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        if state not in [0, 1, 2]:
            return {'error': f'Invalid monitoring state: {state}'}
        
        try:
            track = self._song.tracks[track_index]
            track.monitoring_state = state
            return {'success': True, 'message': f'Monitoring state set to {state}'}
        except Exception as e:
            return {'error': str(e)}
    
    def freeze_track(self, track_index: int) -> Dict[str, Any]:
        """
        Freeze a track.
        
        Args:
            track_index: Track index
            
        Returns:
            Dictionary with result
        """
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        try:
            track = self._song.tracks[track_index]
            track.freeze()
            return {'success': True, 'message': 'Track frozen'}
        except Exception as e:
            return {'error': str(e)}
    
    def unfreeze_track(self, track_index: int) -> Dict[str, Any]:
        """
        Unfreeze a track.
        
        Args:
            track_index: Track index
            
        Returns:
            Dictionary with result
        """
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        try:
            track = self._song.tracks[track_index]
            track.unfreeze()
            return {'success': True, 'message': 'Track unfrozen'}
        except Exception as e:
            return {'error': str(e)}
    
    def group_tracks(self, track_indices: List[int]) -> Dict[str, Any]:
        """
        Group tracks together.
        
        Note: This is documented as not fully supported via LOM.
        Grouping requires manual UI interaction.
        
        Args:
            track_indices: List of track indices to group
            
        Returns:
            Dictionary with result
        """
        # Note: LOM grouping is limited
        # This is documented in ARCHITECTURE.md
        return {
            'error': 'Grouping tracks requires manual UI interaction',
            'message': 'Please group tracks manually in Ableton Live'
        }
