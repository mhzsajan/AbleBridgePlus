"""
Scene Macros Tools for AbleBridgePlus MCP Server.

Provides scene macro creation and management for live shows.
"""

import json
import os
from typing import Any, Dict, List, Optional
from . import tool


class SceneMacros:
    """Scene macros manager."""
    
    def __init__(self, macros_dir: str = None):
        """Initialize scene macros."""
        if macros_dir is None:
            macros_dir = os.path.join(os.path.expanduser("~"), ".ablebridge_macros")
        self.macros_dir = macros_dir
        os.makedirs(macros_dir, exist_ok=True)
        
        self.macros = {}
        self._load_macros()
    
    def _load_macros(self):
        """Load macros from disk."""
        macros_file = os.path.join(self.macros_dir, "scene_macros.json")
        if os.path.exists(macros_file):
            with open(macros_file, 'r') as f:
                self.macros = json.load(f)
    
    def _save_macros(self):
        """Save macros to disk."""
        macros_file = os.path.join(self.macros_dir, "scene_macros.json")
        with open(macros_file, 'w') as f:
            json.dump(self.macros, f, indent=2)
    
    def create_macro(self, name: str, scenes: List[int], description: str = "") -> Dict[str, Any]:
        """Create a scene macro."""
        if name in self.macros:
            return {
                "status": "error",
                "message": f"Macro '{name}' already exists"
            }
        
        self.macros[name] = {
            "name": name,
            "scenes": scenes,
            "description": description,
            "created": __import__('datetime').datetime.now().isoformat()
        }
        
        self._save_macros()
        
        return {
            "status": "macro_created",
            "name": name,
            "scenes": scenes
        }
    
    def fire_macro(self, name: str) -> Dict[str, Any]:
        """Fire a scene macro."""
        if name not in self.macros:
            return {
                "status": "error",
                "message": f"Macro '{name}' not found"
            }
        
        macro = self.macros[name]
        scenes = macro.get("scenes", [])
        
        return {
            "status": "macro_fired",
            "name": name,
            "scenes": scenes,
            "message": f"Firing scenes: {scenes}"
        }
    
    def delete_macro(self, name: str) -> Dict[str, Any]:
        """Delete a scene macro."""
        if name not in self.macros:
            return {
                "status": "error",
                "message": f"Macro '{name}' not found"
            }
        
        del self.macros[name]
        self._save_macros()
        
        return {
            "status": "macro_deleted",
            "name": name
        }
    
    def list_macros(self) -> List[Dict[str, Any]]:
        """List all scene macros."""
        return list(self.macros.values())
    
    def get_macro(self, name: str) -> Dict[str, Any]:
        """Get a specific macro."""
        if name not in self.macros:
            return {
                "status": "error",
                "message": f"Macro '{name}' not found"
            }
        
        return {
            "status": "macro_found",
            "macro": self.macros[name]
        }


# Global instance
_scene_macros = SceneMacros()


@tool(
    name="create_scene_macro",
    description="Create a scene macro to fire multiple scenes at once",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Macro name"
            },
            "scenes": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "List of scene indices to fire"
            },
            "description": {
                "type": "string",
                "description": "Optional description"
            }
        },
        "required": ["name", "scenes"]
    }
)
async def create_scene_macro(name: str, scenes: List[int], description: str = "") -> Dict[str, Any]:
    """Create a scene macro to fire multiple scenes at once."""
    return _scene_macros.create_macro(name, scenes, description)


@tool(
    name="fire_scene_macro",
    description="Fire a scene macro",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Macro name to fire"
            }
        },
        "required": ["name"]
    }
)
async def fire_scene_macro(name: str) -> Dict[str, Any]:
    """Fire a scene macro."""
    return _scene_macros.fire_macro(name)


@tool(
    name="delete_scene_macro",
    description="Delete a scene macro",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Macro name to delete"
            }
        },
        "required": ["name"]
    }
)
async def delete_scene_macro(name: str) -> Dict[str, Any]:
    """Delete a scene macro."""
    return _scene_macros.delete_macro(name)


@tool(
    name="list_scene_macros",
    description="List all scene macros",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def list_scene_macros() -> Dict[str, Any]:
    """List all scene macros."""
    macros = _scene_macros.list_macros()
    return {
        "macros": macros,
        "count": len(macros)
    }
