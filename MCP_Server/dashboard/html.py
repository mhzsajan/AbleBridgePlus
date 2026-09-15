"""
HTML Templates for AbleBridgePlus Dashboard.
"""


def get_dashboard_html() -> str:
    """Get the main dashboard HTML."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AbleBridgePlus Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background-color: #1a1a1a;
            color: #e0e0e0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: #00d4ff;
            margin-bottom: 20px;
            font-size: 2.5em;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background-color: #2a2a2a;
            border-radius: 10px;
            padding: 20px;
            border: 1px solid #3a3a3a;
        }
        .status-card h3 {
            color: #00d4ff;
            margin-bottom: 10px;
        }
        .status-card.connected {
            border-color: #00ff88;
        }
        .status-card.disconnected {
            border-color: #ff4444;
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .status-indicator.connected {
            background-color: #00ff88;
        }
        .status-indicator.disconnected {
            background-color: #ff4444;
        }
        .tools-section {
            background-color: #2a2a2a;
            border-radius: 10px;
            padding: 20px;
            border: 1px solid #3a3a3a;
        }
        .tools-section h2 {
            color: #00d4ff;
            margin-bottom: 20px;
        }
        .tool-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 10px;
        }
        .tool-item {
            background-color: #3a3a3a;
            border-radius: 5px;
            padding: 10px;
        }
        .tool-item strong {
            color: #00d4ff;
        }
        .refresh-btn {
            background-color: #00d4ff;
            color: #1a1a1a;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .refresh-btn:hover {
            background-color: #00b8d4;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>AbleBridgePlus Dashboard</h1>
        
        <button class="refresh-btn" onclick="refreshData()">Refresh</button>
        
        <div class="status-grid">
            <div class="status-card" id="ableton-status">
                <h3>Ableton</h3>
                <p><span class="status-indicator disconnected"></span>Disconnected</p>
            </div>
            <div class="status-card" id="m4l-status">
                <h3>M4L Bridge</h3>
                <p><span class="status-indicator disconnected"></span>Disconnected</p>
            </div>
            <div class="status-card">
                <h3>Tools</h3>
                <p id="tool-count">0</p>
            </div>
        </div>
        
        <div class="tools-section">
            <h2>Available Tools</h2>
            <div class="tool-list" id="tool-list">
                Loading...
            </div>
        </div>
    </div>
    
    <script>
        async function refreshData() {
            try {
                // Load status
                const statusResponse = await fetch('/api/status');
                const statusData = await statusResponse.json();
                
                // Update Ableton status
                const abletonStatus = document.getElementById('ableton-status');
                if (statusData.ableton_connected) {
                    abletonStatus.className = 'status-card connected';
                    abletonStatus.innerHTML = '<h3>Ableton</h3><p><span class="status-indicator connected"></span>Connected</p>';
                } else {
                    abletonStatus.className = 'status-card disconnected';
                    abletonStatus.innerHTML = '<h3>Ableton</h3><p><span class="status-indicator disconnected"></span>Disconnected</p>';
                }
                
                // Update M4L status
                const m4lStatus = document.getElementById('m4l-status');
                if (statusData.m4l_connected) {
                    m4lStatus.className = 'status-card connected';
                    m4lStatus.innerHTML = '<h3>M4L Bridge</h3><p><span class="status-indicator connected"></span>Connected</p>';
                } else {
                    m4lStatus.className = 'status-card disconnected';
                    m4lStatus.innerHTML = '<h3>M4L Bridge</h3><p><span class="status-indicator disconnected"></span>Disconnected</p>';
                }
                
                // Update tool count
                document.getElementById('tool-count').textContent = statusData.tool_count;
                
                // Load tools
                const toolsResponse = await fetch('/api/tools');
                const toolsData = await toolsResponse.json();
                
                const toolList = document.getElementById('tool-list');
                if (toolsData.tools && toolsData.tools.length > 0) {
                    toolList.innerHTML = toolsData.tools.map(tool => 
                        `<div class="tool-item"><strong>${tool.name}</strong>: ${tool.description}</div>`
                    ).join('');
                } else {
                    toolList.innerHTML = 'No tools available';
                }
            } catch (error) {
                console.error('Error refreshing data:', error);
            }
        }
        
        // Initial load
        refreshData();
        
        // Auto-refresh every 5 seconds
        setInterval(refreshData, 5000);
    </script>
</body>
</html>
"""
