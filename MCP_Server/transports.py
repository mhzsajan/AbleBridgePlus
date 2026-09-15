"""
MCP protocol transports for AbleBridgePlus.

Two ways for an MCP client (OpenCode, Claude Desktop, ...) to reach the
server:

- **stdio** (default): newline-delimited JSON-RPC on stdin/stdout. This is
  what MCP client configs spawn. Logging is forced to stderr in this mode —
  anything written to stdout would corrupt the protocol stream. Implemented
  with a blocking read loop plus a persistent event loop for dispatch,
  because asyncio's pipe APIs reject plain stdin/stdout handles on Windows.

- **tcp** (--transport tcp): JSON-RPC over TCP on localhost (default port
  9891). Useful for the dashboard and for multiple local clients sharing
  one Ableton connection.

Both transports are thin shells around ``MCPServer.handle_request``.
"""

import asyncio
import json
import logging
import sys

logger = logging.getLogger("MCP_Server.transport")


def _trace(msg):
    """Optional file tracing (ABLEBRIDGE_TRACE=1) for debugging spawns."""
    import os, time as _t
    if os.environ.get('ABLEBRIDGE_TRACE') != '1':
        return
    path = os.path.join(os.environ.get('TEMP', '.'), 'ablebridge_mcp_trace.log')
    try:
        with open(path, 'a', encoding='utf-8') as f:
            f.write("{:.3f} [{}] {}\n".format(_t.time(), os.getpid(), msg))
    except Exception:
        pass


def _force_stderr_logging():
    """Move all log output to stderr (stdout is protocol-only in stdio mode)."""
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root.addHandler(handler)


def _serialize(obj: dict) -> str:
    return json.dumps(obj, default=str) + "\n"


def _jsonrpc_wrap(request: dict, result: dict) -> dict:
    """Wrap a handler result in a proper JSON-RPC response envelope.

    ``handle_request`` returns either a bare result object or an
    ``{'error': {...}}`` dict; JSON-RPC requires success payloads nested
    under ``"result"`` and errors under ``"error"``.
    """
    rid = request.get('id')
    if isinstance(result, dict) and 'error' in result and len(result) == 1:
        return {'jsonrpc': '2.0', 'id': rid, 'error': result['error']}
    return {'jsonrpc': '2.0', 'id': rid, 'result': result}


def serve_stdio_sync(server, loop: asyncio.AbstractEventLoop) -> None:
    """Serve MCP over newline-delimited JSON on stdin/stdout (blocking).

    Reads requests line-by-line from stdin, dispatches each through the
    server on the given (not-running) event loop, writes one response line
    per request with an id to stdout. JSON-RPC notifications (no id) get no
    response. Exits on EOF (client closed stdin).
    """
    _force_stderr_logging()
    logger.info("Serving MCP over stdio (ctrl+c or EOF to stop)")

    for raw in sys.stdin:
        _trace("stdin recv: " + repr(raw[:120]))
        line = raw.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            sys.stdout.write(_serialize({
                'jsonrpc': '2.0', 'id': None,
                'error': {'code': -32700, 'message': f'Parse error: {e}'}}))
            sys.stdout.flush()
            continue

        has_id = request.get('id') is not None

        try:
            result = loop.run_until_complete(server.handle_request(request))
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.exception("handle_request failed")
            result = {'error': {'code': -32603, 'message': str(e)}}

        if has_id:
            response = _jsonrpc_wrap(request, result)
            _trace("stdout write: " + repr(_serialize(response)[:120]))
            sys.stdout.write(_serialize(response))
            sys.stdout.flush()

    logger.info("stdio client disconnected (EOF)")


async def _handle_tcp_client(server, reader: asyncio.StreamReader,
                             writer: asyncio.StreamWriter) -> None:
    peer = writer.get_extra_info('peername')
    logger.info("TCP client connected: %s", peer)
    try:
        while True:
            line = await reader.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except json.JSONDecodeError as e:
                await _send(writer, {'jsonrpc': '2.0', 'id': None,
                                     'error': {'code': -32700, 'message': f'Parse error: {e}'}})
                continue

            has_id = request.get('id') is not None
            try:
                result = await server.handle_request(request)
            except Exception as e:
                logger.exception("handle_request failed")
                result = {'error': {'code': -32603, 'message': str(e)}}
            if has_id:
                await _send(writer, _jsonrpc_wrap(request, result))
    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        logger.info("TCP client disconnected: %s", peer)


async def _send(writer: asyncio.StreamWriter, obj: dict) -> None:
    try:
        writer.write(_serialize(obj).encode('utf-8'))
        await writer.drain()
    except (ConnectionResetError, BrokenPipeError, RuntimeError):
        pass


async def serve_tcp(server, host: str = '127.0.0.1', port: int = 9891) -> None:
    """Serve MCP over TCP (newline-delimited JSON-RPC per connection)."""
    tcp_server = await asyncio.start_server(
        lambda r, w: _handle_tcp_client(server, r, w), host, port)
    addrs = ', '.join(str(s.getsockname()) for s in tcp_server.sockets or [])
    logger.info("Serving MCP over TCP on %s", addrs)
    async with tcp_server:
        await tcp_server.serve_forever()
