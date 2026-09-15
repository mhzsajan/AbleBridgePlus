"""Absolute-path launcher for the AbleBridge++ stdio MCP server.

MCP clients spawn this without a useful working directory, so -m
MCP_Server.server fails; this bootstraps sys.path from the file location.

Writes a stage trace to %TEMP%\\ablebridge_mcp_trace.log so startup stalls
under MCP clients can be diagnosed.
"""
import os
import sys
import time

TRACE = os.path.join(os.environ.get('TEMP', os.path.dirname(os.path.abspath(__file__))),
                     'ablebridge_mcp_trace.log')


def _trace(msg):
    try:
        with open(TRACE, 'a', encoding='utf-8') as f:
            f.write("{:.3f} [{}] {}\n".format(time.time(), os.getpid(), msg))
    except Exception:
        pass


_trace("=== launcher start, argv=" + repr(sys.argv))
_trace("stdin isatty=" + repr(sys.stdin.isatty()) + " stdout isatty=" + repr(sys.stdout.isatty()))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_trace("sys.path set")

from MCP_Server.server import MCPServer, main  # noqa: E402
_trace("imports done")

_trace("constructing MCPServer")
server = MCPServer()
_trace("MCPServer constructed, tools=" + str(server.tool_registry.tool_count))

import asyncio
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
_trace("event loop created")

from MCP_Server.transports import serve_stdio_sync
_trace("serving stdio")
serve_stdio_sync(server, loop)
_trace("serve_stdio_sync returned")
