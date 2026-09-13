"""
Web Dashboard Server for Enhanced AbletonBridge MCP Server.
"""

import asyncio
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, Optional
import threading

from MCP_Server.constants import WEB_DASHBOARD_PORT, LOCALHOST

logger = logging.getLogger('MCP_Server.dashboard')


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for dashboard."""
    
    def __init__(self, *args, dashboard_server=None, **kwargs):
        self.dashboard_server = dashboard_server
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/':
            self._serve_dashboard()
        elif self.path == '/api/status':
            self._serve_status()
        elif self.path == '/api/tools':
            self._serve_tools()
        else:
            self._send_404()
    
    def _serve_dashboard(self):
        """Serve the main dashboard page."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced AbletonBridge Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .status { margin: 20px 0; padding: 10px; border: 1px solid #ccc; }
        .connected { background-color: #d4edda; }
        .disconnected { background-color: #f8d7da; }
        .tools { margin-top: 20px; }
        .tool { padding: 5px; border-bottom: 1px solid #eee; }
    </style>
</head>
<body>
    <h1>Enhanced AbletonBridge Dashboard</h1>
    <div class="status" id="status">Loading...</div>
    <div class="tools">
        <h2>Available Tools</h2>
        <div id="tools">Loading...</div>
    </div>
    <script>
        async function loadStatus() {
            const response = await fetch('/api/status');
            const data = await response.json();
            const statusDiv = document.getElementById('status');
            if (data.ableton_connected) {
                statusDiv.className = 'status connected';
                statusDiv.innerHTML = '✓ Connected to Ableton';
            } else {
                statusDiv.className = 'status disconnected';
                statusDiv.innerHTML = '✗ Disconnected from Ableton';
            }
        }
        async function loadTools() {
            const response = await fetch('/api/tools');
            const data = await response.json();
            const toolsDiv = document.getElementById('tools');
            toolsDiv.innerHTML = data.tools.map(tool => 
                `<div class="tool"><strong>${tool.name}</strong>: ${tool.description}</div>`
            ).join('');
        }
        loadStatus();
        loadTools();
    </script>
</body>
</html>
"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def _serve_status(self):
        """Serve the status API."""
        status = {
            'ableton_connected': self.dashboard_server.ableton_connected if self.dashboard_server else False,
            'm4l_connected': self.dashboard_server.m4l_connected if self.dashboard_server else False,
            'tool_count': self.dashboard_server.tool_count if self.dashboard_server else 0
        }
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(status).encode())
    
    def _serve_tools(self):
        """Serve the tools API."""
        tools = self.dashboard_server.get_tools() if self.dashboard_server else []
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'tools': tools}).encode())
    
    def _send_404(self):
        """Send 404 response."""
        self.send_response(404)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        """Log HTTP requests."""
        logger.debug(f"HTTP {args[0]}")


class DashboardServer:
    """Web dashboard server for monitoring."""
    
    def __init__(self, port: int = WEB_DASHBOARD_PORT, host: str = LOCALHOST):
        """
        Initialize the dashboard server.
        
        Args:
            port: Port to listen on
            host: Host to bind to
        """
        self.port = port
        self.host = host
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        
        # State references (set by MCP server)
        self.ableton_connected = False
        self.m4l_connected = False
        self.tool_count = 0
        self._tools_func = None
    
    def set_tools_func(self, tools_func):
        """Set the function to get tools list."""
        self._tools_func = tools_func
    
    def get_tools(self):
        """Get the tools list."""
        if self._tools_func:
            return self._tools_func()
        return []
    
    def start(self):
        """Start the dashboard server."""
        if self._running:
            return
        
        # Create handler with reference to this server
        def handler(*args, **kwargs):
            DashboardHandler(*args, dashboard_server=self, **kwargs)
        
        self._server = HTTPServer((self.host, self.port), handler)
        self._running = True
        
        # Run in separate thread
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        
        logger.info(f"Dashboard server started at http://{self.host}:{self.port}")
    
    def stop(self):
        """Stop the dashboard server."""
        if self._server:
            self._server.shutdown()
            self._server = None
        self._running = False
        logger.info("Dashboard server stopped")
    
    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running
