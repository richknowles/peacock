# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Identity

Peacock is a Model Context Protocol (MCP) server that gives AI agents full filesystem access, cross-browser automation, and VM control — all from Python with no Node.js dependency. It is authored by **Rich Knowles**. All commits must be attributed to Rich Knowles only. Do not include "Claude", "Claude Code", or "Anthropic" in any commit messages, code comments, or documentation.

Current version: **v1.1.2**

## Architecture

Three Python files form the complete server:

| File | Role |
|------|------|
| `peacock_server.py` | Entry point. Registers all 36 MCP tools via `@mcp.tool()`. Imports `peacock_browser` and `peacock_vm` as `_browser` / `_vm`, falling back gracefully when optional deps are missing. |
| `peacock_browser.py` | Browser automation. Chrome via CDP (attaches to a running instance — zero launch latency). Firefox, Safari, Edge via Selenium. Bookmark management via direct Chrome JSON file manipulation. |
| `peacock_vm.py` | Proxmox VE integration via `proxmoxer`. VM list/start/stop/status, QEMU Guest Agent command execution, VNC screenshot via `vncdotool`. |

### Tool Groups (36 total)

- **Filesystem (6):** `read_file`, `write_file`, `list_directory`, `execute_command`, `search_files`, `get_file_info`
- **Browser (18):** `browser_open`, `browser_navigate`, `browser_new_tab`, `browser_close_tab`, `browser_screenshot`, `browser_click`, `browser_type`, `browser_get_content`, `browser_get_text`, `browser_scroll`, `browser_execute_js`, `browser_wait_for`, `browser_list_tabs`, `browser_list_sessions`, `browser_close`, `browser_bookmark_add`, `browser_bookmark_group`
- **VM / Proxmox (9):** `vm_connect`, `vm_list`, `vm_status`, `vm_start`, `vm_stop`, `vm_screenshot`, `vm_execute`, `vm_browser_open`, `vm_list_connections`, `vm_disconnect`
- **Scheduling (3):** `schedule_task`, `list_scheduled_tasks`, `remove_scheduled_task`

### Chrome CDP vs Selenium

`browser_open()` with `browser="chrome"` tries CDP first:
1. Checks `http://localhost:{cdp_port}/json` for a running Chrome instance
2. Attaches to it instantly via WebSocket — no browser launch, no driver download
3. If Chrome is not running, launches it with `--remote-debugging-port={cdp_port}`
4. Falls back to Selenium only if CDP is completely unavailable

Firefox, Safari, Edge always use Selenium. `webdriver-manager` handles driver downloads automatically.

### Security Model

All filesystem tools enforce `str(resolved_path).startswith(str(Path.home()))`. Change `BASE_DIR` at the top of `peacock_server.py` to expand or restrict scope.

## Commands

```bash
# Install all dependencies
pip3 install -r requirements.txt                          # macOS
pip3 install --break-system-packages -r requirements.txt  # Linux

# Platform-specific install (handles config hints, browser checks)
./install_mac.sh          # macOS
./install.sh              # Linux (auto-detects macOS and delegates)
.\install_windows.ps1     # Windows (run in PowerShell as Administrator)

# Smoke-test the server (Ctrl-C to stop once you see the startup banner)
python3 peacock_server.py

# Syntax-check all modules
python3 -c "import py_compile; [py_compile.compile(f, doraise=True) for f in ['peacock_server.py','peacock_browser.py','peacock_vm.py']]"

# Run existing install verification
./test.sh
```

## Platform Targets

All code must work on macOS, Linux, and Windows. Platform is detected via `platform.system()` returning `'Darwin'` | `'Linux'` | `'Windows'`. Browser-specific paths and commands are gated on this value.

**Browser support matrix:**

| Browser | macOS | Linux | Windows | Method |
|---------|-------|-------|---------|--------|
| Chrome | ✅ | ✅ | ✅ | CDP (attach) + Selenium (launch) |
| Firefox | ✅ | ✅ | ✅ | Selenium + GeckoDriver |
| Safari | ✅ | ❌ | ❌ | Selenium SafariDriver |
| Edge | ✅ | ✅ | ✅ | Selenium EdgeDriver |

## Claude Desktop Integration

Config path by platform:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "peacock": {
      "command": "python3",
      "args": ["/full/path/to/peacock/peacock_server.py"]
    }
  }
}
```

On Windows use `"python"` instead of `"python3"`. Logs at `~/.config/Claude/logs/` (Linux) or `~/Library/Logs/Claude/` (macOS).

## Key Design Decisions

- **CDP-first for Chrome** — attaches to the user's real browser with their cookies, extensions, and saved passwords. This is the primary differentiator vs Playwright.
- **No Node.js** — pure Python stack. `proxmoxer` handles Proxmox REST API. `websocket-client` handles CDP WebSocket.
- **Optional deps are truly optional** — `peacock_browser` and `peacock_vm` import errors are caught at server startup; affected tools return a helpful install message rather than crashing.
- **Scheduling uses system cron** — `crontab` on Linux/macOS, `schtasks` on Windows. Peacock-managed entries are tagged with `# peacock-managed:<name>` for safe update/removal.
- **Chrome bookmarks** — written directly to the Bookmarks JSON file. Chrome recomputes the checksum on next launch. Users must restart Chrome to see new bookmarks.
- **VM screenshot** — requires `vncdotool` (not in default requirements to keep install light). Listed in `requirements.txt` as a comment to install manually.

## Dependencies

```
fastmcp>=0.1.0          # MCP server framework
websocket-client>=1.6.0 # Chrome CDP WebSocket
requests>=2.31.0        # CDP HTTP + proxmoxer HTTP backend
selenium>=4.15.0        # Firefox / Safari / Edge
webdriver-manager>=4.0.0 # Auto-downloads browser drivers
proxmoxer>=2.0.0        # Proxmox VE REST API
# vncdotool>=1.0.0      # VM screenshots (optional, install separately)
```
