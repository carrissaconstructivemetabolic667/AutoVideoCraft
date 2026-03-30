#!/usr/bin/env bash
set -e

echo ""
echo " ============================================"
echo "  AutoVideoCraft - AI Short Video Generator"
echo " ============================================"
echo ""

# Check Python 3.9+
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 not found. Please install Python 3.9+"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  Run: brew install python"
    else
        echo "  Run: sudo apt install python3 python3-pip python3-venv"
    fi
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[INFO] Python version: $PYTHON_VERSION"

MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 9 ]; }; then
    echo "[ERROR] Python 3.9+ is required. Found: $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment if not exists
if [ ! -d ".venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv .venv
fi

echo "[INFO] Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "[INFO] Installing dependencies (first run may take a few minutes)..."
pip install -r requirements.txt -q --disable-pip-version-check

# Create required directories
mkdir -p outputs temp

# Launch the app
echo ""
echo "[INFO] Starting AutoVideoCraft Web UI..."
echo "[INFO] Open your browser at: http://127.0.0.1:7860"
echo "[INFO] Press Ctrl+C to stop the server"
echo ""

python -m autovideocraft.app
