<p align="center">
  <img src="peacock_branding_1024x1024.png" alt="Peacock" width="320"/>
</p>

<h1 align="center">🦚 Peacock MCP Server</h1>

<p align="center">
  <strong>The AI agent platform that makes Playwright look slow.</strong>
</p>

<p align="center">
  <a href="https://github.com/richknowles/peacock/releases"><img src="https://img.shields.io/badge/version-1.1.2-blueviolet?style=flat-square" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/browsers-Chrome%20%7C%20Firefox%20%7C%20Safari%20%7C%20Edge-orange?style=flat-square" alt="Browsers">
  <img src="https://img.shields.io/badge/VM-Proxmox%20VE-E57000?style=flat-square" alt="Proxmox">
  <img src="https://img.shields.io/badge/protocol-MCP-5C4EE5?style=flat-square" alt="MCP">
  <img src="https://img.shields.io/badge/security-hardened-red?style=flat-square" alt="Security Hardened">
  <img src="https://img.shields.io/badge/Node.js-not%20required-success?style=flat-square" alt="No Node.js">
</p>

---

# Chapter 1 — What Peacock Is

## Overview

Peacock is a **Model Context Protocol (MCP) server** written in pure Python. It gives any MCP-compatible AI agent — Claude Desktop, custom agents, LLM pipelines — a complete toolkit for operating a real computer:

- **Filesystem** — read, write, search, execute commands
- **Browser automation** — Chrome (via CDP), Firefox, Safari, Edge across macOS, Linux, and Windows
- **VM control** — Proxmox VE: start/stop VMs, run commands inside guests, take VNC screenshots, open browsers in guest OS
- **Remote browser** — control Chrome on a Mac or Windows VM from a headless LXC over SSH
- **Scheduling** — native cron (Linux/macOS) and Windows Task Scheduler

**41 MCP tools. Zero Node.js. No bundled browsers. No Playwright.**

---

## Security Hardening

> **For admins and security teams:** Peacock was subjected to a full pre-release vulnerability audit. Every finding was remediated before v1.1.0 shipped. The table below is the complete record.

| # | Finding | Severity | Remediation |
|---|---------|:--------:|-------------|
| 1 | Path traversal via `startswith()` string comparison | **HIGH** | Replaced with `Path.relative_to()` — raises `ValueError` on any escape attempt |
| 2 | Symlink escape via unresolved `BASE_DIR` | **HIGH** | `BASE_DIR` resolved with `.resolve()` at startup, eliminating symlink chains |
| 3 | Command injection via `shell=True` | **CRITICAL** | Switched to `shlex.split()` + `shell=False`; shell metacharacters never interpreted |
| 4 | TOCTOU race in `write_file` mkdir | MEDIUM | Path re-verified with `_safe_path()` after `mkdir` to catch symlink swaps |
| 5 | Unbounded glob patterns (DoS vector) | MEDIUM | Allowlist regex on pattern characters; `**` depth capped at 2 |
| 6 | No rate limiting | MEDIUM | Token bucket: 30 calls / 10 s per tool, enforced server-side |
| 7 | Unvalidated `mode` parameter in `write_file` | LOW–MED | Strict allowlist — only `"w"` or `"a"` accepted |
| 8 | Error messages leak home path | LOW | All exception strings scrubbed; home path replaced with `~` before returning |

**Baseline security posture (always enforced):**
- All filesystem operations restricted to the user's home directory via `_safe_path()`
- `BASE_DIR` is configurable — set it to a dedicated sandbox directory for tighter containment
- Command execution timeout: 30 seconds maximum
- Server runs as the invoking user — never root, never elevated

---

## Tool Reference (41 tools)

### Filesystem

| Tool | Description |
|------|-------------|
| `read_file(path)` | Read a file; returns content with byte count |
| `write_file(path, content, mode)` | Write (`w`) or append (`a`) to a file; creates parent dirs |
| `list_directory(path, show_hidden)` | List directory contents with sizes |
| `execute_command(command, cwd)` | Run a shell command; 30 s timeout, no shell injection |
| `search_files(pattern, directory, max_results)` | Recursive glob search with pattern allowlist |
| `get_file_info(path)` | Size, permissions, mtime, extension |

### Browser — Chrome (CDP)

Chrome attaches to a **running instance** via the Chrome DevTools Protocol — zero launch latency, access to your real cookies, extensions, and saved passwords. No WebDriver, no browser download.

| Tool | Description |
|------|-------------|
| `browser_open(url, browser, cdp_host, cdp_port)` | Open/attach browser; `cdp_host` accepts a remote IP for cross-machine control |
| `browser_navigate(url)` | Navigate current tab |
| `browser_new_tab(url)` | Open new tab |
| `browser_close_tab()` | Close current tab |
| `browser_click(selector)` | Click element by CSS selector |
| `browser_type(selector, text)` | Clear and type into an input |
| `browser_get_content()` | Page title, URL, HTML preview |
| `browser_get_text(selector)` | Visible text of page or element |
| `browser_scroll(direction, pixels)` | Scroll up / down / left / right |
| `browser_screenshot(save_path)` | PNG screenshot |
| `browser_execute_js(script)` | Execute JavaScript, return result |
| `browser_wait_for(selector, timeout)` | Poll until element appears |
| `browser_list_tabs()` | All open tabs with title + URL |
| `browser_list_sessions()` | All active Peacock browser sessions |
| `browser_close()` | Close session, free resources |

### Browser — Bookmarks & Tab Groups

| Tool | Description |
|------|-------------|
| `browser_bookmark_add(url, title, folder, browser)` | Add one bookmark; writes Chrome JSON directly, triggers Safari Reading List, opens Firefox dialog |
| `browser_bookmark_group(urls_and_titles, folder, browser)` | Bookmark a JSON list of `{url, title}` objects in one call |
| `browser_open_tab_group(urls_and_titles, group_name, cdp_host)` | Open all URLs as tabs, attempt Chrome 102+ tab group, bookmark as folder |

### Browser — Remote & SSH

| Tool | Description |
|------|-------------|
| `browser_setup_ssh_tunnel(remote_host, remote_user, cdp_port, ssh_key)` | SSH tunnel from this machine to a remote Chrome CDP port; enables cross-machine control |
| `browser_close_ssh_tunnel()` | Close the active SSH tunnel |

### Mac-Specific (SSH + AppleScript)

Control Safari or Chrome on a Mac from any remote machine — including a headless LXC.

| Tool | Description |
|------|-------------|
| `mac_safari_open_and_bookmark(urls_and_titles, folder, mac_host, mac_user)` | Open Safari tabs, create bookmark folder, attempt Tab Group (Safari 15+) |
| `mac_chrome_open_and_bookmark(urls_and_titles, folder, mac_host, mac_user)` | Open Chrome tabs and write bookmarks via remote python3 |

### VM / Proxmox

| Tool | Description |
|------|-------------|
| `vm_connect(host, username, password)` | Connect to Proxmox VE REST API |
| `vm_list()` | All VMs across all nodes with status |
| `vm_status(vm_id)` | CPU%, RAM, uptime for one VM |
| `vm_start(vm_id)` | Start a VM |
| `vm_stop(vm_id, force)` | Graceful shutdown or force-stop |
| `vm_screenshot(vm_id, save_path)` | VNC screenshot via `vncdotool` |
| `vm_execute(vm_id, command)` | Run command in guest via QEMU Guest Agent |
| `vm_browser_open(vm_id, url, browser)` | Launch browser in guest OS |
| `vm_list_connections()` | Active Proxmox connections |
| `vm_disconnect()` | Close Proxmox connection |

### Scheduling

| Tool | Description |
|------|-------------|
| `schedule_task(name, cron_expr, command)` | Add/update a named cron job (Linux/macOS) or Windows Task Scheduler entry |
| `list_scheduled_tasks()` | All Peacock-managed scheduled tasks |
| `remove_scheduled_task(name)` | Remove by name |

---

# Chapter 2 — Human Installation & Operation

## Prerequisites

| Platform | Requirement |
|----------|-------------|
| macOS | Python 3.10+, Claude Desktop |
| Linux | Python 3.10+, python3-venv, Claude Desktop |
| Windows | Python 3.10+ (from python.org, "Add to PATH" checked), Claude Desktop |

---

## Install

**macOS**
```bash
git clone https://github.com/richknowles/peacock
cd peacock
./install_mac.sh
```

**Linux**
```bash
git clone https://github.com/richknowles/peacock
cd peacock
./install.sh
```

**Windows** — open PowerShell as Administrator:
```powershell
git clone https://github.com/richknowles/peacock
cd peacock
.\install_windows.ps1
```

The installer creates a `.venv`, installs all dependencies, and prints the exact JSON block to paste into your Claude Desktop config.

---

## Configure Claude Desktop

Paste the output from the installer into your Claude Desktop config file and restart.

| Platform | Config file location |
|----------|----------------------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

It looks like this (paths filled in by the installer):
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

---

## Verify the Install

```bash
.venv/bin/python3 peacock_server.py
```

Expected output:
```
🦚 PEACOCK MCP SERVER — v1.1.2 🦚
Built by Rich Knowles
🖥️  Platform: Darwin
📁 Base directory: /Users/yourname
🌐 Browser tools: ✅ ready
🖥️  VM tools:      ✅ ready
🚀 Starting server...
```

---

## Browser Setup (Human)

### Chrome — no setup needed
Peacock attaches to Chrome you already have open. Nothing to install or configure.

### Firefox
```bash
.venv/bin/pip install webdriver-manager   # downloads GeckoDriver automatically on first use
```

### Safari (macOS only — one-time)
```bash
sudo safaridriver --enable
```

### Edge
Built into Windows. No setup needed.

### Proxmox VM Control (optional)
```bash
.venv/bin/pip install proxmoxer
.venv/bin/pip install vncdotool   # only needed for vm_screenshot
```
Inside each guest VM, install and start `qemu-guest-agent` for `vm_execute` to work.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'mcp'`** — Re-run the installer. The `.venv` may not have been activated.

**`Permission denied` on the server script** — `chmod +x peacock_server.py`

**Claude Desktop doesn't see Peacock** — Check the JSON syntax is valid, restart Claude Desktop fully, and check logs at `~/.config/Claude/logs/` (Linux) or `~/Library/Logs/Claude/` (macOS).

**Browser tools unavailable** — Run `.venv/bin/pip install selenium webdriver-manager websocket-client requests` inside the Peacock directory.

**`browser_bookmark_add` for Chrome — bookmarks don't appear** — Chrome must be restarted to pick up direct file changes to the Bookmarks JSON.

---

# Chapter 3 — Agent Installation & Operation

## What Agents Can Do

Any MCP-compatible AI agent can load Peacock and gain all 41 tools immediately. This includes agents running on:

- Claude Desktop (local)
- Headless LXC containers (Ubuntu 22.04 recommended)
- Remote servers and VMs
- Any platform with Python 3.10+ and an MCP client

---

## Agent Install (Headless Linux / LXC)

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv openssh-client git
git clone https://github.com/richknowles/peacock
cd peacock
./install.sh
```

Configure the agent's MCP client to point to:
```
command: /path/to/peacock/.venv/bin/python3
args:    [/path/to/peacock/peacock_server.py]
```

---

## Controlling a Remote Browser from a Headless Agent

### Path A — Mac Chrome via SSH tunnel (recommended)

**On the Mac (one-time):**
```bash
# Enable Remote Login
# System Settings → General → Sharing → Remote Login → ON

# Authorize the agent's SSH key
ssh-copy-id agent_user@agent_host   # run from Mac, pointing at the LXC

# Start Chrome with remote debugging
open -a "Google Chrome" --args --remote-debugging-port=9222
```

**Agent calls:**
```
browser_setup_ssh_tunnel("192.168.1.x", "rich", cdp_port=9222)
browser_open_tab_group('[{"url":"...","title":"..."}]', group_name="Watch List")
```

### Path B — Mac Safari / Chrome via AppleScript (no CDP needed)

**On the Mac (one-time):**
```bash
# Enable Remote Login (same as above)
ssh-copy-id agent_user@agent_host
```

**Agent calls:**
```
mac_safari_open_and_bookmark(
  '[{"url":"https://example.com","title":"Item"}]',
  folder="Product Watch",
  mac_host="192.168.1.x",
  mac_user="rich"
)
```

Safari tabs open on the Mac, a bookmark folder is created, and a Tab Group is attempted (Safari 15+ / macOS Monterey+). No CDP, no display, no extensions.

### Path C — Windows VM via Proxmox Guest Agent

```
vm_connect("proxmox-host", "root@pam", "password")
vm_execute(101, 'cmd /c start chrome --remote-debugging-port=9222 --remote-debugging-host=0.0.0.0')
browser_open_tab_group('[{"url":"...","title":"..."}]', cdp_host="windows-vm-ip")
```

---

## Agent Workflow: Product Watch Cron Job

A complete example — Hermes-Agent on an LXC sets up a recurring product watch that opens tabs on the user's Mac:

```
1. mac_safari_open_and_bookmark(
     '[{"url":"https://amazon.com/dp/X","title":"Widget"},
       {"url":"https://ebay.com/itm/123","title":"Widget (eBay)"}]',
     folder="Widget Watch",
     mac_host="192.168.1.50",
     mac_user="rich"
   )

2. schedule_task(
     name="widget-watch",
     cron_expr="0 8 * * *",
     command="python3 /home/hermes/check_widget_price.py"
   )
```

Result: every morning at 08:00 the price check script runs; any time the user wants to browse manually, the tabs and bookmarks are ready in Safari.

---

## Remote Browser Capability Matrix

| Scenario | Tool | Requires |
|----------|------|----------|
| Agent on LXC → Mac Chrome (fast, full control) | `browser_setup_ssh_tunnel` + `browser_open` | Remote Login on Mac, SSH key |
| Agent on LXC → Mac Safari (tabs + bookmarks) | `mac_safari_open_and_bookmark` | Remote Login on Mac, SSH key |
| Agent on LXC → Mac Chrome (tabs + bookmarks, no CDP) | `mac_chrome_open_and_bookmark` | Remote Login on Mac, SSH key |
| Agent on LXC → Windows VM browser | `vm_execute` + `browser_open(cdp_host=...)` | Proxmox Guest Agent in VM |
| Agent on LXC → Windows VM browser (simple) | `vm_browser_open` | Proxmox Guest Agent in VM |

---

# Chapter 4 — Human Tips & Tricks

**Change the security boundary.**
`BASE_DIR` in `peacock_server.py` defaults to your home directory. Point it at a dedicated workspace folder to tighten the sandbox, or expand it to `/` only if you fully understand the implications.

**Keep Chrome open for instant response.**
Peacock attaches to a running Chrome tab in milliseconds. If Chrome is closed, it launches a fresh profile — which is slower and doesn't have your cookies. Leave Chrome open.

**Regenerate the animated logo.**
```bash
.venv/bin/pip install Pillow numpy
.venv/bin/python3 make_logo_anim.py
```

**Run a quick sanity check before connecting Claude Desktop.**
```bash
.venv/bin/python3 -c "import peacock_browser, peacock_vm; print('All modules OK')"
```

**Tab groups aren't appearing after `browser_open_tab_group`.**
Chrome's tab group API (`chrome.tabGroups`) is an extension-only API. Peacock tries the CDP method (Chrome 102+) but it's experimental. The tabs are still open — select them all, right-click, and choose *Add tabs to new group* in 2 seconds.

**Bookmark changes don't appear in Chrome.**
Chrome reads the Bookmarks file at startup. Close and reopen Chrome after `browser_bookmark_add` or `browser_bookmark_group` to see new entries.

**Use `execute_command` for anything not covered by a dedicated tool.**
It runs any shell command. On macOS you can call `osascript`, `open`, `say`, or any CLI tool. On Linux, `curl`, `jq`, `ffmpeg` — whatever is installed.

---

# Chapter 5 — Agent Tips & Tricks

**Always check `browser_list_sessions()` before opening a new browser.**
Reusing an existing session is instant. Opening a new one takes 1–3 s for Selenium, ~100 ms for CDP.

**Use `cdp_host` for cross-machine control without a tunnel.**
If the Chrome machine is on a trusted private network and firewall rules allow port 9222, pass `cdp_host="192.168.1.x"` directly to `browser_open`. No SSH tunnel required.

**Chain `vm_execute` + `browser_open` for Windows VM browsing.**
```
vm_execute(101, 'cmd /c start chrome --remote-debugging-port=9222 --remote-debugging-host=0.0.0.0')
# wait ~3s for Chrome to start
browser_open("https://example.com", cdp_host="192.168.1.101", cdp_port=9222)
```
After that, all 15+ browser control tools work against the Windows VM's Chrome.

**Use `browser_execute_js` to extract structured data.**
```
browser_execute_js("Array.from(document.querySelectorAll('.price')).map(e => e.innerText)")
```
Returns a JSON array. Faster and more reliable than scraping HTML.

**`browser_wait_for` before `browser_click`.**
Always wait for the target element to exist before clicking. Pages with dynamic content will silently fail otherwise.

**Prefer `browser_get_text` over `browser_get_content` for data extraction.**
`get_content` returns the full HTML source (can be large). `get_text` returns only visible text, which is smaller and easier to parse.

**SSH key path matters on LXC.**
When calling `mac_safari_open_and_bookmark` or `browser_setup_ssh_tunnel`, pass `ssh_key="/home/hermes/.ssh/id_ed25519"` explicitly if the agent's home directory is non-standard.

**`schedule_task` creates idempotent entries.**
Calling `schedule_task` with the same `name` replaces the existing entry rather than adding a duplicate. Safe to call repeatedly.

**Check VM status before `vm_execute`.**
Always call `vm_status(vm_id)` first. If the VM is stopped, `vm_execute` will silently fail because the QEMU Guest Agent isn't running.

**Screenshot → read the result path → open it.**
`browser_screenshot` saves to `~/peacock_screenshot_<timestamp>.png` by default. Pass a specific `save_path` if you need a predictable location for follow-up `read_file` calls.

---

# About

**Built by:** Rich Knowles

**Why "Peacock"?** Because the AI wants to show off. 🦚

**License:** MIT
