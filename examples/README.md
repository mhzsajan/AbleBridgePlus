# Enhanced AbletonBridge Examples

This directory contains example usage of Enhanced AbletonBridge.

## Basic Examples

### Get Session Info
```python
import asyncio
from MCP_Server.server import MCPServer

async def main():
    server = MCPServer()
    await server.start()
    
    # Get session info
    result = await server.handle_request({
        'method': 'tools/call',
        'params': {
            'name': 'get_session_info',
            'arguments': {}
        }
    })
    
    print(result)
    await server.stop()

asyncio.run(main())
```

### Create MIDI Track
```python
import asyncio
from MCP_Server.server import MCPServer

async def main():
    server = MCPServer()
    await server.start()
    
    # Create MIDI track
    result = await server.handle_request({
        'method': 'tools/call',
        'params': {
            'name': 'create_midi_track',
            'arguments': {'index': -1}
        }
    })
    
    print(result)
    await server.stop()

asyncio.run(main())
```

## Live Show Examples

### Load Live Preset
```python
import asyncio
from MCP_Server.server import MCPServer

async def main():
    server = MCPServer()
    await server.start()
    
    # Load live preset
    result = await server.handle_request({
        'method': 'tools/call',
        'params': {
            'name': 'load_live_preset',
            'arguments': {'preset_name': 'Concert'}
        }
    })
    
    print(result)
    await server.stop()

asyncio.run(main())
```

### Set Next Song
```python
import asyncio
from MCP_Server.server import MCPServer

async def main():
    server = MCPServer()
    await server.start()
    
    # Set next song
    result = await server.handle_request({
        'method': 'tools/call',
        'params': {
            'name': 'set_next_song',
            'arguments': {'song_name': 'Kutu Ma Timi'}
        }
    })
    
    print(result)
    await server.stop()

asyncio.run(main())
```

## Video Integration Examples

### Configure Spout
```python
import asyncio
from MCP_Server.server import MCPServer

async def main():
    server = MCPServer()
    await server.start()
    
    # Configure Spout output
    result = await server.handle_request({
        'method': 'tools/call',
        'params': {
            'name': 'configure_spout',
            'arguments': {'enabled': True, 'port': 5000}
        }
    })
    
    print(result)
    await server.stop()

asyncio.run(main())
```

### Get Video Status
```python
import asyncio
from MCP_Server.server import MCPServer

async def main():
    server = MCPServer()
    await server.start()
    
    # Get video status
    result = await server.handle_request({
        'method': 'tools/call',
        'params': {
            'name': 'get_video_status',
            'arguments': {}
        }
    })
    
    print(result)
    await server.stop()

asyncio.run(main())
```

## MIDI Mapping Examples

### Create MIDI Mapping
```python
import asyncio
from MCP_Server.server import MCPServer

async def main():
    server = MCPServer()
    await server.start()
    
    # Create MIDI mapping
    result = await server.handle_request({
        'method': 'tools/call',
        'params': {
            'name': 'create_midi_mapping',
            'arguments': {
                'controller_name': 'Minilab3',
                'channel': 0,
                'cc': 7,
                'track_index': 0,
                'parameter_name': 'Volume',
                'min_value': 0.0,
                'max_value': 1.0
            }
        }
    })
    
    print(result)
    await server.stop()

asyncio.run(main())
```

## Performance Monitoring Examples

### Get CPU Usage
```python
import asyncio
from MCP_Server.server import MCPServer

async def main():
    server = MCPServer()
    await server.start()
    
    # Get CPU usage
    result = await server.handle_request({
        'method': 'tools/call',
        'params': {
            'name': 'get_cpu_usage',
            'arguments': {}
        }
    })
    
    print(result)
    await server.stop()

asyncio.run(main())
```

### Get Memory Usage
```python
import asyncio
from MCP_Server.server import MCPServer

async def main():
    server = MCPServer()
    await server.start()
    
    # Get memory usage
    result = await server.handle_request({
        'method': 'tools/call',
        'params': {
            'name': 'get_memory_usage',
            'arguments': {}
        }
    })
    
    print(result)
    await server.stop()

asyncio.run(main())
```
