"""
AbleBridgePlus MCP Server

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
import time
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from MCP_Server.connections.ableton import get_ableton_connection, AbletonConnection
from MCP_Server.connections.m4l import get_m4l_connection, M4LConnection
from MCP_Server.constants import LOCALHOST, ABLETON_TCP_PORT
from MCP_Server.state import GlobalState
from MCP_Server.tools import ToolRegistry
import MCP_Server.state as state


class _FastMCPAdapter:
    """Minimal FastMCP-compatible adapter for the register_tools(mcp) pattern.

    The ported tool modules call ``@mcp.tool()`` inside ``register_tools(mcp)``.
    This adapter implements just that decorator so the modules register into
    the server's ToolRegistry instead of a real FastMCP instance.
    """

    def __init__(self, registry: ToolRegistry):
        self._registry = registry

    def tool(self, *args, **kwargs):
        """Decorator: register the wrapped function as a tool."""
        def decorator(func):
            self._registry.register_tool(func.__name__, func)
            return func
        return decorator


class _ContextShim:
    """Minimal MCP Context replacement for tools that report progress."""

    async def report_progress(self, current: float, total: float, message: str = None):
        """Best-effort progress reporting (no-op in this server)."""
        pass

    def info(self, message: str):
        pass

    def debug(self, message: str):
        pass

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
        # Share the module-level singletons so both the server and the tool
        # modules (via state.ableton_connection / get_ableton_connection) use
        # the same connections.
        self.ableton_connection = AbletonConnection(host=LOCALHOST, port=ABLETON_TCP_PORT)
        state.ableton_connection = self.ableton_connection
        self.m4l_connection = M4LConnection()
        state.m4l_connection = self.m4l_connection
        
        # Register all tools
        self._register_tools()
        
        logger.info("AbleBridgePlus MCP Server initialized")
    
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
        
        # v0.3.0 Live Show Control tools
        from MCP_Server.tools import show_clock, emergency_control, session_backup
        from MCP_Server.tools import performance_analytics, audio_presets
        from MCP_Server.tools import video_lighting, ai_enhancement
        from MCP_Server.tools import scene_macros, backup_presets
        
        # v0.4.0: context engine, music toolkit, doctor, autopilot
        from MCP_Server.tools import project_context, music_gen, doctor, show_autopilot
        # v0.5.0: audio intelligence, producer pipeline, studio memory
        from MCP_Server.tools import audio_intelligence, producer, studio_memory

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
            advanced_routing, ai_integration,
            # v0.3.0 Live Show Control tools
            show_clock, emergency_control, session_backup,
            performance_analytics, audio_presets,
            video_lighting, ai_enhancement,
            scene_macros, backup_presets,
            # v0.4.0
            project_context, music_gen, doctor, show_autopilot,
            # v0.5.0
            audio_intelligence, producer, studio_memory
        ]
        
        adapter = _FastMCPAdapter(self.tool_registry)
        for module in tool_modules:
            if hasattr(module, 'register_tools'):
                # New-style modules: register_tools(mcp) with @mcp.tool()
                module.register_tools(adapter)
            else:
                # Old-style modules: @tool(...) decorated functions
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
                'name': 'AbleBridgePlus',
                'version': '0.5.1'
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
            import inspect
            call_args = dict(arguments)
            # New-style tools take a Context as first param; inject a shim.
            if 'ctx' in inspect.signature(tool_func).parameters:
                call_args['ctx'] = _ContextShim()
            result = await tool_func(**call_args)
            text = result if isinstance(result, str) else json.dumps(result, indent=2)
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': text
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
        logger.info("Starting AbleBridgePlus MCP Server...")
        
        # Connect to Ableton
        try:
            self.ableton_connection.connect()
            logger.info("Connected to Ableton")
        except Exception as e:
            logger.warning(f"Could not connect to Ableton: {e}")
            logger.info("Server will start without Ableton connection")
        
        # Connect to M4L Bridge
        try:
            self.m4l_connection.connect()
            logger.info("Connected to M4L Bridge")
        except Exception as e:
            logger.warning(f"Could not connect to M4L Bridge: {e}")
            logger.info("Server will start without M4L Bridge")
        
        state.server_start_time = time.time()
        logger.info("AbleBridgePlus MCP Server started")
        logger.info("Ready to accept connections")
    
    async def stop(self):
        """Stop the MCP server."""
        logger.info("Stopping AbleBridgePlus MCP Server...")
        
        # Disconnect from Ableton
        try:
            self.ableton_connection.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from Ableton: {e}")
        
        # Disconnect from M4L Bridge
        try:
            self.m4l_connection.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from M4L Bridge: {e}")
        
        logger.info("AbleBridgePlus MCP Server stopped")


def main(argv=None):
    """Main entry point (synchronous; owns its own event loop).

    --transport stdio|tcp  (default stdio)
    --tcp-port N           (default 9891, tcp mode only)
    --no-banner            suppress the startup banner
    """
    import argparse
    parser = argparse.ArgumentParser(description='AbleBridgePlus MCP Server')
    parser.add_argument('--transport', choices=['stdio', 'tcp'], default='stdio')
    parser.add_argument('--tcp-port', type=int, default=9891)
    parser.add_argument('--no-banner', action='store_true')
    args = parser.parse_args(argv)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = MCPServer()

    try:
        if args.transport == 'stdio':
            # Answer the MCP handshake IMMEDIATELY: MCP clients (OpenCode,
            # Claude Desktop, ...) time out the initialize round-trip, so we
            # must not block on Ableton/M4L connections first. Tools connect
            # to Ableton lazily on first use instead.
            from MCP_Server.transports import serve_stdio_sync
            serve_stdio_sync(server, loop)
        else:
            loop.run_until_complete(server.start())
            # Web dashboard rides along with TCP mode (port 9880).
            try:
                from MCP_Server.dashboard import DashboardServer
                dashboard = DashboardServer()
                dashboard.ableton_connected = bool(
                    getattr(server.ableton_connection, "_connected", False))
                dashboard.tool_count = server.tool_registry.tool_count
                dashboard.set_tools_func(server.tool_registry.get_all_tools)
                dashboard.start()
            except Exception as dash_err:
                logger.warning("Dashboard not started: %s", dash_err)
            if not args.no_banner:
                banner = (
                    "\n"
                    "  ╔══════════════════════════════════════════╗\n"
                    "  ║   AbleBridgePlus MCP Server (TCP)          ║\n"
                    "  ║   Tools: {n:>3}                            ║\n"
                    "  ║   Listening on 127.0.0.1:{port:<6}         ║\n"
                    "  ╚══════════════════════════════════════════╝\n"
                ).format(n=server.tool_registry.tool_count, port=args.tcp_port)
                print(banner, file=sys.stderr)
            from MCP_Server.transports import serve_tcp
            loop.run_until_complete(serve_tcp(server, port=args.tcp_port))

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        loop.run_until_complete(server.stop())
        loop.close()


if __name__ == '__main__':
    main()
