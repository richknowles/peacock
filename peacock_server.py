#!/usr/bin/env python3
"""
🦚 PEACOCK MCP SERVER — v1.1.2
Built by Rich Knowles

Full-stack AI agent platform:
  • Filesystem: read, write, search, execute commands
  • Browser: Chrome (CDP), Firefox, Safari, Edge — all platforms
  • VM: Proxmox VE — start/stop/screenshot/execute/browser
  • Scheduling: cron-based task automation
"""

import os
import platform
import re
import shlex
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional

VERSION = "1.1.2"
__version__ = VERSION
PLATFORM = platform.system()

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("ERROR: FastMCP not installed. Run: pip install fastmcp")
    exit(1)

try:
    import peacock_browser as _browser
    BROWSER_AVAILABLE = True
except ImportError as _err:
    BROWSER_AVAILABLE = False
    _browser_err = str(_err)

try:
    import peacock_vm as _vm
    VM_AVAILABLE = True
except ImportError as _err:
    VM_AVAILABLE = False
    _vm_err = str(_err)

mcp = FastMCP("Peacock")

# Resolve symlinks at startup so BASE_DIR is always a canonical path
BASE_DIR = Path.home().resolve()


# ── Rate limiting ─────────────────────────────────────────────────────────────
_RATE_LIMIT = 30        # max calls per tool
_RATE_WINDOW = 10.0     # per N seconds
_call_log: dict[str, list[float]] = defaultdict(list)


def _check_rate(tool: str) -> str | None:
    now = time.monotonic()
    _call_log[tool] = [t for t in _call_log[tool] if now - t < _RATE_WINDOW]
    if len(_call_log[tool]) >= _RATE_LIMIT:
        return f"❌ Rate limit: max {_RATE_LIMIT} calls/{_RATE_WINDOW:.0f}s for {tool}"
    _call_log[tool].append(now)
    return None


# ── Path safety ───────────────────────────────────────────────────────────────
def _safe_path(raw: str) -> Path:
    """Resolve path (including symlinks) and assert it is inside BASE_DIR.

    Uses relative_to() which raises ValueError on any escape — immune to
    string-prefix bypass and symlink-chain attacks.
    """
    resolved = Path(raw).expanduser().resolve()
    try:
        resolved.relative_to(BASE_DIR)
    except ValueError:
        raise PermissionError("Access denied: path is outside the allowed directory")
    return resolved


def _safe_err(e: Exception) -> str:
    """Return error message with home path redacted to avoid info disclosure."""
    return str(e).replace(str(BASE_DIR), "~")


# ── Glob pattern allowlist ────────────────────────────────────────────────────
_GLOB_SAFE = re.compile(r"^[\w\-.*?\[\]{}]+$")


# ══════════════════════════════════════════════════════════════════════════════
# FILESYSTEM TOOLS
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def read_file(path: str) -> str:
    """
    Read the contents of a file.

    Args:
        path: Absolute or relative path to the file

    Returns:
        File contents as string
    """
    if err := _check_rate("read_file"):
        return err
    try:
        file_path = _safe_path(path)
        if not file_path.exists():
            return f"❌ File not found: {path}"
        if not file_path.is_file():
            return f"❌ Not a file: {path}"
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        return f"✅ Read {len(content)} bytes from {path}\n\n{content}"
    except PermissionError as e:
        return f"❌ {e}"
    except Exception as e:
        return f"❌ Error reading file: {_safe_err(e)}"


@mcp.tool()
def write_file(path: str, content: str, mode: str = "w") -> str:
    """
    Write content to a file.

    Args:
        path: Absolute or relative path to the file
        content: Content to write
        mode: Write mode — 'w' (overwrite) or 'a' (append)

    Returns:
        Success/failure message
    """
    if err := _check_rate("write_file"):
        return err
    if mode not in ("w", "a"):
        return "❌ Invalid mode: must be 'w' (overwrite) or 'a' (append)"
    try:
        file_path = _safe_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # Re-verify after mkdir to catch symlink swaps (TOCTOU mitigation)
        file_path = _safe_path(path)
        with open(file_path, mode, encoding="utf-8") as f:
            f.write(content)
        return f"✅ Wrote {len(content)} bytes to {path}"
    except PermissionError as e:
        return f"❌ {e}"
    except Exception as e:
        return f"❌ Error writing file: {_safe_err(e)}"


@mcp.tool()
def list_directory(path: str = ".", show_hidden: bool = False) -> str:
    """
    List contents of a directory.

    Args:
        path: Directory path (default: current directory)
        show_hidden: Include hidden files (default: False)

    Returns:
        Directory listing
    """
    if err := _check_rate("list_directory"):
        return err
    try:
        dir_path = _safe_path(path)
        if not dir_path.exists():
            return f"❌ Directory not found: {path}"
        if not dir_path.is_dir():
            return f"❌ Not a directory: {path}"
        items = []
        for item in sorted(dir_path.iterdir()):
            if not show_hidden and item.name.startswith("."):
                continue
            if item.is_dir():
                items.append(f"📁 {item.name}/")
            else:
                items.append(f"📄 {item.name} ({item.stat().st_size} bytes)")
        if not items:
            return f"📂 {dir_path} is empty"
        return f"📂 {dir_path}\n\n" + "\n".join(items)
    except PermissionError as e:
        return f"❌ {e}"
    except Exception as e:
        return f"❌ Error listing directory: {_safe_err(e)}"


@mcp.tool()
def execute_command(command: str, cwd: Optional[str] = None) -> str:
    """
    Execute a shell command.

    Args:
        command: Shell command to execute
        cwd: Working directory (default: home directory)

    Returns:
        Command output (stdout, stderr, exit code)
    """
    if err := _check_rate("execute_command"):
        return err
    try:
        work_dir = _safe_path(cwd) if cwd else BASE_DIR
        args = shlex.split(command)
        if not args:
            return "❌ Empty command"
        result = subprocess.run(
            args,
            shell=False,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = [
            f"🦚 Executed: {command}",
            f"📍 Working directory: {work_dir}",
            f"↩️  Exit code: {result.returncode}",
        ]
        if result.stdout:
            output.append(f"\n📤 STDOUT:\n{result.stdout}")
        if result.stderr:
            output.append(f"\n📤 STDERR:\n{result.stderr}")
        return "\n".join(output)
    except subprocess.TimeoutExpired:
        return "❌ Command timed out after 30 seconds"
    except PermissionError as e:
        return f"❌ {e}"
    except Exception as e:
        return f"❌ Error executing command: {_safe_err(e)}"


@mcp.tool()
def search_files(pattern: str, directory: str = ".", max_results: int = 50) -> str:
    """
    Search for files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g., "*.py", "test_*.txt")
        directory: Directory to search in
        max_results: Maximum number of results

    Returns:
        List of matching files
    """
    if err := _check_rate("search_files"):
        return err
    if not _GLOB_SAFE.match(pattern):
        return "❌ Invalid pattern: only alphanumeric, *, ?, [], {}, -, and . are allowed"
    if pattern.count("**") > 2:
        return "❌ Invalid pattern: too many recursive wildcards"
    try:
        search_dir = _safe_path(directory)
        if not search_dir.exists():
            return f"❌ Directory not found: {directory}"
        matches = []
        for p in search_dir.rglob(pattern):
            if len(matches) >= max_results:
                matches.append(f"... and more (limit: {max_results})")
                break
            relative = p.relative_to(search_dir)
            matches.append(f"📁 {relative}/" if p.is_dir() else f"📄 {relative}")
        if not matches:
            return f"❌ No files matching '{pattern}' found in {directory}"
        return f"🔍 Found {len(matches)} matches for '{pattern}':\n\n" + "\n".join(matches)
    except PermissionError as e:
        return f"❌ {e}"
    except Exception as e:
        return f"❌ Error searching files: {_safe_err(e)}"


@mcp.tool()
def get_file_info(path: str) -> str:
    """
    Get detailed information about a file or directory.

    Args:
        path: Path to file or directory

    Returns:
        Detailed file information
    """
    if err := _check_rate("get_file_info"):
        return err
    try:
        file_path = _safe_path(path)
        if not file_path.exists():
            return f"❌ Path not found: {path}"
        stat = file_path.stat()
        info = [
            f"📋 File Information: {file_path}",
            f"Type: {'📁 Directory' if file_path.is_dir() else '📄 File'}",
            f"Size: {stat.st_size} bytes",
            f"Modified: {stat.st_mtime}",
            f"Permissions: {oct(stat.st_mode)[-3:]}",
        ]
        if file_path.is_file():
            info.append(f"Extension: {file_path.suffix}")
        return "\n".join(info)
    except PermissionError as e:
        return f"❌ {e}"
    except Exception as e:
        return f"❌ Error getting file info: {_safe_err(e)}"


# ══════════════════════════════════════════════════════════════════════════════
# BROWSER TOOLS
# ══════════════════════════════════════════════════════════════════════════════

def _browser_unavailable(name: str) -> str:
    msg = f"❌ Browser tool '{name}' unavailable."
    if not BROWSER_AVAILABLE:
        msg += f"\n   Import error: {_browser_err}"
        msg += "\n   Run: pip install selenium webdriver-manager websocket-client requests"
    return msg


@mcp.tool()
def browser_open(url: str, browser: str = "chrome", headless: bool = False,
                 attach: bool = True, cdp_port: int = 9222,
                 cdp_host: str = "localhost") -> str:
    """
    Open a browser and navigate to a URL.
    browser: chrome (default) | firefox | safari | edge
    attach=True: for Chrome, attaches to an already-running instance via CDP — no launch delay.
    headless=True: run without a visible window (Chrome/Firefox/Edge only).
    cdp_host: set to a remote IP/hostname to control Chrome on another machine
              (e.g. your Mac or a Windows VM). Use browser_setup_ssh_tunnel first
              for a secure connection, then leave cdp_host as 'localhost'.
    Returns a session ID used by all other browser_ tools.
    """
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_open")
    return _browser.browser_open(url, browser, headless, attach, cdp_port, cdp_host)


@mcp.tool()
def browser_navigate(url: str, session_id: Optional[str] = None) -> str:
    """Navigate the active (or specified) browser tab to a URL."""
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_navigate")
    return _browser.browser_navigate(url, session_id)


@mcp.tool()
def browser_new_tab(url: str = "about:blank", session_id: Optional[str] = None) -> str:
    """Open a new tab in the current browser session and optionally navigate to a URL."""
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_new_tab")
    return _browser.browser_new_tab(url, session_id)


@mcp.tool()
def browser_close_tab(session_id: Optional[str] = None) -> str:
    """Close the current tab. The browser remains open; other tabs are unaffected."""
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_close_tab")
    return _browser.browser_close_tab(session_id)


@mcp.tool()
def browser_screenshot(save_path: Optional[str] = None, session_id: Optional[str] = None) -> str:
    """
    Capture a screenshot of the current browser tab and save it as a PNG.
    Defaults to ~/peacock_screenshot_<timestamp>.png.
    """
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_screenshot")
    return _browser.browser_screenshot(save_path, session_id)


@mcp.tool()
def browser_click(selector: str, session_id: Optional[str] = None) -> str:
    """Click a page element identified by a CSS selector (e.g. '#submit', '.btn-primary')."""
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_click")
    return _browser.browser_click(selector, session_id)


@mcp.tool()
def browser_type(selector: str, text: str, session_id: Optional[str] = None) -> str:
    """Clear an input element (CSS selector) and type the given text into it."""
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_type")
    return _browser.browser_type(selector, text, session_id)


@mcp.tool()
def browser_get_content(session_id: Optional[str] = None) -> str:
    """Return the current tab's title, URL, and a preview of the page HTML source."""
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_get_content")
    return _browser.browser_get_content(session_id)


@mcp.tool()
def browser_get_text(selector: Optional[str] = None, session_id: Optional[str] = None) -> str:
    """
    Return the visible text of the page or of a specific element.
    selector: CSS selector (optional). Omit to get all body text.
    """
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_get_text")
    return _browser.browser_get_text(selector, session_id)


@mcp.tool()
def browser_scroll(direction: str = "down", pixels: int = 500,
                   session_id: Optional[str] = None) -> str:
    """Scroll the page. direction: up | down | left | right. pixels: scroll distance."""
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_scroll")
    return _browser.browser_scroll(direction, pixels, session_id)


@mcp.tool()
def browser_execute_js(script: str, session_id: Optional[str] = None) -> str:
    """
    Execute arbitrary JavaScript in the current tab and return the result.
    Example: browser_execute_js("document.title")
    """
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_execute_js")
    return _browser.browser_execute_js(script, session_id)


@mcp.tool()
def browser_wait_for(selector: str, timeout: int = 10,
                     session_id: Optional[str] = None) -> str:
    """Poll until a CSS selector appears on the page, or timeout (seconds) is reached."""
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_wait_for")
    return _browser.browser_wait_for(selector, timeout, session_id)


@mcp.tool()
def browser_list_tabs(session_id: Optional[str] = None) -> str:
    """List all open tabs in the current browser session with titles and URLs."""
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_list_tabs")
    return _browser.browser_list_tabs(session_id)


@mcp.tool()
def browser_list_sessions() -> str:
    """List all active Peacock browser sessions and which one is currently active."""
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_list_sessions")
    return _browser.browser_list_sessions()


@mcp.tool()
def browser_close(session_id: Optional[str] = None) -> str:
    """Close the active (or specified) browser session and release its resources."""
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_close")
    return _browser.browser_close(session_id)


@mcp.tool()
def browser_bookmark_add(url: str, title: str = "", folder: str = "Peacock Watches",
                          browser: str = "chrome",
                          session_id: Optional[str] = None) -> str:
    """
    Add a single bookmark.
    Chrome: writes to the Bookmarks JSON file directly (restart Chrome to see it).
    Firefox: triggers the bookmark dialog via keyboard shortcut (confirm manually).
    Safari (macOS): adds to Reading List.
    folder: name of the bookmark folder to create/use.
    """
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_bookmark_add")
    return _browser.browser_bookmark_add(url, title, folder, browser, session_id)


@mcp.tool()
def browser_bookmark_group(urls_and_titles: str, folder: str = "Peacock Watches",
                            browser: str = "chrome",
                            session_id: Optional[str] = None) -> str:
    """
    Bookmark a group of URLs into a named folder in a single call.
    urls_and_titles: JSON array of {url, title} objects,
                     OR one URL per line (titles will match URLs).
    Example: '[{"url":"https://amazon.com/dp/X","title":"Widget"},...]'
    Creates the folder if it does not exist.
    """
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_bookmark_group")
    return _browser.browser_bookmark_group(urls_and_titles, folder, browser, session_id)


@mcp.tool()
def browser_open_tab_group(urls_and_titles: str, group_name: str = "Peacock",
                            browser: str = "chrome", bookmark_also: bool = True,
                            cdp_host: str = "localhost", cdp_port: int = 9222,
                            session_id: Optional[str] = None) -> str:
    """
    Open a list of URLs as separate tabs and create a named Chrome tab group.
    Also bookmarks them as a folder for later access.

    urls_and_titles: JSON array of {url, title} objects, or one URL per line.
    group_name: name for the Chrome tab group and bookmark folder.
    bookmark_also: also save all URLs to a Chrome bookmark folder (default True).
    cdp_host: hostname/IP of the machine running Chrome (default localhost).
              Set to a remote IP to control Chrome on your Mac or Windows VM.
              Example: browser_open_tab_group(urls, cdp_host='192.168.1.50')

    Tab group creation requires Chrome 102+. If it fails, tabs stay open and
    can be grouped manually: select all tabs → right-click → Add to new group.
    """
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_open_tab_group")
    return _browser.browser_open_tab_group(
        urls_and_titles, group_name, browser, bookmark_also, cdp_host, cdp_port, session_id
    )


@mcp.tool()
def browser_setup_ssh_tunnel(remote_host: str, remote_user: str,
                              cdp_port: int = 9222,
                              ssh_key: Optional[str] = None) -> str:
    """
    Create an SSH tunnel from this machine to a remote Chrome CDP port.
    Use this when Peacock runs on an LXC/server and needs to control Chrome
    on a Mac or Windows VM on the same network.

    remote_host: IP or hostname of the machine running Chrome.
    remote_user: SSH username on that machine.
    cdp_port: the remote debugging port Chrome is listening on (default 9222).
    ssh_key: path to SSH private key (optional).

    Chrome on the remote machine must be started with:
      --remote-debugging-port=<cdp_port>

    After setup, use browser_open or browser_open_tab_group with
    cdp_host='localhost' (the tunnel maps it through).
    """
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_setup_ssh_tunnel")
    return _browser.browser_setup_ssh_tunnel(remote_host, remote_user, cdp_port, ssh_key)


@mcp.tool()
def browser_close_ssh_tunnel() -> str:
    """Stop the background SSH tunnel started by browser_setup_ssh_tunnel."""
    if not BROWSER_AVAILABLE:
        return _browser_unavailable("browser_close_ssh_tunnel")
    return _browser.browser_close_ssh_tunnel()


# ══════════════════════════════════════════════════════════════════════════════
# VM / PROXMOX TOOLS
# ══════════════════════════════════════════════════════════════════════════════

def _vm_unavailable(name: str) -> str:
    msg = f"❌ VM tool '{name}' unavailable."
    if not VM_AVAILABLE:
        msg += f"\n   Import error: {_vm_err}"
        msg += "\n   Run: pip install proxmoxer requests vncdotool"
    return msg


@mcp.tool()
def vm_connect(host: str, username: str, password: str,
               port: int = 8006, verify_ssl: bool = False) -> str:
    """
    Connect to a Proxmox VE server.
    host: IP address or hostname (e.g. '192.168.1.10' or 'proxmox.lan').
    username: Proxmox user (e.g. 'root@pam').
    Returns a connection ID for all subsequent vm_ calls.
    """
    if not VM_AVAILABLE:
        return _vm_unavailable("vm_connect")
    return _vm.vm_connect(host, username, password, port, verify_ssl)


@mcp.tool()
def vm_list(conn_id: Optional[str] = None) -> str:
    """List all VMs across all nodes on the connected Proxmox server."""
    if not VM_AVAILABLE:
        return _vm_unavailable("vm_list")
    return _vm.vm_list(conn_id)


@mcp.tool()
def vm_status(vm_id: int, node: Optional[str] = None, conn_id: Optional[str] = None) -> str:
    """Get runtime status, CPU%, RAM usage, and uptime for a specific VM."""
    if not VM_AVAILABLE:
        return _vm_unavailable("vm_status")
    return _vm.vm_status(vm_id, node, conn_id)


@mcp.tool()
def vm_start(vm_id: int, node: Optional[str] = None, conn_id: Optional[str] = None) -> str:
    """Start a stopped or paused VM on Proxmox."""
    if not VM_AVAILABLE:
        return _vm_unavailable("vm_start")
    return _vm.vm_start(vm_id, node, conn_id)


@mcp.tool()
def vm_stop(vm_id: int, force: bool = False,
             node: Optional[str] = None, conn_id: Optional[str] = None) -> str:
    """
    Stop a VM.
    force=False (default): graceful ACPI shutdown.
    force=True: immediate power cut — use only if the VM is unresponsive.
    """
    if not VM_AVAILABLE:
        return _vm_unavailable("vm_stop")
    return _vm.vm_stop(vm_id, force, node, conn_id)


@mcp.tool()
def vm_screenshot(vm_id: int, save_path: Optional[str] = None,
                   node: Optional[str] = None, conn_id: Optional[str] = None) -> str:
    """
    Capture a screenshot of a running VM's display via the Proxmox VNC proxy.
    Requires vncdotool: pip install vncdotool
    Returns the path to the saved PNG file.
    """
    if not VM_AVAILABLE:
        return _vm_unavailable("vm_screenshot")
    return _vm.vm_screenshot(vm_id, save_path, node, conn_id)


@mcp.tool()
def vm_execute(vm_id: int, command: str, timeout: int = 30,
                node: Optional[str] = None, conn_id: Optional[str] = None) -> str:
    """
    Execute a shell command inside a running VM via the QEMU Guest Agent.
    Requires qemu-guest-agent installed and running inside the guest OS.
    Returns stdout, stderr, and exit code.
    """
    if not VM_AVAILABLE:
        return _vm_unavailable("vm_execute")
    return _vm.vm_execute(vm_id, command, timeout, node, conn_id)


@mcp.tool()
def vm_browser_open(vm_id: int, url: str, browser: str = "chrome",
                     node: Optional[str] = None, conn_id: Optional[str] = None) -> str:
    """
    Open a browser inside a VM and navigate to a URL.
    Uses the QEMU Guest Agent to launch the browser command in the guest OS.
    browser: chrome | firefox | edge
    The guest OS must have the browser installed and the Guest Agent running.
    """
    if not VM_AVAILABLE:
        return _vm_unavailable("vm_browser_open")
    return _vm.vm_browser_open(vm_id, url, browser, node, conn_id)


@mcp.tool()
def vm_list_connections() -> str:
    """List all active Proxmox connections and which one is currently active."""
    if not VM_AVAILABLE:
        return _vm_unavailable("vm_list_connections")
    return _vm.vm_list_connections()


@mcp.tool()
def vm_disconnect(conn_id: Optional[str] = None) -> str:
    """Disconnect the active (or specified) Proxmox connection."""
    if not VM_AVAILABLE:
        return _vm_unavailable("vm_disconnect")
    return _vm.vm_disconnect(conn_id)


# ══════════════════════════════════════════════════════════════════════════════
# SCHEDULING TOOLS
# ══════════════════════════════════════════════════════════════════════════════

_CRON_MARKER = "# peacock-managed"


@mcp.tool()
def schedule_task(name: str, cron_expr: str, command: str) -> str:
    """
    Create a scheduled task (cron job on Linux/macOS, schtasks on Windows).
    name: a unique identifier for this task (used to update/remove it later).
    cron_expr: standard 5-field cron expression, e.g. '0 9 * * 1-5' (weekdays at 9am).
    command: the shell command to run on schedule.
    Example: schedule_task('price-check', '0 */6 * * *', 'python3 ~/check_price.py')
    """
    if PLATFORM == "Windows":
        try:
            result = subprocess.run(
                ["schtasks", "/create", "/f", "/tn", f"Peacock\\{name}",
                 "/tr", command, "/sc", "once", "/st", "00:00"],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                return f"✅ Scheduled task '{name}' created on Windows Task Scheduler.\n⚠️  Note: full cron scheduling requires manual configuration in Task Scheduler."
            return f"❌ schtasks failed: {result.stderr}"
        except Exception as e:
            return f"❌ schedule_task failed on Windows: {e}"

    entry = f"{cron_expr} {command} {_CRON_MARKER}:{name}"
    try:
        current = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        existing = current.stdout if current.returncode == 0 else ""
        lines = [l for l in existing.splitlines() if f"{_CRON_MARKER}:{name}" not in l]
        lines.append(entry)
        new_crontab = "\n".join(lines) + "\n"
        proc = subprocess.run(["crontab", "-"], input=new_crontab, capture_output=True, text=True)
        if proc.returncode != 0:
            return f"❌ crontab update failed: {proc.stderr}"
        return f"✅ Scheduled task '{name}' added\n⏰ Schedule: {cron_expr}\n🔧 Command: {command}"
    except Exception as e:
        return f"❌ schedule_task failed: {e}"


@mcp.tool()
def list_scheduled_tasks() -> str:
    """List all Peacock-managed scheduled tasks (cron jobs or Windows tasks)."""
    if PLATFORM == "Windows":
        try:
            result = subprocess.run(
                ["schtasks", "/query", "/fo", "LIST", "/tn", "Peacock\\"],
                capture_output=True, text=True,
            )
            return result.stdout or "📭 No Peacock scheduled tasks found on Windows."
        except Exception as e:
            return f"❌ list_scheduled_tasks failed: {e}"

    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if result.returncode != 0:
            return "📭 No crontab found. No scheduled tasks."
        lines = [l for l in result.stdout.splitlines() if _CRON_MARKER in l]
        if not lines:
            return "📭 No Peacock-managed tasks in crontab."
        parts = [f"⏰ Peacock Scheduled Tasks ({len(lines)}):"]
        for l in lines:
            name = l.split(f"{_CRON_MARKER}:")[-1].strip() if f"{_CRON_MARKER}:" in l else "unnamed"
            parts.append(f"  • [{name}] {l.split(_CRON_MARKER)[0].strip()}")
        return "\n".join(parts)
    except Exception as e:
        return f"❌ list_scheduled_tasks failed: {e}"


@mcp.tool()
def remove_scheduled_task(name: str) -> str:
    """Remove a Peacock-managed scheduled task by name."""
    if PLATFORM == "Windows":
        try:
            result = subprocess.run(
                ["schtasks", "/delete", "/f", "/tn", f"Peacock\\{name}"],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                return f"✅ Windows task 'Peacock\\{name}' deleted."
            return f"❌ schtasks delete failed: {result.stderr}"
        except Exception as e:
            return f"❌ remove_scheduled_task failed: {e}"

    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if result.returncode != 0:
            return "📭 No crontab to remove from."
        lines = [l for l in result.stdout.splitlines() if f"{_CRON_MARKER}:{name}" not in l]
        subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", capture_output=True, text=True)
        return f"✅ Scheduled task '{name}' removed."
    except Exception as e:
        return f"❌ remove_scheduled_task failed: {e}"


# ══════════════════════════════════════════════════════════════════════════════
# MAC / SAFARI TOOLS  (work from any platform via SSH → osascript)
# ══════════════════════════════════════════════════════════════════════════════

def _run_on_mac(script: str, mac_host: str, mac_user: str,
                ssh_key: Optional[str] = None) -> tuple[int, str, str]:
    """
    Execute an AppleScript on a Mac, either locally (mac_host empty / localhost)
    or remotely via SSH. Returns (returncode, stdout, stderr).
    """
    osascript_cmd = ["osascript", "-e", script]

    if not mac_host or mac_host in ("localhost", "127.0.0.1"):
        result = subprocess.run(osascript_cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout.strip(), result.stderr.strip()

    ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes"]
    if ssh_key:
        ssh_cmd += ["-i", ssh_key]
    ssh_cmd.append(f"{mac_user}@{mac_host}")
    # Pass the AppleScript to osascript on the remote Mac via stdin
    ssh_cmd += ["osascript", "-"]
    result = subprocess.run(ssh_cmd, input=script, capture_output=True, text=True, timeout=30)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _build_safari_applescript(entries: list[dict], folder: str,
                               open_tabs: bool, create_tab_group: bool) -> str:
    """
    Generate AppleScript that opens URLs in Safari and/or bookmarks them.
    Handles quote-escaping so URLs and titles are safe inside the script.
    """
    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    lines = ['tell application "Safari"', "    activate"]

    if open_tabs:
        lines += [
            "    -- Open a new window if Safari has none",
            "    if (count of windows) = 0 then make new document",
            "    set w to window 1",
        ]
        for i, e in enumerate(entries):
            url = esc(e.get("url", ""))
            if i == 0:
                lines.append(f'    set URL of current tab of w to "{url}"')
            else:
                lines.append(f'    tell w to make new tab with properties {{URL:"{url}"}}')

    if create_tab_group and open_tabs:
        # Safari 15+ Tab Groups via AppleScript (macOS Monterey+)
        folder_esc = esc(folder)
        lines += [
            f'    -- Attempt to create a Tab Group (Safari 15+ / macOS Monterey+)',
            f'    try',
            f'        make new tab group at end of tab groups with properties {{name:"{folder_esc}"}}',
            f'        set tg to last tab group',
            f'        repeat with t in tabs of w',
            f'            move t to end of tabs of tg',
            f'        end repeat',
            f'    end try',
        ]

    # Bookmark each URL into a named folder
    folder_esc = esc(folder)
    lines += [
        f'    -- Create bookmark folder "{folder}" if it does not exist',
        f'    if not (exists bookmark folder "{folder_esc}" of bookmarks bar) then',
        f'        make new bookmark folder at end of bookmarks bar with properties {{name:"{folder_esc}"}}',
        f'    end if',
        f'    set bkFolder to bookmark folder "{folder_esc}" of bookmarks bar',
    ]
    for e in entries:
        url = esc(e.get("url", ""))
        title = esc(e.get("title", e.get("url", "")))
        lines.append(
            f'    make new bookmark at end of bkFolder'
            f' with properties {{name:"{title}", URL:"{url}"}}'
        )

    lines.append("end tell")
    return "\n".join(lines)


@mcp.tool()
def mac_safari_open_and_bookmark(
    urls_and_titles: str,
    folder: str = "Peacock Watches",
    open_tabs: bool = True,
    create_tab_group: bool = True,
    mac_host: str = "",
    mac_user: str = "",
    ssh_key: Optional[str] = None,
) -> str:
    """
    Open URLs in Safari on a Mac and bookmark them in a named folder.
    Works from a remote LXC or any machine by SSHing to the Mac.

    urls_and_titles: JSON array of {url, title} objects, or one URL per line.
    folder: bookmark folder name to create or reuse (default 'Peacock Watches').
    open_tabs: also open each URL as a Safari tab right now (default True).
    create_tab_group: attempt to create a Safari Tab Group (Safari 15+ / macOS Monterey+).
    mac_host: IP or hostname of the Mac. Leave empty or 'localhost' if Peacock
              is running directly on the Mac.
    mac_user: SSH username on the Mac (required when mac_host is a remote address).
    ssh_key: path to SSH private key file on this machine (optional).

    One-time Mac setup required:
      1. Enable SSH on the Mac: System Settings → General → Sharing → Remote Login → On
      2. Authorise the LXC's SSH key: ssh-copy-id mac_user@mac_host
      3. No other setup needed — osascript is built into macOS.
    """
    import json as _json

    try:
        entries = _json.loads(urls_and_titles)
        if isinstance(entries, dict):
            entries = [entries]
    except (_json.JSONDecodeError, TypeError):
        raw = [l.strip() for l in str(urls_and_titles).splitlines() if l.strip()]
        entries = [{"url": l, "title": l} for l in raw]

    if not entries:
        return "❌ No URLs provided"

    script = _build_safari_applescript(entries, folder, open_tabs, create_tab_group)

    try:
        rc, stdout, stderr = _run_on_mac(script, mac_host, mac_user, ssh_key)
    except subprocess.TimeoutExpired:
        return "❌ Timed out waiting for Safari to respond (30s)"
    except FileNotFoundError:
        return "❌ ssh not found. Install: sudo apt install openssh-client"
    except Exception as e:
        return f"❌ Failed to run on Mac: {e}"

    if rc != 0:
        return (
            f"❌ AppleScript error (exit {rc}): {stderr or stdout}\n"
            f"💡 Ensure Remote Login is enabled on the Mac:\n"
            f"   System Settings → General → Sharing → Remote Login → On\n"
            f"   Also run: ssh-copy-id {mac_user}@{mac_host}"
        )

    tab_group_note = " + Tab Group (if Safari 15+)" if create_tab_group else ""
    tab_note = f", {len(entries)} tab(s) opened{tab_group_note}" if open_tabs else ""
    return (
        f"✅ Safari: {len(entries)} URL(s) bookmarked in '{folder}'{tab_note}\n"
        + "\n".join(f"  • {e.get('title', e.get('url', ''))} — {e.get('url', '')}"
                    for e in entries)
    )


@mcp.tool()
def mac_chrome_open_and_bookmark(
    urls_and_titles: str,
    folder: str = "Peacock Watches",
    open_tabs: bool = True,
    mac_host: str = "",
    mac_user: str = "",
    ssh_key: Optional[str] = None,
) -> str:
    """
    Open URLs in Chrome on a Mac and bookmark them, using AppleScript via SSH.
    Use this when you want Mac Chrome tabs without setting up a CDP tunnel.

    urls_and_titles: JSON array of {url, title} objects, or one URL per line.
    folder: Chrome bookmark folder name (written to the Bookmarks JSON file).
    open_tabs: also open each URL as a Chrome tab right now (default True).
    mac_host: IP or hostname of the Mac (leave empty if already on the Mac).
    mac_user: SSH username on the Mac.
    ssh_key: path to SSH private key file (optional).
    """
    import json as _json

    try:
        entries = _json.loads(urls_and_titles)
        if isinstance(entries, dict):
            entries = [entries]
    except (_json.JSONDecodeError, TypeError):
        raw = [l.strip() for l in str(urls_and_titles).splitlines() if l.strip()]
        entries = [{"url": l, "title": l} for l in raw]

    if not entries:
        return "❌ No URLs provided"

    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    lines = ['tell application "Google Chrome"', "    activate"]
    if open_tabs:
        lines += [
            "    if (count of windows) = 0 then make new window",
            "    set w to window 1",
        ]
        for i, e in enumerate(entries):
            url = esc(e.get("url", ""))
            if i == 0:
                lines.append(f'    set URL of active tab of w to "{url}"')
            else:
                lines.append(f'    make new tab at end of tabs of w with properties {{URL:"{url}"}}')
    lines.append("end tell")
    open_script = "\n".join(lines)

    results = []

    if open_tabs:
        rc, stdout, stderr = _run_on_mac(open_script, mac_host, mac_user, ssh_key)
        if rc != 0:
            results.append(f"⚠️  Tab open error: {stderr or stdout}")
        else:
            results.append(f"✅ Opened {len(entries)} tab(s) in Mac Chrome")

    # Bookmark by remotely editing the Bookmarks file via Python
    bm_py = f"""
import json, time, os
from pathlib import Path

bm_path = Path.home() / 'Library/Application Support/Google/Chrome/Default/Bookmarks'
if not bm_path.exists():
    print('NOT_FOUND')
    exit(1)

with open(bm_path) as f:
    data = json.load(f)

roots = data.get('roots', {{}})
bar = roots.get('bookmark_bar', {{}})

def find_or_create(node, name):
    for c in node.get('children', []):
        if c.get('type') == 'folder' and c.get('name') == name:
            return c
    new = {{'children':[],'date_added':str(int(time.time()*1000000)),
             'date_last_used':'0','date_modified':'0',
             'guid':f'peacock-f-{{int(time.time())}}',
             'id':str(int(time.time())),'name':name,'type':'folder'}}
    node.setdefault('children',[]).append(new)
    return new

target = find_or_create(bar, {_json.dumps(folder)})
entries = {_json.dumps(entries)}

for e in entries:
    target['children'].append({{
        'date_added':str(int(time.time()*1000000)),'date_last_used':'0',
        'guid':f'peacock-bm-{{int(time.time())}}','id':str(int(time.time())),
        'name':e.get('title',e.get('url','')),'type':'url','url':e.get('url','')
    }})

data['checksum'] = ''
with open(bm_path,'w') as f:
    json.dump(data, f, indent=3)
print('OK')
"""

    bm_script = f'do shell script "python3 -c \\" + chr(10) + {repr(bm_py)} + chr(10) + \\""'
    # Simpler: run python3 directly via SSH, not through AppleScript
    if not mac_host or mac_host in ("localhost", "127.0.0.1"):
        import sys
        proc = subprocess.run([sys.executable, "-c", bm_py],
                              capture_output=True, text=True, timeout=15)
        rc2, out2 = proc.returncode, proc.stdout.strip() or proc.stderr.strip()
    else:
        ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes"]
        if ssh_key:
            ssh_cmd += ["-i", ssh_key]
        ssh_cmd.append(f"{mac_user}@{mac_host}")
        ssh_cmd += ["python3", "-"]
        proc = subprocess.run(ssh_cmd, input=bm_py, capture_output=True, text=True, timeout=15)
        rc2, out2 = proc.returncode, proc.stdout.strip() or proc.stderr.strip()

    if rc2 == 0 and "OK" in out2:
        results.append(f"✅ Bookmarked {len(entries)} URL(s) in '{folder}' (restart Chrome to see)")
    else:
        results.append(f"⚠️  Bookmark write: {out2 or 'unknown error'}")

    return "\n".join(results) + "\n" + "\n".join(
        f"  • {e.get('title', e.get('url',''))} — {e.get('url','')}" for e in entries
    )


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"🦚 PEACOCK MCP SERVER — v{VERSION} 🦚")
    print("Built by Rich Knowles")
    print(f"🖥️  Platform: {PLATFORM}")
    print(f"📁 Base directory: {BASE_DIR}")
    print(f"🌐 Browser tools: {'✅ ready' if BROWSER_AVAILABLE else '⚠️  unavailable (pip install selenium webdriver-manager websocket-client requests)'}")
    print(f"🖥️  VM tools:      {'✅ ready' if VM_AVAILABLE else '⚠️  unavailable (pip install proxmoxer requests)'}")
    print("🚀 Starting server...")
    mcp.run()
