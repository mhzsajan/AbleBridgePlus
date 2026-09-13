"""
Ableton TCP Connection for Enhanced AbletonBridge MCP Server.
"""

import asyncio
import json
import logging
import socket
from typing import Any, Dict, Optional

from MCP_Server.constants import (
    LOCALHOST, ABLETON_TCP_PORT,
    TCP_TIMEOUT, MAX_RECONNECT_ATTEMPTS, RECONNECT_DELAY
)

logger = logging.getLogger('MCP_Server.connections.ableton')


class AbletonConnection:
    """TCP connection to Ableton Remote Script."""
    
    def __init__(self, host: str = LOCALHOST, port: int = ABLETON_TCP_PORT):
        """
        Initialize the Ableton connection.
        
        Args:
            host: Hostname or IP address
            port: TCP port number
        """
        self.host = host
        self.port = port
        self._socket: Optional[socket.socket] = None
        self._connected = False
        self._reconnect_attempts = 0
    
    async def connect(self):
        """Connect to Ableton Remote Script."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(TCP_TIMEOUT)
            self._socket.connect((self.host, self.port))
            self._connected = True
            self._reconnect_attempts = 0
            logger.info(f"Connected to Ableton at {self.host}:{self.port}")
        except Exception as e:
            self._connected = False
            logger.error(f"Failed to connect to Ableton: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Ableton Remote Script."""
        if self._socket:
            try:
                self._socket.close()
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
            finally:
                self._socket = None
                self._connected = False
                logger.info("Disconnected from Ableton")
    
    async def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a command to Ableton and receive response.
        
        Args:
            command: Command dictionary
            
        Returns:
            Response dictionary
        """
        if not self._connected or not self._socket:
            raise ConnectionError("Not connected to Ableton")
        
        try:
            # Serialize command
            command_json = json.dumps(command)
            command_bytes = command_json.encode('utf-8')
            
            # Send command
            self._socket.sendall(command_bytes)
            
            # Receive response
            response_data = b""
            while True:
                chunk = self._socket.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                # Check if we have a complete JSON response
                try:
                    response = json.loads(response_data.decode('utf-8'))
                    return response
                except json.JSONDecodeError:
                    # Continue receiving more data
                    continue
            
            # If we get here, we didn't receive a complete response
            raise ConnectionError("Incomplete response from Ableton")
            
        except socket.timeout:
            logger.error("Timeout waiting for Ableton response")
            raise
        except Exception as e:
            logger.error(f"Error communicating with Ableton: {e}")
            self._connected = False
            raise
    
    async def send_command_with_retry(self, command: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """
        Send a command with retry logic.
        
        Args:
            command: Command dictionary
            max_retries: Maximum number of retries
            
        Returns:
            Response dictionary
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await self.send_command(command)
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    # Try to reconnect
                    try:
                        await self.disconnect()
                        await asyncio.sleep(RECONNECT_DELAY)
                        await self.connect()
                    except Exception as reconnect_error:
                        logger.error(f"Reconnection failed: {reconnect_error}")
        
        raise last_error
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Ableton."""
        return self._connected
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
