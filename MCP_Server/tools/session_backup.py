"""
Session Backup Tools for AbleBridgePlus MCP Server.

Provides session backup, restore, and comparison functionality.
"""

import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional
from . import tool


class SessionBackup:
    """Session backup manager."""
    
    def __init__(self, backup_dir: str = None):
        """Initialize session backup."""
        if backup_dir is None:
            backup_dir = os.path.join(os.path.expanduser("~"), ".ablebridge_backups")
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    def backup_session(self, session_data: Dict[str, Any], name: str = None) -> Dict[str, Any]:
        """Create a session backup."""
        if name is None:
            name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = os.path.join(self.backup_dir, f"{name}.json")
        
        with open(backup_path, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        return {
            "status": "backup_created",
            "name": name,
            "path": backup_path,
            "timestamp": datetime.now().isoformat()
        }
    
    def restore_session(self, backup_name: str) -> Dict[str, Any]:
        """Restore session from backup."""
        backup_path = os.path.join(self.backup_dir, f"{backup_name}.json")
        
        if not os.path.exists(backup_path):
            return {
                "status": "error",
                "message": f"Backup '{backup_name}' not found"
            }
        
        with open(backup_path, 'r') as f:
            session_data = json.load(f)
        
        return {
            "status": "session_restored",
            "name": backup_name,
            "data": session_data
        }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups."""
        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                backups.append({
                    "name": filename[:-5],  # Remove .json
                    "path": filepath,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return sorted(backups, key=lambda x: x["modified"], reverse=True)
    
    def delete_backup(self, backup_name: str) -> Dict[str, Any]:
        """Delete a backup."""
        backup_path = os.path.join(self.backup_dir, f"{backup_name}.json")
        
        if not os.path.exists(backup_path):
            return {
                "status": "error",
                "message": f"Backup '{backup_name}' not found"
            }
        
        os.remove(backup_path)
        return {
            "status": "backup_deleted",
            "name": backup_name
        }


# Global instance
_session_backup = SessionBackup()


@tool(
    name="backup_session",
    description="Create a backup of the current session",
    input_schema={
        "type": "object",
        "properties": {
            "session_data": {
                "type": "object",
                "description": "Session data to backup"
            },
            "name": {
                "type": "string",
                "description": "Name for the backup (optional)"
            }
        },
        "required": ["session_data"]
    }
)
async def backup_session(session_data: Dict[str, Any], name: str = None) -> Dict[str, Any]:
    """Create a backup of the current session."""
    return _session_backup.backup_session(session_data, name)


@tool(
    name="restore_session",
    description="Restore session from a backup",
    input_schema={
        "type": "object",
        "properties": {
            "backup_name": {
                "type": "string",
                "description": "Name of the backup to restore"
            }
        },
        "required": ["backup_name"]
    }
)
async def restore_session(backup_name: str) -> Dict[str, Any]:
    """Restore session from a backup."""
    return _session_backup.restore_session(backup_name)


@tool(
    name="list_backups",
    description="List all available session backups",
    input_schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def list_backups() -> Dict[str, Any]:
    """List all available session backups."""
    backups = _session_backup.list_backups()
    return {
        "backups": backups,
        "count": len(backups)
    }


@tool(
    name="delete_backup",
    description="Delete a session backup",
    input_schema={
        "type": "object",
        "properties": {
            "backup_name": {
                "type": "string",
                "description": "Name of the backup to delete"
            }
        },
        "required": ["backup_name"]
    }
)
async def delete_backup(backup_name: str) -> Dict[str, Any]:
    """Delete a session backup."""
    return _session_backup.delete_backup(backup_name)
