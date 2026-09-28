"""
AbleBridgePlus MCP Server Package.

A comprehensive AI integration layer for Ableton Live, built on the foundation of
AbletonBridge by hidingwill (https://github.com/hidingwill/AbletonBridge).
"""

# Single source of truth for the version. This used to be a hardcoded "0.1.0"
# here while version.py, constants.py and pyproject.toml each carried their own
# number, so one process reported four different versions.
from MCP_Server.version import __version__  # noqa: F401

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
