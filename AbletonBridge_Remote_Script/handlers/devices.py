"""
Device Handler for AbleBridge++ Remote Script.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger('AbletonBridge_Remote_Script.handlers.devices')


class DeviceHandler:
    """Handler for device operations."""
    
    def __init__(self, control_surface):
        """Initialize the device handler."""
        self._control_surface = control_surface
        self._song = control_surface.song()
    
    def get_device_parameters(self, track_index: int, device_index: int) -> Dict[str, Any]:
        """Get device parameters."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        if device_index < 0 or device_index >= len(track.devices):
            return {'error': f'Invalid device index: {device_index}'}
        
        device = track.devices[device_index]
        
        try:
            params = []
            for param in device.parameters:
                params.append({
                    'name': param.name,
                    'value': param.value,
                    'min': param.min,
                    'max': param.max,
                    'is_enabled': param.is_enabled
                })
            
            return {
                'track_index': track_index,
                'device_index': device_index,
                'name': device.name,
                'type': device.type,
                'parameters': params,
                'parameter_count': len(params)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def set_device_parameter(self, track_index: int, device_index: int,
                           parameter_name: str, value: float) -> Dict[str, Any]:
        """Set a device parameter."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        if device_index < 0 or device_index >= len(track.devices):
            return {'error': f'Invalid device index: {device_index}'}
        
        device = track.devices[device_index]
        
        try:
            for param in device.parameters:
                if param.name == parameter_name:
                    param.value = value
                    return {'success': True, 'message': f'Parameter {parameter_name} set to {value}'}
            
            return {'error': f'Parameter not found: {parameter_name}'}
        except Exception as e:
            return {'error': str(e)}
    
    def set_device_enabled(self, track_index: int, device_index: int, enabled: bool) -> Dict[str, Any]:
        """Enable or disable a device."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        if device_index < 0 or device_index >= len(track.devices):
            return {'error': f'Invalid device index: {device_index}'}
        
        device = track.devices[device_index]
        
        try:
            device.is_enabled = enabled
            return {'success': True, 'message': f'Device {"enabled" if enabled else "disabled"}'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_device_info(self, track_index: int, device_index: int) -> Dict[str, Any]:
        """Get device information."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        if device_index < 0 or device_index >= len(track.devices):
            return {'error': f'Invalid device index: {device_index}'}
        
        device = track.devices[device_index]
        
        return {
            'track_index': track_index,
            'device_index': device_index,
            'name': device.name,
            'type': device.type,
            'is_enabled': device.is_enabled,
            'parameter_count': len(device.parameters)
        }
    
    def delete_device(self, track_index: int, device_index: int) -> Dict[str, Any]:
        """Delete a device."""
        if track_index < 0 or track_index >= len(self._song.tracks):
            return {'error': f'Invalid track index: {track_index}'}
        
        track = self._song.tracks[track_index]
        
        if device_index < 0 or device_index >= len(track.devices):
            return {'error': f'Invalid device index: {device_index}'}
        
        device = track.devices[device_index]
        
        try:
            track.delete_device(device)
            return {'success': True, 'message': 'Device deleted'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_appointed_device(self) -> Dict[str, Any]:
        """Get the currently selected device."""
        try:
            device = self._view.selected_track.view.selected_device
            if device is None:
                return {'error': 'No device selected'}
            
            return {
                'name': device.name,
                'type': device.type,
                'is_enabled': device.is_enabled
            }
        except Exception as e:
            return {'error': str(e)}
