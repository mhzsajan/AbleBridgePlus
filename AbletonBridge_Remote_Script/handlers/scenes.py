"""
Scene Handler for AbleBridge++ Remote Script.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger('AbletonBridge_Remote_Script.handlers.scenes')


class SceneHandler:
    """Handler for scene operations."""
    
    def __init__(self, control_surface):
        """Initialize the scene handler."""
        self._control_surface = control_surface
        self._song = control_surface.song()
    
    def get_scenes(self) -> Dict[str, Any]:
        """Get information about all scenes."""
        try:
            scenes = []
            for i, scene in enumerate(self._song.scenes):
                scenes.append({
                    'index': i,
                    'name': scene.name,
                    'color_index': scene.color_index,
                    'is_playing': scene.is_playing,
                    'clip_slots_count': len(scene.clip_slots)
                })
            
            return {
                'scenes': scenes,
                'count': len(scenes)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def create_scene(self, index: int = -1) -> Dict[str, Any]:
        """Create a new scene."""
        try:
            self._song.create_scene(index)
            return {'success': True, 'message': 'Scene created'}
        except Exception as e:
            return {'error': str(e)}
    
    def delete_scene(self, scene_index: int) -> Dict[str, Any]:
        """Delete a scene."""
        if scene_index < 0 or scene_index >= len(self._song.scenes):
            return {'error': f'Invalid scene index: {scene_index}'}
        
        try:
            scene = self._song.scenes[scene_index]
            self._song.delete_scene(scene)
            return {'success': True, 'message': 'Scene deleted'}
        except Exception as e:
            return {'error': str(e)}
    
    def fire_scene(self, scene_index: int) -> Dict[str, Any]:
        """Fire (launch) a scene."""
        if scene_index < 0 or scene_index >= len(self._song.scenes):
            return {'error': f'Invalid scene index: {scene_index}'}
        
        try:
            scene = self._song.scenes[scene_index]
            scene.fire()
            return {'success': True, 'message': 'Scene fired'}
        except Exception as e:
            return {'error': str(e)}
    
    def set_scene_name(self, scene_index: int, name: str) -> Dict[str, Any]:
        """Set scene name."""
        if scene_index < 0 or scene_index >= len(self._song.scenes):
            return {'error': f'Invalid scene index: {scene_index}'}
        
        try:
            scene = self._song.scenes[scene_index]
            scene.name = name
            return {'success': True, 'message': 'Scene name updated'}
        except Exception as e:
            return {'error': str(e)}
    
    def set_scene_color(self, scene_index: int, color_index: int) -> Dict[str, Any]:
        """Set scene color."""
        if scene_index < 0 or scene_index >= len(self._song.scenes):
            return {'error': f'Invalid scene index: {scene_index}'}
        
        if color_index < 0 or color_index > 69:
            return {'error': f'Invalid color index: {color_index}'}
        
        try:
            scene = self._song.scenes[scene_index]
            scene.color_index = color_index
            return {'success': True, 'message': 'Scene color updated'}
        except Exception as e:
            return {'error': str(e)}
