#!/bin/bash
# 🦚 PEACOCK INSTALLATION SCRIPT 🦚
# Built by Rich Knowles

echo "🦚 Installing Peacock MCP Server..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install --break-system-packages -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"

# Make the server executable
chmod +x peacock_server.py

echo ""
echo "🎉 Peacock installed successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Add this to ~/.config/Claude/claude_desktop_config.json:"
echo ""
echo '{'
echo '  "mcpServers": {'
echo '    "peacock": {'
echo '      "command": "python3",'
echo '      "args": ['
echo "        \"$(pwd)/peacock_server.py\""
echo '      ]'
echo '    }'
echo '  }'
echo '}'
echo ""
echo "2. Restart Claude Desktop"
echo "3. Watch Me DRIVE! 🦚
