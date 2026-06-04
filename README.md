<p align="center">
  <img src="peacock-logo-anim.apng" alt="Peacock Logo" width="300"/>
</p>

<h1 align="center">🦚 PEACOCK MCP SERVER 🦚</h1>

<p align="center">
  <strong>v1.1.0</strong> &nbsp;·&nbsp; Built by Rich Knowles &nbsp;·&nbsp; MIT License
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

## Choose Your Own Adventure 🦚

### 🍎 macOS (Sonoma +)

**Known to work with:** macOS Sonoma and later

```bash
cd peacock
./install_mac.sh
```

### 🐧 Linux (CosmicTosh)

**Known to work with:** CosmicTosh (Debian-based custom Linux distro running atop ZFS)

```bash
cd peacock
./install.sh
```

### 🥪 Super Peacock!

> 🎲 **Hybrid** — OpenCore macOS (Sonoma) paired with Archlinux (madOS)

Currently running dualboot OC Sonoma + madOS which is my forthcoming distribution that will NOT be opinionated!

```bash
cd peacock
./install.sh
```

### 🐍 Recommended: Virtual Environment Install (any platform)

```bash
cd peacock
python3 -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

Then point your Claude Desktop config at `.venv/bin/python3` instead of the system `python3`.

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

For venv installs, use the venv interpreter instead:
```json
"command": "/full/path/to/peacock/.venv/bin/python3"
```

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
python3 peacock_server.py
```

You should see:
```
🦚 PEACOCK MCP SERVER v1.1.0 🦚
📁 Base directory: /your/home/directory
🚀 Starting server...
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'mcp'`

**macOS:** `pip3 install fastmcp`
**Linux:** `pip3 install --break-system-packages fastmcp`
**Venv (recommended):** `pip install fastmcp` (inside activated venv)

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
pip install Pillow numpy   # one-time setup
python3 make_logo_anim.py
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
