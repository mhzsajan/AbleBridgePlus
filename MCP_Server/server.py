"""
Enhanced AbletonBridge MCP Server

A comprehensive AI integration layer for Ableton Live, built on the foundation of
AbletonBridge by hidingwill (https://github.com/hidingwill/AbletonBridge).

This server implements the Model Context Protocol (MCP) to connect AI tools with
Ableton's Live Object Model (LOM).
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from MCP_Server.connections.ableton import AbletonConnection
from MCP_Server.connections.m4l import M4LConnection
from MCP_Server.state import GlobalState
from MCP_Server.tools import ToolRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MCP_Server')


class MCPServer:
    """Main MCP Server class."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.state = GlobalState()
        self.tool_registry = ToolRegistry()
        self.ableton_connection = AbletonConnection()
        self.m4l_connection = M4LConnection()
        
        # Register all tools
        self._register_tools()
        
        logger.info("Enhanced AbletonBridge MCP Server initialized")
    
    def _register_tools(self):
        """Register all available tools."""
        # Core tools (from AbletonBridge)
        from MCP_Server.tools import tracks, clips, devices, mixer, browser
        from MCP_Server.tools import automation, arrangement, creative, grid
        from MCP_Server.tools import m4l_tools, midi_cc, scenes, session
        from MCP_Server.tools import snapshots, workflows
        
        # Enhanced tools (our additions)
        from MCP_Server.tools import midi_mapping, plugin_management
        from MCP_Server.tools import video_routing, setlist_management
        from MCP_Server.tools import performance, quick_presets
        from MCP_Server.tools import audio_analysis, template_system
        from MCP_Server.tools import advanced_routing, ai_integration
        
        # Register all tool modules
        tool_modules = [
            tracks, clips, devices, mixer, browser,
            automation, arrangement, creative, grid,
            m4l_tools, midi_cc, scenes, session,
            snapshots, workflows,
            # Enhanced tools
            midi_mapping, plugin_management,
            video_routing, setlist_management,
            performance, quick_presets,
            audio_analysis, template_system,
            advanced_routing, ai_integration
        ]
        
        for module in tool_modules:
            self.tool_registry.register_module(module)
        
        logger.info(f"Registered {self.tool_registry.tool_count} tools")
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an MCP request.
        
        Args:
            request: MCP request dictionary
            
        Returns:
            MCP response dictionary
        """
        try:
            method = request.get('method')
            params = request.get('params', {})
            
            if method == 'initialize':
                return await self._handle_initialize(params)
            elif method == 'tools/list':
                return await self._handle_list_tools(params)
            elif method == 'tools/call':
                return await self._handle_call_tool(params)
            elif method == 'resources/list':
                return await self._handle_list_resources(params)
            elif method == 'resources/read':
                return await self._handle_read_resource(params)
            else:
                return self._error_response(
                    -32601,
                    f"Method not found: {method}"
                )
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return self._error_response(-32603, str(e))
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        return {
            'protocolVersion': '2024-11-05',
            'capabilities': {
                'tools': {},
                'resources': {}
            },
            'serverInfo': {
                'name': 'Enhanced AbletonBridge',
                'version': '0.1.0'
            }
        }
    
    async def _handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools = self.tool_registry.get_all_tools()
        return {
            'tools': tools
        }
    
    async def _handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        
        if not tool_name:
            return self._error_response(-32602, "Missing tool name")
        
        # Get the tool function
        tool_func = self.tool_registry.get_tool(tool_name)
        if not tool_func:
            return self._error_response(-32602, f"Tool not found: {tool_name}")
        
        # Execute the tool
        try:
            result = await tool_func(**arguments)
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': json.dumps(result, indent=2)
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return self._error_response(-32603, str(e))
    
    async def _handle_list_resources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request."""
        return {
            'resources': []
        }
    
    async def _handle_read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request."""
        return self._error_response(-32601, "No resources available")
    
    def _error_response(self, code: int, message: str) -> Dict[str, Any]:
        """Create an error response."""
        return {
            'error': {
                'code': code,
                'message': message
            }
        }
    
    async def start(self):
        """Start the MCP server."""
        logger.info("Starting Enhanced AbletonBridge MCP Server...")
        
        # Connect to Ableton
        try:
            await self.ableton_connection.connect()
            logger.info("Connected to Ableton")
        except Exception as e:
            logger.warning(f"Could not connect to Ableton: {e}")
            logger.info("Server will start without Ableton connection")
        
        # Connect to M4L Bridge
        try:
            await self.m4l_connection.connect()
            logger.info("Connected to M4L Bridge")
        except Exception as e:
            logger.warning(f"Could not connect to M4L Bridge: {e}")
            logger.info("Server will start without M4L Bridge")
        
        logger.info("Enhanced AbletonBridge MCP Server started")
        logger.info("Ready to accept connections")
    
    async def stop(self):
        """Stop the MCP server."""
        logger.info("Stopping Enhanced AbletonBridge MCP Server...")
        
        # Disconnect from Ableton
        try:
            await self.ableton_connection.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from Ableton: {e}")
        
        # Disconnect from M4L Bridge
        try:
            await self.m4l_connection.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from M4L Bridge: {e}")
        
        logger.info("Enhanced AbletonBridge MCP Server stopped")


async def main():
    """Main entry point."""
    server = MCPServer()
    
    try:
        await server.start()
        
        # Keep the server running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await server.stop()


if __name__ == '__main__':
    asyncio.run(main())
