#!/bin/bash
# 🦚 PEACOCK INSTALLATION SCRIPT — Linux / macOS — v1.1.2
# Built by Rich Knowles

set -e

PLATFORM="$(uname -s)"

if [ "$PLATFORM" = "Darwin" ]; then
    echo "🍎 macOS detected — using macOS installer"
    exec "$(dirname "$0")/install_mac.sh"
fi

echo "🦚 Installing Peacock MCP Server v1.1.2 for Linux..."

# Python 3 check
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Install: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi
echo "✅ Python 3: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv
echo "✅ Virtual environment created"

# Install dependencies into venv
echo "📦 Installing dependencies..."
.venv/bin/pip install -q -r requirements.txt
echo "✅ Dependencies installed"

# Detect browsers
if ! command -v google-chrome &> /dev/null && ! command -v chromium &> /dev/null && ! command -v chromium-browser &> /dev/null; then
    echo ""
    echo "⚠️  Chrome/Chromium not detected. Install one:"
    echo "   Debian/Ubuntu: sudo apt install chromium-browser"
    echo "   Arch:          sudo pacman -S chromium"
    echo "   Fedora:        sudo dnf install chromium"
fi

if ! command -v firefox &> /dev/null; then
    echo ""
    echo "⚠️  Firefox not detected:"
    echo "   Debian/Ubuntu: sudo apt install firefox"
    echo "   Arch:          sudo pacman -S firefox"
fi

chmod +x peacock_server.py

PYTHON_PATH="$(pwd)/.venv/bin/python3"
SERVER_PATH="$(pwd)/peacock_server.py"

echo ""
echo "🎉 Peacock v1.1.2 installed!"
echo ""
echo "📝 Add this to ~/.config/Claude/claude_desktop_config.json:"
echo ""
echo "  \"mcpServers\": {"
echo "    \"peacock\": {"
echo "      \"command\": \"$PYTHON_PATH\","
echo "      \"args\": [\"$SERVER_PATH\"]"
echo "    }"
echo "  }"
echo ""
echo "Then restart Claude Desktop."
echo ""
echo "🖥️  VM control: .venv/bin/pip install proxmoxer requests vncdotool"
echo "🦚 Watch it drive."
