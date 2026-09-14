"""
AbleBridge++ MCP Server Package.

A comprehensive AI integration layer for Ableton Live, built on the foundation of
AbletonBridge by hidingwill (https://github.com/hidingwill/AbletonBridge).
"""

__version__ = "0.1.0"
__author__ = "Sajan Maharjan"
__license__ = "MIT"
__description__ = "Enhanced AI integration layer for Ableton Live"

# Import main components
from MCP_Server.server import MCPServer
from MCP_Server.state import GlobalState
from MCP_Server.constants import SERVER_NAME, SERVER_VERSION
from MCP_Server.validation import ValidationError

__all__ = [
    'MCPServer',
    'GlobalState',
    'SERVER_NAME',
    'SERVER_VERSION',
    'ValidationError'
]
