"""
M4L Bridge UDP/OSC Connection for Enhanced AbletonBridge MCP Server.
"""

import asyncio
import json
import logging
import socket
from typing import Any, Dict, Optional

from MCP_Server.constants import (
    LOCALHOST, M4L_OSC_IN_PORT, M4L_OSC_OUT_PORT,
    UDP_TIMEOUT
)

logger = logging.getLogger('MCP_Server.connections.m4l')


class M4LConnection:
    """UDP/OSC connection to M4L Bridge."""
    
    def __init__(self, host: str = LOCALHOST, in_port: int = M4L_OSC_IN_PORT, out_port: int = M4L_OSC_OUT_PORT):
        """
        Initialize the M4L connection.
        
        Args:
            host: Hostname or IP address
            in_port: UDP port for receiving
            out_port: UDP port for sending
        """
        self.host = host
        self.in_port = in_port
        self.out_port = out_port
        self._in_socket: Optional[socket.socket] = None
        self._out_socket: Optional[socket.socket] = None
        self._connected = False
        self._listening = False
    
    async def connect(self):
        """Connect to M4L Bridge."""
        try:
            # Create input socket for receiving
            self._in_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._in_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._in_socket.bind((self.host, self.in_port))
            self._in_socket.settimeout(UDP_TIMEOUT)
            
            # Create output socket for sending
            self._out_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            self._connected = True
            logger.info(f"Connected to M4L Bridge at {self.host}:{self.out_port}")
        except Exception as e:
            self._connected = False
            logger.error(f"Failed to connect to M4L Bridge: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from M4L Bridge."""
        if self._in_socket:
            try:
                self._in_socket.close()
            except Exception as e:
                logger.error(f"Error closing input socket: {e}")
            finally:
                self._in_socket = None
        
        if self._out_socket:
            try:
                self._out_socket.close()
            except Exception as e:
                logger.error(f"Error closing output socket: {e}")
            finally:
                self._out_socket = None
        
        self._connected = False
        logger.info("Disconnected from M4L Bridge")
    
    async def send_osc(self, address: str, *args):
        """
        Send an OSC message.
        
        Args:
            address: OSC address
            *args: OSC arguments
        """
        if not self._connected or not self._out_socket:
            raise ConnectionError("Not connected to M4L Bridge")
        
        try:
            # Simple OSC message encoding
            # This is a simplified version - real implementation would use proper OSC encoding
            message = {
                'address': address,
                'args': list(args)
            }
            message_json = json.dumps(message)
            message_bytes = message_json.encode('utf-8')
            
            self._out_socket.sendto(message_bytes, (self.host, self.out_port))
            logger.debug(f"Sent OSC message to {address}")
        except Exception as e:
            logger.error(f"Error sending OSC message: {e}")
            raise
    
    async def receive_osc(self) -> Optional[Dict[str, Any]]:
        """
        Receive an OSC message.
        
        Returns:
            Received message or None if timeout
        """
        if not self._connected or not self._in_socket:
            raise ConnectionError("Not connected to M4L Bridge")
        
        try:
            data, addr = self._in_socket.recvfrom(4096)
            message = json.loads(data.decode('utf-8'))
            logger.debug(f"Received OSC message from {addr}")
            return message
        except socket.timeout:
            return None
        except Exception as e:
            logger.error(f"Error receiving OSC message: {e}")
            raise
    
    async def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a command to M4L Bridge and receive response.
        
        Args:
            command: Command dictionary
            
        Returns:
            Response dictionary
        """
        # Send command via OSC
        await self.send_osc('/command', json.dumps(command))
        
        # Receive response
        response = await self.receive_osc()
        if response and 'args' in response and len(response['args']) > 0:
            return json.loads(response['args'][0])
        
        raise ConnectionError("No response from M4L Bridge")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to M4L Bridge."""
        return self._connected
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
