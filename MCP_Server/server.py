"""
AbleBridgePlus MCP Server

A comprehensive AI integration layer for Ableton Live, built on the foundation of
AbletonBridge by hidingwill (https://github.com/hidingwill/AbletonBridge).

This server implements the Model Context Protocol (MCP) to connect AI tools with
Ableton's Live Object Model (LOM).
"""

import asyncio
import inspect as _inspect_mod
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional

# Sentinel for "no annotation supplied"; `inspect.Parameter.empty` is the real
# one, aliased so _json_type_ok can reference it without a local import.
inspect_empty = _inspect_mod.Parameter.empty

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
        """Decorator: register the wrapped function as a tool.

        ``name=`` overrides the advertised tool name. Previously any kwargs
        were accepted and discarded, so ``@mcp.tool(name="x")`` silently
        registered the function under its Python name instead.
        """
        def decorator(func):
            name = kwargs.get("name") or (args[0] if args and isinstance(args[0], str) else None)
            self._registry.register_tool(name or func.__name__, func)
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


def _type_name(annotation) -> str:
    """Human-readable name for a type annotation, for error messages."""
    import typing
    if annotation is None or annotation is type(None):
        return "null"
    origin = typing.get_origin(annotation)
    if origin is not None:
        args = typing.get_args(annotation)
        inner = ", ".join(_type_name(a) for a in args) if args else "any"
        return "{0}[{1}]".format(getattr(origin, "__name__", str(origin)), inner)
    return getattr(annotation, "__name__", str(annotation))


def _json_type_ok(value, annotation) -> bool:
    """Coarse JSON-type check of a value against a type annotation.

    Intentionally permissive: only obvious mismatches are rejected (a string
    where an int is declared, a scalar where a list is declared). Untyped and
    ``Any`` annotations always pass, as do ``Optional``/``Union`` members, so
    this never blocks a legitimate call.
    """
    import typing
    if annotation is inspect_empty or annotation is typing.Any:
        return True
    if annotation is None:
        return True
    origin = typing.get_origin(annotation)
    if origin is typing.Union:
        return any(_json_type_ok(value, a) for a in typing.get_args(annotation))
    if origin in (list, set, tuple, frozenset):
        return isinstance(value, (list, tuple))
    if origin is dict:
        return isinstance(value, dict)
    if origin is typing.Literal:
        return value in typing.get_args(annotation)
    if annotation is float:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if annotation is int:
        return isinstance(value, int) and not isinstance(value, bool)
    if annotation is bool:
        return isinstance(value, bool)
    if annotation is str:
        return isinstance(value, str)
    if isinstance(annotation, type):
        if annotation is float:
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if annotation is int:
            return isinstance(value, int) and not isinstance(value, bool)
        if annotation in (list, set, tuple, frozenset, dict):
            return isinstance(value, (list, tuple, dict))
        if not annotation.__module__.startswith("MCP_Server"):
            return True  # custom class: leave it to the tool
        return isinstance(value, annotation)
    return True

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
        
        # Hydrate the browser cache from disk (if present and fresh) so that
        # search_browser / resolve_device_uri work immediately at startup
        # instead of requiring a full 70s rescan in every new process.
        try:
            from MCP_Server.cache.browser import load_browser_cache_from_disk
            if load_browser_cache_from_disk():
                logger.info("Browser cache hydrated from disk at startup")
        except Exception as e:
            logger.warning("Browser cache disk hydration skipped: %s", e)

        # v0.6: hydrate persisted named checkpoints so restore_checkpoint
        # works across server restarts.
        try:
            from MCP_Server import checkpoints as _ckpt
            _ckpt.load_persisted()
            logger.info("Named checkpoints hydrated (%d)",
                        len(_ckpt.list_all()["named"]))
        except Exception as e:
            logger.warning("Checkpoint hydration skipped: %s", e)
        
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
        # v0.6.0: undo-safe experimentation
        from MCP_Server.tools import undo_safety
        # v0.6.x: MCP resources & prompts, whole-mix reference matching
        from MCP_Server.tools import resources_prompts, mix_matching
        # v0.7: spectral engine (Ears v2) — per-clip timbre analysis
        from MCP_Server.tools import spectral_analysis
        # v0.7: loudness (LUFS approximation) — jump-out detection
        from MCP_Server.tools import loudness_analysis
        # v0.8: Videosync2 show automation (timeline-baked video control)
        from MCP_Server.tools import vsync_automation

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
            audio_intelligence, producer, studio_memory,
            # v0.6.0
            undo_safety,
            # v0.6.x: resources/prompts handlers live in server dispatch,
            # mix_matching registers tools
            mix_matching,
            # v0.7
            spectral_analysis,
            loudness_analysis,
            # v0.8
            vsync_automation
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
            elif method == 'ping':
                # Both official SDKs send ping as a liveness probe; answering
                # -32601 made healthy clients report the server as dead.
                return {}
            elif method == 'tools/list':
                return await self._handle_list_tools(params)
            elif method == 'tools/call':
                return await self._handle_call_tool(params)
            elif method == 'resources/list':
                return await self._handle_list_resources(params)
            elif method == 'resources/templates/list':
                from MCP_Server.tools.resources_prompts import list_resource_templates
                return {'resourceTemplates': list_resource_templates()}
            elif method == 'resources/read':
                return await self._handle_read_resource(params)
            elif method == 'prompts/list':
                return await self._handle_list_prompts(params)
            elif method == 'prompts/get':
                return await self._handle_get_prompt(params)
            else:
                return self._error_response(
                    -32601,
                    f"Method not found: {method}"
                )
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return self._error_response(-32603, str(e))
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request.

        Negotiates the protocol version: if the client asks for a revision we
        support we echo it back, otherwise we return our newest. The previous
        hardcoded literal ignored ``params`` entirely.
        """
        from MCP_Server.constants import (PROTOCOL_VERSION,
                                          SUPPORTED_PROTOCOL_VERSIONS,
                                          SERVER_VERSION)
        requested = (params or {}).get('protocolVersion')
        if requested in SUPPORTED_PROTOCOL_VERSIONS:
            negotiated = requested
        else:
            negotiated = PROTOCOL_VERSION
        return {
            'protocolVersion': negotiated,
            'capabilities': {
                'tools': {},
                'resources': {},
                'prompts': {}
            },
            'serverInfo': {
                'name': 'AbleBridgePlus',
                'version': SERVER_VERSION
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
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            return self._error_response(
                -32602,
                "Invalid arguments for {0}: expected an object, got {1}".format(
                    tool_name, type(arguments).__name__))
        
        # Get the tool function
        tool_func = self.tool_registry.get_tool(tool_name)
        if not tool_func:
            return self._error_response(-32602, f"Tool not found: {tool_name}")
        
        # Validate arguments against the function signature BEFORE calling.
        # Previously nothing checked them, so a missing or misspelled argument
        # surfaced as a *successful* tools/call result whose text happened to
        # contain a Python TypeError. Per JSON-RPC that is -32602 Invalid
        # params: a client cannot otherwise tell "you called it wrong" from
        # "the tool ran and failed", and won't retry with corrected arguments.
        try:
            import inspect
            signature = inspect.signature(tool_func)
            accepts_kwargs = any(
                p.kind is inspect.Parameter.VAR_KEYWORD
                for p in signature.parameters.values())
            allowed = {n for n, p in signature.parameters.items()
                       if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                     inspect.Parameter.KEYWORD_ONLY)}
            accepts_positional = any(
                p.kind is inspect.Parameter.VAR_POSITIONAL
                for p in signature.parameters.values())

            unexpected = sorted(set(arguments) - allowed)
            if unexpected and not accepts_kwargs:
                return self._error_response(
                    -32602,
                    "Unknown argument(s) for {0}: {1}. Accepted: {2}".format(
                        tool_name, ", ".join(unexpected),
                        ", ".join(sorted(allowed)) or "(none)"))

            required = [
                n for n, p in signature.parameters.items()
                if n != 'ctx'
                and p.default is inspect.Parameter.empty
                and p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD,
                               inspect.Parameter.KEYWORD_ONLY)
            ]
            if not accepts_positional:
                missing = sorted(set(required) - set(arguments))
                if missing:
                    return self._error_response(
                        -32602,
                        "Missing required argument(s) for {0}: {1}".format(
                            tool_name, ", ".join(missing)))

            # Reject a value of the wrong JSON type up front so the agent gets a
            # pointed message instead of an exception from deep inside a tool.
            for pname, value in arguments.items():
                param = signature.parameters.get(pname)
                if param is None or param.annotation is inspect.Parameter.empty:
                    continue
                if not _json_type_ok(value, param.annotation):
                    return self._error_response(
                        -32602,
                        "Argument {0!r} of {1} should be {2}, got {3}".format(
                            pname, tool_name,
                            _type_name(param.annotation),
                            type(value).__name__))
        except (ValueError, TypeError) as e:
            return self._error_response(
                -32602, f"Could not inspect signature of {tool_name}: {e}")

        # Execute the tool
        try:
            import inspect
            call_args = dict(arguments)
            # New-style tools take a Context as first param; inject a shim.
            if 'ctx' in inspect.signature(tool_func).parameters:
                call_args['ctx'] = _ContextShim()
            result = await tool_func(**call_args)
            if isinstance(result, (set, tuple)):
                result = list(result)
            text = result if isinstance(result, str) else json.dumps(result, indent=2, default=str)
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
        from MCP_Server.tools.resources_prompts import list_resources
        return {'resources': list_resources()}
    
    async def _handle_read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request."""
        from MCP_Server.tools.resources_prompts import read_resource
        uri = params.get('uri')
        if not uri:
            return self._error_response(-32602, "Missing resource uri")
        try:
            return read_resource(uri)
        except ValueError as e:
            return self._error_response(-32602, str(e))
        except Exception as e:
            return self._error_response(-32603, f"Resource read failed: {e}")
    
    async def _handle_list_prompts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/list request."""
        from MCP_Server.tools.resources_prompts import list_prompts
        return {'prompts': list_prompts()}
    
    async def _handle_get_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/get request."""
        from MCP_Server.tools.resources_prompts import get_prompt
        name = params.get('name')
        if not name:
            return self._error_response(-32602, "Missing prompt name")
        try:
            return get_prompt(name, params.get('arguments') or {})
        except ValueError as e:
            return self._error_response(-32602, str(e))
        except Exception as e:
            return self._error_response(-32603, f"Prompt build failed: {e}")
    
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
