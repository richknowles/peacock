#!/bin/bash
# 🦚 PEACOCK TEST SCRIPT 🦚
# Quick test to verify installation

echo "🦚 Testing Peacock MCP Server..."
echo ""

# Test 1: Check if peacock_server.py exists
echo "Test 1: Checking if peacock_server.py exists..."
if [ -f "peacock_server.py" ]; then
    echo "✅ peacock_server.py found"
else
    echo "❌ peacock_server.py not found"
    exit 1
fi

# Test 2: Check if Python 3 is available
echo ""
echo "Test 2: Checking Python 3..."
if command -v python3 &> /dev/null; then
    echo "✅ Python 3 found: $(python3 --version)"
else
    echo "❌ Python 3 not found"
    exit 1
fi

# Test 3: Check if fastmcp is installed
echo ""
echo "Test 3: Checking fastmcp installation..."
if python3 -c "import mcp.server.fastmcp" 2>/dev/null; then
    echo "✅ fastmcp is installed"
else
    echo "❌ fastmcp not installed"
    echo "   Run: pip3 install --break-system-packages fastmcp"
    exit 1
fi

# Test 4: Syntax check
echo ""
echo "Test 4: Checking Python syntax..."
if python3 -m py_compile peacock_server.py 2>/dev/null; then
    echo "✅ Python syntax is valid"
else
    echo "❌ Python syntax error"
    exit 1
fi

echo ""
echo "🎉 All tests passed!"
echo ""
echo "Next steps:"
echo "1. Configure Claude Desktop (see README.md)"
echo "2. Restart Claude Desktop"
echo "3. Watch Claude Strut! 🦚 🚘"
