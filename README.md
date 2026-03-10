<p align="center">
  <img src="https://github.com/richknowles/peacock/blob/ad40be9840e7c8ad08ee47ac512cb067b486a241/peacock-logo-img.png" alt="Peacock Logo" width="400"/>
</p>

<h1 align="center">🦚 PEACOCK MCP SERVER 🦚</h1>

## What is Peacock?

Peacock is a custom Model Context Protocol (MCP) server that gives Claude Desktop full filesystem access and command execution capabilities on your system.

**Why "Peacock"?**  
Because the AI wants to show off! 🦚 --wait what???

---

## Choose Your Own Adventure 🦚

### 🍎 macOS (Sonoma +)

**Known to work with:** macOS Sonoma and later

```bash
cd peacock
./install_mac.sh
```

### 🐧 Linux (CosmicTosh)

**Known to work with:** CosmicTosh (Debian-based custom Linux distro running atop ZFS)


### 🥪 Super Peacock! Hybrid - OpenCore macOS (Sonoma) paired with Archlinux (madOS)

**Currently running dualboot OC Sonoma + madOS which is my forthcoming distribution that will NOT be opinionated!

> ⚡️ **One of the first!** This was one of the earliest Linux MCP servers for Claude Desktop to hit the scene!

```bash
cd peacock
./install.sh
```

---

## Features

- ✅ **Read/Write Files** - Full filesystem access
- ✅ **Execute Commands** - Run bash commands directly
- ✅ **Directory Listings** - Browse your filesystem
- ✅ **File Search** - Find files with glob patterns
- ✅ **File Info** - Get detailed file metadata
- ✅ **Security** - Restricted to home directory by default

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

**Example:** `read_file("/home/rich/.bashrc")` (Linux)  
**Example:** `read_file("/Users/rich/.bashrc")` (macOS)

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

**macOS:** Run: `pip3 install fastmcp`  
**Linux:** Run: `pip3 install --break-system-packages fastmcp`

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
- **Agentic AI** is possible and can simultaneously be made to be secure
- **Python** async programming
- **System Integration** between AI and macOS/Linux
- **Security** best practices
- **Documentation** skills
- **Cross-platform** support

---

## Credits

**Built by:**

- Rich Knowles

**Built for:**

- Emmett (the future 🎮)

---

## About the Name & Logo

The name **Peacock** was chosen because... it makes sense and who doesn't love a good peacock? 🦚

The logo was designed to represent elegance and beauty while taking pride in the accomplishment witn just the right dose of humility. of a - just like how this MCP server lets Claude show off its filesystem powers.

---

## License

MIT License
