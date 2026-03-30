@echo off
chcp 65001 >nul
title AutoVideoCraft - AI Video Generator

echo.
echo  ============================================
echo   AutoVideoCraft - AI Short Video Generator
echo  ============================================
echo.

:: Check Python version
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: Check Python version is 3.9+
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [INFO] Python version: %PYVER%

:: Create and activate virtual environment if not exists
if not exist ".venv" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
)

echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat

:: Install/update dependencies
echo [INFO] Installing dependencies (this may take a few minutes on first run)...
pip install -r requirements.txt -q --disable-pip-version-check

:: Create required directories
if not exist "outputs" mkdir outputs
if not exist "temp" mkdir temp

:: Launch the app
echo.
echo [INFO] Starting AutoVideoCraft Web UI...
echo [INFO] Open your browser at: http://127.0.0.1:7860
echo [INFO] Press Ctrl+C to stop the server
echo.

python -m autovideocraft.app

pause
