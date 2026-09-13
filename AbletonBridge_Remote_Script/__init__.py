"""
Enhanced AbletonBridge Remote Script Package.

This Remote Script runs inside Ableton Live as a Control Surface.
It provides TCP/UDP communication with the MCP Server.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

__version__ = "0.1.0"
__author__ = "Sajan Maharjan"
__license__ = "MIT"
