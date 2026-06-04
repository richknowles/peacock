<p align="center">
  <img src="peacock-logo-anim.apng" alt="Peacock Logo" width="300"/>
</p>

<h1 align="center">🦚 PEACOCK MCP SERVER 🦚</h1>

<p align="center">
  <strong>v1.1.1</strong> &nbsp;·&nbsp; Built by Rich Knowles &nbsp;·&nbsp; MIT License
</p>

---

## What is Peacock?

Peacock is a custom Model Context Protocol (MCP) server that gives Claude Desktop **full filesystem access and command execution** capabilities on your system.

> ⚡️ **One of the first!** This was one of the earliest Linux MCP servers for Claude Desktop to hit the scene!

**The big note** is as big as I can get it!

**Do not use this** if you don't know what you are doing or, at the very least, do not know how to recover from installing this or breaking your system with this. Do **NOT** break your wife's computer with this. Do not break anyone's computer with this. I will be happy to respond to any and all questions.

**I am not responsible** for any chaos or dark magic that ensues. The world must understand that you have to take security seriously when operating any computer. That being said, some people should not be given the keys to a toaster! Nor should they be given other destructive things like hand-grenades, computers or artificial intelligence.

**Why "Peacock"?**
Because the AI wants to show off! 🦚

---

## Installation

Clone the repo, then run the installer for your platform. The script creates a virtual environment, installs all dependencies, and prints the exact config block to paste into Claude Desktop.

### 🍎 macOS (Sonoma +)

```bash
git clone https://github.com/richknowles/peacock
cd peacock
./install_mac.sh
```

### 🐧 Linux

```bash
git clone https://github.com/richknowles/peacock
cd peacock
./install.sh
```

### 🥪 Super Peacock (dualboot OC Sonoma + madOS)

```bash
git clone https://github.com/richknowles/peacock
cd peacock
./install.sh
```

---

## Features

- ✅ **Read/Write Files** — Full filesystem access
- ✅ **Execute Commands** — Run shell commands directly
- ✅ **Directory Listings** — Browse your filesystem
- ✅ **File Search** — Find files with glob patterns
- ✅ **File Info** — Get detailed file metadata
- ✅ **Security** — Restricted to home directory; hardened against injection and traversal

---

## Configuration

The install script prints the exact config block to copy — it looks like this (with your real paths filled in):

```json
{
  "mcpServers": {
    "peacock": {
      "command": "/path/to/peacock/.venv/bin/python3",
      "args": ["/path/to/peacock/peacock_server.py"]
    }
  }
}
```

**macOS:** paste into `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux:** paste into `~/.config/Claude/claude_desktop_config.json`

Then restart Claude Desktop.

---

## Available Tools

### `read_file(path)`
Read the contents of a file.

**Example:** `read_file("/home/rich/.bashrc")` (Linux)
**Example:** `read_file("/Users/rich/.bashrc")` (macOS)

### `write_file(path, content, mode="w")`
Write content to a file. `mode` must be `"w"` (overwrite) or `"a"` (append).

**Example:** `write_file("/home/rich/test.txt", "Hello World!")`

### `list_directory(path=".", show_hidden=False)`
List contents of a directory.

**Example:** `list_directory("/home/rich", show_hidden=True)`

### `execute_command(command, cwd=None)`
Execute a shell command. Commands are parsed with `shlex` — shell metacharacters are **not** interpreted.

**Example:** `execute_command("ls -la", cwd="/home/rich")`

### `search_files(pattern, directory=".", max_results=50)`
Search for files matching a glob pattern. Only safe characters are allowed in patterns.

**Example:** `search_files("*.py", directory="/home/rich")`

### `get_file_info(path)`
Get detailed information about a file.

**Example:** `get_file_info("/home/rich/.bashrc")`

---

## Security

Peacock v1.1.0 ships with a hardened security layer. All fixes were applied after a full vulnerability audit.

| # | Finding | Severity | Fix |
|---|---------|----------|-----|
| 1 | Path traversal via string comparison | HIGH | Replaced `.startswith()` with `relative_to()` which raises on any escape |
| 2 | Symlink escape via unresolved BASE_DIR | HIGH | `BASE_DIR` now resolved at startup with `.resolve()` |
| 3 | Command injection via `shell=True` | CRITICAL | Switched to `shlex.split()` + `shell=False` |
| 4 | TOCTOU race in `write_file` mkdir | MEDIUM | Path re-verified after `mkdir` to catch symlink swaps |
| 5 | Unvalidated glob patterns (DoS) | MEDIUM | Allowlist regex + limit on `**` depth |
| 6 | No rate limiting | MEDIUM | Token bucket: 30 calls / 10 s per tool |
| 7 | Unvalidated `mode` parameter | LOW-MEDIUM | Strict allowlist: only `"w"` or `"a"` accepted |
| 8 | Error message info disclosure | LOW | Home path redacted from all exception messages |

**Remaining baseline posture:**
- All operations are restricted to the user's home directory
- Command timeout: 30 seconds maximum
- Runs as your user, never root

To change the base directory, edit `BASE_DIR` in `peacock_server.py`.

---

## Testing

```bash
.venv/bin/python3 peacock_server.py
```

You should see:
```
🦚 PEACOCK MCP SERVER v1.1.1 🦚
Built by Rich Knowles
📁 Base directory: /your/home/directory
🚀 Starting server...
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'mcp'`

The install script sets up the virtual environment automatically. If you hit this, re-run the installer:
```bash
./install_mac.sh   # macOS
./install.sh       # Linux
```

### `Permission denied`

Make sure the script is executable: `chmod +x peacock_server.py`

### Claude Desktop doesn't see Peacock

1. Check the config file syntax (must be valid JSON)
2. Restart Claude Desktop completely
3. Check Claude Desktop logs: `~/.config/Claude/logs/`

---

## Regenerate the Animated Logo

The animation is generated by `make_logo_anim.py` — run it any time to recreate `peacock-logo-anim.apng` from the source PNG:

```bash
.venv/bin/pip install Pillow numpy   # one-time setup
.venv/bin/python3 make_logo_anim.py
```

---

## Portfolio Use

This project demonstrates:
- **MCP Protocol** implementation
- **Agentic AI** is possible and can simultaneously be made to be secure
- **Python** programming
- **System Integration** between AI and macOS/Linux
- **Security** best practices — full audit + hardening
- **Documentation** skills
- **Cross-platform** support

---

## Credits

**Built by:** Rich Knowles

---

## About the Name & Logo

The name **Peacock** was chosen because... it makes sense and who doesn't love a good peacock? 🦚

The logo was designed to represent elegance and beauty...
> while taking pride and humility in the accomplishment.

---

## License

MIT License
