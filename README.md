# 🦚 PEACOCK MCP SERVER 🦚


## What is Peacock?

Peacock is a custom Model Context Protocol (MCP) server that gives Claude Desktop full filesystem access and command execution capabilities on your Linux system.

**Why "Peacock"?**  
Because the AI wants to show off! 🦚 --wait what???

---

## Features

- ✅ **Read/Write Files** - Full filesystem access
- ✅ **Execute Commands** - Run bash commands directly
- ✅ **Directory Listings** - Browse your filesystem
- ✅ **File Search** - Find files with glob patterns
- ✅ **File Info** - Get detailed file metadata
- ✅ **Security** - Restricted to home directory by default

---

## Installation

### Quick Start

```bash
cd peacock
./install.sh
```

### Manual Installation

```bash
# Install dependencies
pip3 install --break-system-packages fastmcp

# Make executable
chmod +x peacock_server.py
```

---

## Configuration

Add this to `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "peacock": {
      "command": "python3",
      "args": [
        "/full/path/to/peacock/peacock_server.py"
      ]
    }
  }
}
```

**Replace `/full/path/to/peacock/` with the actual path!**

---

## Available Tools

### `read_file(path)`
Read the contents of a file.

**Example:** `read_file("/home/rich/.bashrc")`

### `write_file(path, content, mode="w")`
Write content to a file.

**Example:** `write_file("/home/rich/test.txt", "Hello World!")`

### `list_directory(path=".", show_hidden=False)`
List contents of a directory.

**Example:** `list_directory("/home/rich", show_hidden=True)`

### `execute_command(command, cwd=None)`
Execute a shell command.

**Example:** `execute_command("ls -la", cwd="/home/rich")`

### `search_files(pattern, directory=".", max_results=50)`
Search for files matching a pattern.

**Example:** `search_files("*.py", directory="/home/rich")`

### `get_file_info(path)`
Get detailed information about a file.

**Example:** `get_file_info("/home/rich/.bashrc")`

---

## Security

- **Default restriction:** All operations are restricted to the user's home directory
- **Command timeout:** 30 seconds maximum execution time
- **No root access:** Runs as your user, not as root

To change the base directory, edit `BASE_DIR` in `peacock_server.py`.

---

## Testing

Test the server manually:

```bash
python3 peacock_server.py
```

You should see:
```
🦚 PEACOCK MCP SERVER 🦚
📁 Base directory: /home/directory
🚀 Starting server...
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'mcp'"

Run: `pip3 install --break-system-packages fastmcp`

### "Permission denied"

Make sure the script is executable: `chmod +x peacock_server.py`

### Claude Desktop doesn't see Peacock

1. Check the config file syntax (must be valid JSON)
2. Restart Claude Desktop completely
3. Check Claude Desktop logs: `~/.config/Claude/logs/`

---

## Portfolio Use

This project demonstrates:
- **MCP Protocol** implementation
- **Python** async programming
- **System Integration** between AI and Linux
- **Security** best practices
- **Documentation** skills

Perfect for resume/portfolio inclusion!

---

## Credits

**Built by:**
- Rich Knowles

**Built for:**
- Anna (the mission 🇺🇦💜)
- Emmett (the future 🎮)
- The job search (USDM here we come!)

---

## License

MIT License
