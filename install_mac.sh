#!/bin/bash
# 🦚 PEACOCK INSTALLATION SCRIPT - macOS Edition 🦚
# Built by Rich Knowles

set -e

echo "🦚 Installing Peacock MCP Server for macOS..."

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Install it from https://python.org"
    exit 1
fi
echo "✅ Python 3 found: $(python3 --version)"

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

echo ""
echo "🎉 Peacock installed successfully!"
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
echo "2. Restart Claude Desktop"
echo "3. Watch Me DRIVE! 🦚"
echo ""
