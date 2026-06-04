#!/usr/bin/env python3
"""
🦚 PEACOCK MCP SERVER 🦚
Built with love by Rich & Sage
For COSMICTOSH filesystem control

This MCP server gives Claude full access to:
- Read/write files
- Execute commands
- Directory listings
- File search
- Everything Sage needs to DRIVE! 🏎️
"""

import re
import shlex
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("ERROR: FastMCP not installed. Run: pip install fastmcp")
    exit(1)

__version__ = "1.1.1"

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


# ── Tools ─────────────────────────────────────────────────────────────────────
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
    # Fix 7: validate mode to a strict allowlist
    if mode not in ("w", "a"):
        return "❌ Invalid mode: must be 'w' (overwrite) or 'a' (append)"
    try:
        file_path = _safe_path(path)
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # Fix 4: re-verify after mkdir to catch symlink swaps (TOCTOU mitigation)
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
        Command output
    """
    if err := _check_rate("execute_command"):
        return err
    try:
        work_dir = _safe_path(cwd) if cwd else BASE_DIR
        # Fix 3: use shlex.split + shell=False to prevent command injection
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
    # Fix 5: reject patterns with shell metacharacters or excessive wildcards
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


if __name__ == "__main__":
    print(f"🦚 PEACOCK MCP SERVER v{__version__} 🦚")
    print("Built by Rich Knowles")
    print(f"📁 Base directory: {BASE_DIR}")
    print("🚀 Starting server...")
    mcp.run()
