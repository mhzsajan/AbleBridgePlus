@echo off
setlocal enabledelayedexpansion

echo ========================================
echo AbleBridge++ Installer v0.3.0
echo ========================================
echo.
echo Based on AbletonBridge by hidingwill
echo https://github.com/mhzsajan/enhanced-abletonbridge
echo.

REM Check for Python
echo Checking for Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
echo Found Python %PYTHON_VERSION%

REM Check for uv
echo.
echo Checking for uv package manager...
uv --version >nul 2>&1
if errorlevel 1 (
    echo uv not found. Installing uv...
    pip install uv
    if errorlevel 1 (
        echo ERROR: Failed to install uv
        echo Please install uv manually: pip install uv
        pause
        exit /b 1
    )
)

echo Found uv
echo.

REM Set installation directory
set INSTALL_DIR=%USERPROFILE%\enhanced-abletonbridge
echo Installation directory: %INSTALL_DIR%
echo.

REM Create installation directory
if not exist "%INSTALL_DIR%" (
    echo Creating installation directory...
    mkdir "%INSTALL_DIR%"
)

REM Copy files
echo Copying files...
xcopy /E /I /Y "%~dp0.." "%INSTALL_DIR%"
if errorlevel 1 (
    echo ERROR: Failed to copy files
    pause
    exit /b 1
)

echo Files copied successfully!
echo.

REM Install dependencies
echo Installing dependencies...
cd /d "%INSTALL_DIR%"
uv sync
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo Dependencies installed!
echo.

REM Copy Remote Script to Ableton
echo.
echo Setting up Ableton Remote Script...
set ABLETON_DIR=%USERPROFILE%\Documents\Ableton\User Library\Remote Scripts
if not exist "%ABLETON_DIR%" (
    echo Ableton User Library not found at: %ABLETON_DIR%
    echo Please manually copy AbletonBridge_Remote_Script to your Remote Scripts folder.
    echo.
) else (
    if not exist "%ABLETON_DIR%\AbletonBridge" (
        mkdir "%ABLETON_DIR%\AbletonBridge"
    )
    xcopy /E /I /Y "%INSTALL_DIR%\AbletonBridge_Remote_Script" "%ABLETON_DIR%\AbletonBridge"
    echo Remote Script installed to: %ABLETON_DIR%\AbletonBridge
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo.
echo 1. Open Ableton Live
echo 2. Go to Preferences → Link, Tempo & MIDI
echo 3. Under "Control Surface", select "AbletonBridge"
echo 4. Set Input and Output to "AbletonBridge"
echo.
echo To start the MCP Server:
echo    cd %INSTALL_DIR%
echo    uv run python -m MCP_Server.server
echo.
echo For more information, see README.md
echo.
pause
