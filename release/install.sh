#!/bin/bash

echo "========================================"
echo "AbleBridgePlus Installer v0.3.0"
echo "========================================"
echo ""
echo "MCP bridge for Ableton Live - 417 tools"
echo "https://github.com/mhzsajan/AbleBridgePlus"
echo ""

# Check for Python
echo "Checking for Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found!"
    echo "Please install Python 3.10+ from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Check for uv
echo ""
echo "Checking for uv package manager..."
if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing uv..."
    pip3 install uv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install uv"
        echo "Please install uv manually: pip3 install uv"
        exit 1
    fi
fi

echo "Found uv"
echo ""

# Set installation directory
INSTALL_DIR="$HOME/ablebridge"
echo "Installation directory: $INSTALL_DIR"
echo ""

# Create installation directory
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Creating installation directory..."
    mkdir -p "$INSTALL_DIR"
fi

# Copy files
echo "Copying files..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cp -r "$SCRIPT_DIR/.."/* "$INSTALL_DIR/"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to copy files"
    exit 1
fi

echo "Files copied successfully!"
echo ""

# Install dependencies
echo "Installing dependencies..."
cd "$INSTALL_DIR"
uv sync
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo "Dependencies installed!"
echo ""

# Copy Remote Script to Ableton
echo ""
echo "Setting up Ableton Remote Script..."

# macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    ABLETON_DIR="$HOME/Music/Ableton/User Library/Remote Scripts"
# Linux
else
    ABLETON_DIR="$HOME/.ableton/User Library/Remote Scripts"
fi

if [ ! -d "$ABLETON_DIR" ]; then
    echo "Ableton User Library not found at: $ABLETON_DIR"
    echo "Please manually copy AbleBridgePlus to your Remote Scripts folder."
    echo ""
else
    if [ ! -d "$ABLETON_DIR/AbleBridgePlus" ]; then
        mkdir -p "$ABLETON_DIR/AbleBridgePlus"
    fi
    cp -r "$INSTALL_DIR/AbleBridgePlus"/* "$ABLETON_DIR/AbleBridgePlus/"
    echo "Remote Script installed to: $ABLETON_DIR/AbleBridgePlus"
fi

echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Open Ableton Live"
echo "2. Go to Preferences -> Link, Tempo & MIDI"
echo "3. Under 'Control Surface', select 'AbleBridgePlus'"
echo "4. Set Input and Output to 'AbleBridgePlus'"
echo ""
echo "To start the MCP Server:"
echo "   cd $INSTALL_DIR"
echo "   uv run python -m MCP_Server.server"
echo ""
echo "For more information, see README.md and CHANGELOG.md"
echo ""