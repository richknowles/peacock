#!/bin/bash
# 🦚 PEACOCK INSTALLATION SCRIPT — macOS Edition — v1.1.2
# Built by Rich Knowles

set -e

echo "🦚 Installing Peacock MCP Server v1.1.2 for macOS..."

# Python 3 check
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Install it from https://python.org or via Homebrew: brew install python"
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

# Make server executable
chmod +x peacock_server.py

PYTHON_PATH="$(pwd)/.venv/bin/python3"
SERVER_PATH="$(pwd)/peacock_server.py"

# Suggest enabling Safari WebDriver (one-time, needs password)
echo ""
echo "⚠️  To enable Safari browser control, run once:"
echo "   sudo safaridriver --enable"

echo ""
echo "🎉 Peacock v1.1.2 installed on macOS!"
echo ""
echo "📝 Add this to ~/Library/Application Support/Claude/claude_desktop_config.json:"
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
echo "🌐 Chrome: Peacock attaches to your running Chrome — no setup needed."
echo "🦊 Firefox: drivers auto-downloaded via webdriver-manager."
echo "🧭 Safari: sudo safaridriver --enable (one-time)."
echo "🖥️  VM control: .venv/bin/pip install proxmoxer requests vncdotool"
echo ""
echo "🦚 Watch it drive."
