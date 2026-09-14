"""
Backup Presets Tools for AbleBridge++ MCP Server.

Provides backup preset management for live shows.
"""

import json
import os
from typing import Any, Dict, List, Optional
from . import tool


class BackupPresets:
    """Backup presets manager."""
    
    def __init__(self, presets_dir: str = None):
        """Initialize backup presets."""
        if presets_dir is None:
            presets_dir = os.path.join(os.path.expanduser("~"), ".ablebridge_backup_presets")
        self.presets_dir = presets_dir
        os.makedirs(presets_dir, exist_ok=True)
        
        self.active_preset = None
    
    def save_preset(self, name: str, configuration: Dict[str, Any]) -> Dict[str, Any]:
        """Save a backup preset."""
        preset_path = os.path.join(self.presets_dir, f"{name}.json")
        
        preset_data = {
            "name": name,
            "configuration": configuration,
            "created": __import__('datetime').datetime.now().isoformat()
        }
        
        with open(preset_path, 'w') as f:
            json.dump(preset_data, f, indent=2)
        
        return {
            "status": "backup_preset_saved",
            "name": name,
            "path": preset_path
        }
    
    def load_preset(self, name: str) -> Dict[str, Any]:
        """Load a backup preset."""
        preset_path = os.path.join(self.presets_dir, f"{name}.json")
        
        if not os.path.exists(preset_path):
            return {
                "status": "error",
                "message": f"Backup preset '{name}' not found"
            }
        
        with open(preset_path, 'r') as f:
            preset_data = json.load(f)
        
        return {
            "status": "backup_preset_loaded",
            "preset": preset_data
        }
    
    def activate_preset(self, name: str) -> Dict[str, Any]:
        """Activate a backup preset."""
        result = self.load_preset(name)
        
        if result.get("status") == "error":
            return result
        
        self.active_preset = name
        
        return {
            "status": "backup_preset_activated",
            "name": name,
            "configuration": result["preset"]["configuration"]
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get backup preset status."""
        return {
            "active_preset": self.active_preset,
            "available_presets": self.list_presets()
        }
    
    def list_presets(self) -> List[Dict[str, Any]]:
        """List all backup presets."""
        presets = []
        
        for filename in os.listdir(self.presets_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.presets_dir, filename)
                with open(filepath, 'r') as f:
                    preset_data = json.load(f)
                presets.append({
                    "name": preset_data.get("name"),
                    "created": preset_data.get("created")
                })
        
        return presets
    
    def delete_preset(self, name: str) -> Dict[str, Any]:
        """Delete a backup preset."""
        preset_path = os.path.join(self.presets_dir, f"{name}.json")
        
        if not os.path.exists(preset_path):
            return {
                "status": "error",
                "message": f"Backup preset '{name}' not found"
            }
        
        os.remove(preset_path)
        
        if self.active_preset == name:
            self.active_preset = None
        
        return {
            "status": "backup_preset_deleted",
            "name": name
        }


# Global instance
_backup_presets = BackupPresets()


@tool(
    name="save_backup_preset",
    description="Save a backup preset configuration",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Preset name"
            },
            "configuration": {
                "type": "object",
                "description": "Backup configuration"
            }
        },
        "required": ["name", "configuration"]
    }
)
async def save_backup_preset(name: str, configuration: Dict[str, Any]) -> Dict[str, Any]:
    """Save a backup preset configuration."""
    return _backup_presets.save_preset(name, configuration)


@tool(
    name="load_backup_preset",
    description="Load a backup preset",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Preset name"
            }
        },
        "required": ["name"]
    }
)
async def load_backup_preset(name: str) -> Dict[str, Any]:
    """Load a backup preset."""
    return _backup_presets.load_preset(name)


@tool(
    name="activate_backup_preset",
    description="Activate a backup preset",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Preset name to activate"
            }
        },
        "required": ["name"]
    }
)
async def activate_backup_preset(name: str) -> Dict[str, Any]:
    """Activate a backup preset."""
    return _backup_presets.activate_preset(name)


@tool(
    name="get_backup_status",
    description="Get backup preset status",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def get_backup_status() -> Dict[str, Any]:
    """Get backup preset status."""
    return _backup_presets.get_status()
