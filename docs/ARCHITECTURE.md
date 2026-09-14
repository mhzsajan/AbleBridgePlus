# Architecture

This document describes the architecture of AbleBridge++.

## System Overview

AbleBridge++ is an AI integration layer for Ableton Live that uses the Model Context Protocol (MCP) to connect AI tools with Ableton's Live Object Model (LOM).

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Tool (Claude, GPT, etc.)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ MCP Protocol
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      MCP Server (Python)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Tools     │  │ Connections │  │   Cache     │         │
│  │  (340+)     │  │  TCP/UDP    │  │  Browser    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Remote Script  │ │   M4L Bridge    │ │  Web Dashboard  │
│  (TCP: 9877)    │ │  (UDP: 9878)    │ │  (HTTP: 9880)   │
└─────────────────┘ └─────────────────┘ └─────────────────┘
              │               │               │
              ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                      Ableton Live                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Tracks    │  │   Devices   │  │   Clips     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. MCP Server

The MCP Server is the main entry point for AI tools. It handles:
- Tool registration and execution
- Connection management
- Response formatting
- Error handling

**Location:** `MCP_Server/`

**Key Files:**
- `server.py` — Main server entry point
- `state.py` — Global state management
- `constants.py` — Configuration constants
- `validation.py` — Input validation

### 2. Tools

Tools are organized by functionality. Each tool is a Python function that can be called by the AI.

**Location:** `MCP_Server/tools/`

**Categories:**
- `tracks.py` — Track management (create, delete, rename, etc.)
- `clips.py` — Clip management (create, edit, fire, etc.)
- `devices.py` — Device management (load, configure, etc.)
- `mixer.py` — Mixer controls (volume, pan, sends, etc.)
- `browser.py` — Browser operations (search, load, etc.)
- `automation.py` — Automation (create, edit, etc.)
- `arrangement.py` — Arrangement view operations
- `creative.py` — Creative tools (generation, transformation)
- `grid.py` — Grid notation (ASCII drum patterns)
- `m4l_tools.py` — M4L-specific tools
- `midi_cc.py` — MIDI CC mapping
- `scenes.py` — Scene management
- `session.py` — Session state
- `snapshots.py` — Device snapshots
- `workflows.py` — Compound workflows

**Enhanced Tools (New):**
- `midi_mapping.py` — MIDI controller mapping
- `plugin_management.py` — Plugin scanning and configuration
- `video_routing.py` — Videosync2 integration
- `setlist_management.py` — AbleSet integration
- `performance.py` — Performance monitoring
- `quick_presets.py` — Live show presets
- `audio_analysis.py` — Audio analysis tools
- `template_system.py` — Template management
- `advanced_routing.py` — Advanced routing
- `ai_integration.py` — AI-specific features

### 3. Connections

Connections handle communication between the MCP Server and Ableton.

**Location:** `MCP_Server/connections/`

**Files:**
- `ableton.py` — TCP connection to Remote Script
- `m4l.py` — UDP/OSC connection to M4L Bridge

### 4. Remote Script

The Remote Script runs inside Ableton as a Control Surface. It handles:
- TCP commands from the MCP Server
- UDP real-time parameter updates
- Live Object Model (LOM) access

**Location:** `AbletonBridge_Remote_Script/`

**Key Files:**
- `__init__.py` — Main Remote Script entry point
- `handlers/` — Command handlers

**Handlers:**
- `tracks.py` — Track operations
- `clips.py` — Clip operations
- `devices.py` — Device operations
- `mixer.py` — Mixer operations
- `browser.py` — Browser operations
- `automation.py` — Automation operations
- `arrangement.py` — Arrangement operations
- `audio.py` — Audio operations
- `midi.py` — MIDI operations
- `scenes.py` — Scene operations
- `session.py` — Session operations

### 5. M4L Bridge

The M4L Bridge is a Max for Live device that provides access to hidden parameters and advanced features.

**Location:** `M4L_Device/`

**Features:**
- Hidden parameter access
- Rack chain internals
- Audio analysis
- Property observation
- AB comparison

### 6. Web Dashboard

The Web Dashboard provides a web interface for monitoring the server.

**Location:** `MCP_Server/dashboard/`

**Files:**
- `html.py` — HTML templates
- `server.py` — HTTP server

## Data Flow

### Tool Execution Flow

1. **AI Tool** calls a tool via MCP
2. **MCP Server** receives the call
3. **MCP Server** validates input
4. **MCP Server** sends command to Remote Script via TCP
5. **Remote Script** executes the command using LOM
6. **Remote Script** returns result
7. **MCP Server** formats response
8. **MCP Server** returns result to AI Tool

### Real-time Parameter Flow

1. **AI Tool** sets a parameter via MCP
2. **MCP Server** receives the call
3. **MCP Server** sends UDP packet to Remote Script
4. **Remote Script** applies parameter change
5. **No response needed** (fire-and-forget)

### M4L Bridge Flow

1. **MCP Server** sends OSC message to M4L Bridge
2. **M4L Bridge** processes the message
3. **M4L Bridge** accesses LOM
4. **M4L Bridge** returns result via OSC
5. **MCP Server** receives result

## Communication Protocols

### TCP (Port 9877)
- Used for: Command/response communication
- Protocol: JSON over TCP
- Features: Reliable, ordered delivery

### UDP (Port 9882)
- Used for: Real-time parameter updates
- Protocol: JSON over UDP
- Features: Fast, fire-and-forget

### UDP/OSC (Ports 9878/9879)
- Used for: M4L Bridge communication
- Protocol: OSC (Open Sound Control)
- Features: Low latency, audio-focused

### HTTP (Port 9880)
- Used for: Web Dashboard
- Protocol: HTTP/HTML
- Features: Browser-accessible

## State Management

### Global State
The MCP Server maintains global state for:
- Connection status
- Session information
- Cache data
- Configuration

### State Files
- `state.py` — Main state management
- `cache/browser.py` — Browser cache

### Persistence
- Browser cache is persisted to disk
- Session state is refreshed on each query
- Configuration is loaded from environment variables

## Error Handling

### Tool Errors
- Tools return standardized error responses
- Errors include error code and message
- Errors are logged for debugging

### Connection Errors
- TCP connection failures trigger reconnection
- UDP packets are fire-and-forget (no error handling)
- M4L Bridge errors are logged

### Validation Errors
- Input validation occurs before execution
- Invalid parameters return helpful error messages
- Validation errors are logged

## Security Considerations

### Local Only
- All communication is local (localhost)
- No external network access required
- No authentication needed

### Port Management
- Ports are fixed (9877, 9878, 9879, 9880, 9882)
- Singleton guard prevents multiple instances
- Ports are released on shutdown

### Data Privacy
- No data is sent to external servers
- All processing is local
- Browser cache is local only

## Performance

### Optimization Techniques
- Chunked responses for large data
- Async tool handlers
- Browser cache for fast startup
- UDP for real-time updates

### Resource Usage
- MCP Server: ~50MB RAM
- Remote Script: ~20MB RAM
- M4L Bridge: ~30MB RAM (when loaded)
- Total: ~100MB RAM

### Latency
- TCP commands: ~10-50ms
- UDP updates: ~1-5ms
- M4L Bridge: ~5-20ms

## Extensibility

### Adding New Tools
1. Create a new file in `MCP_Server/tools/`
2. Define tool functions
3. Register tools in `__init__.py`
4. Add to tool documentation

### Adding New Handlers
1. Create a new file in `AbletonBridge_Remote_Script/handlers/`
2. Define handler functions
3. Register handlers in `__init__.py`
4. Add to handler documentation

### Adding New Connections
1. Create a new file in `MCP_Server/connections/`
2. Define connection class
3. Initialize in `server.py`
4. Add to connection documentation

## Future Architecture

### Planned Enhancements
- Plugin-based tool system
- Dynamic tool loading
- Distributed processing
- Multi-DAW support
- Cloud integration

### Scalability
- Horizontal scaling via multiple MCP servers
- Vertical scaling via async processing
- Load balancing for multiple AI tools
