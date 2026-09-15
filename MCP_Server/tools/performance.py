"""
Performance Monitoring Tools for AbleBridgePlus MCP Server.

These tools provide CPU, memory, and latency monitoring.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional
from MCP_Server.tools import tool


# Performance history file
PERFORMANCE_HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".ablebridge", "performance_history.json")


def _load_performance_history() -> List[Dict]:
    """Load performance history from file."""
    if os.path.exists(PERFORMANCE_HISTORY_FILE):
        try:
            with open(PERFORMANCE_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_performance_history(history: List[Dict]):
    """Save performance history to file."""
    os.makedirs(os.path.dirname(PERFORMANCE_HISTORY_FILE), exist_ok=True)
    # Keep only last 100 entries
    if len(history) > 100:
        history = history[-100:]
    with open(PERFORMANCE_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)


@tool(
    name="get_cpu_usage",
    description="Get CPU usage per track/device",
    inputSchema={
        'type': 'object',
        'properties': {
            'track_index': {
                'type': 'integer',
                'description': 'Specific track index (optional, returns all if omitted)'
            }
        }
    }
)
async def get_cpu_usage(track_index: Optional[int] = None) -> Dict[str, Any]:
    """
    Get CPU usage.
    
    Args:
        track_index: Specific track index (optional)
        
    Returns:
        Dictionary with CPU usage information
    """
    # This is a placeholder
    # Real implementation would query Ableton's CPU usage
    return {
        'cpu_usage': 0.0,
        'track_index': track_index,
        'message': 'CPU monitoring requires Ableton integration'
    }


@tool(
    name="get_memory_usage",
    description="Get memory usage",
    inputSchema={
        'type': 'object',
        'properties': {}
    }
)
async def get_memory_usage() -> Dict[str, Any]:
    """
    Get memory usage.
    
    Returns:
        Dictionary with memory usage information
    """
    import psutil
    
    try:
        memory = psutil.virtual_memory()
        return {
            'total_mb': memory.total / (1024 * 1024),
            'available_mb': memory.available / (1024 * 1024),
            'used_mb': memory.used / (1024 * 1024),
            'percent': memory.percent,
            'message': 'Memory usage retrieved'
        }
    except Exception as e:
        return {
            'error': str(e),
            'message': 'Memory monitoring requires psutil'
        }


@tool(
    name="get_latency_info",
    description="Get latency information",
    inputSchema={
        'type': 'object',
        'properties': {}
    }
)
async def get_latency_info() -> Dict[str, Any]:
    """
    Get latency information.
    
    Returns:
        Dictionary with latency information
    """
    # This is a placeholder
    # Real implementation would query Ableton's latency settings
    return {
        'input_latency': 0.0,
        'output_latency': 0.0,
        'total_latency': 0.0,
        'buffer_size': 0,
        'sample_rate': 44100,
        'message': 'Latency monitoring requires Ableton integration'
    }


@tool(
    name="set_performance_alerts",
    description="Set performance alerts",
    inputSchema={
        'type': 'object',
        'properties': {
            'cpu_warning_threshold': {
                'type': 'number',
                'description': 'CPU usage warning threshold (0-100)'
            },
            'memory_warning_threshold': {
                'type': 'number',
                'description': 'Memory usage warning threshold (0-100)'
            },
            'latency_warning_threshold': {
                'type': 'number',
                'description': 'Latency warning threshold in ms'
            }
        }
    }
)
async def set_performance_alerts(
    cpu_warning_threshold: Optional[float] = None,
    memory_warning_threshold: Optional[float] = None,
    latency_warning_threshold: Optional[float] = None
) -> Dict[str, Any]:
    """
    Set performance alerts.
    
    Args:
        cpu_warning_threshold: CPU usage warning threshold
        memory_warning_threshold: Memory usage warning threshold
        latency_warning_threshold: Latency warning threshold
        
    Returns:
        Dictionary with result
    """
    config_file = os.path.join(os.path.expanduser("~"), ".ablebridge", "performance_config.json")
    
    config = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except Exception:
            pass
    
    if cpu_warning_threshold is not None:
        config['cpu_warning_threshold'] = cpu_warning_threshold
    if memory_warning_threshold is not None:
        config['memory_warning_threshold'] = memory_warning_threshold
    if latency_warning_threshold is not None:
        config['latency_warning_threshold'] = latency_warning_threshold
    
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    return {
        'success': True,
        'config': config,
        'message': 'Performance alerts configured'
    }


@tool(
    name="get_performance_history",
    description="Get performance history",
    inputSchema={
        'type': 'object',
        'properties': {
            'limit': {
                'type': 'integer',
                'description': 'Number of entries to retrieve (default: 10)'
            }
        }
    }
)
async def get_performance_history(limit: int = 10) -> Dict[str, Any]:
    """
    Get performance history.
    
    Args:
        limit: Number of entries to retrieve
        
    Returns:
        Dictionary with performance history
    """
    history = _load_performance_history()
    
    return {
        'history': history[-limit:],
        'count': len(history),
        'limit': limit
    }


@tool(
    name="optimize_performance",
    description="Get performance optimization suggestions",
    inputSchema={
        'type': 'object',
        'properties': {}
    }
)
async def optimize_performance() -> Dict[str, Any]:
    """
    Get performance optimization suggestions.
    
    Returns:
        Dictionary with optimization suggestions
    """
    suggestions = [
        {
            'type': 'freeze_track',
            'description': 'Freeze tracks with heavy plugins to reduce CPU usage',
            'priority': 'high'
        },
        {
            'type': 'reduce_buffer_size',
            'description': 'Reduce buffer size for lower latency',
            'priority': 'medium'
        },
        {
            'type': 'close_other_applications',
            'description': 'Close other applications to free up system resources',
            'priority': 'medium'
        },
        {
            'type': 'use_simpler_presets',
            'description': 'Use simpler plugin presets to reduce CPU usage',
            'priority': 'low'
        }
    ]
    
    return {
        'suggestions': suggestions,
        'message': 'Performance optimization suggestions'
    }
