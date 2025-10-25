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

import os
import subprocess
import json
from pathlib import Path
from typing import Any, Optional
import asyncio

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("ERROR: FastMCP not installed. Run: pip install fastmcp")
    exit(1)

# Initialize the MCP server
mcp = FastMCP("Peacock")

# Base directory for file operations (configurable)
BASE_DIR = Path.home()


@mcp.tool()
def read_file(path: str) -> str:
    """
    Read the contents of a file.
    
    Args:
        path: Absolute or relative path to the file
    
    Returns:
        File contents as string
    """
    try:
        file_path = Path(path).expanduser().resolve()
        
        # Security check - ensure we're not going outside allowed areas
        if not str(file_path).startswith(str(BASE_DIR)):
            return f"❌ Access denied: {path} is outside allowed directory"
        
        if not file_path.exists():
            return f"❌ File not found: {path}"
        
        if not file_path.is_file():
            return f"❌ Not a file: {path}"
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return f"✅ Read {len(content)} bytes from {path}\n\n{content}"
    
    except Exception as e:
        return f"❌ Error reading file: {str(e)}"


@mcp.tool()
def write_file(path: str, content: str, mode: str = "w") -> str:
    """
    Write content to a file.
    
    Args:
        path: Absolute or relative path to the file
        content: Content to write
        mode: Write mode ('w' for overwrite, 'a' for append)
    
    Returns:
        Success/failure message
    """
    try:
        file_path = Path(path).expanduser().resolve()
        
        # Security check
        if not str(file_path).startswith(str(BASE_DIR)):
            return f"❌ Access denied: {path} is outside allowed directory"
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, mode, encoding='utf-8') as f:
            f.write(content)
        
        return f"✅ Wrote {len(content)} bytes to {path}"
    
    except Exception as e:
        return f"❌ Error writing file: {str(e)}"


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
    try:
        dir_path = Path(path).expanduser().resolve()
        
        # Security check
        if not str(dir_path).startswith(str(BASE_DIR)):
            return f"❌ Access denied: {path} is outside allowed directory"
        
        if not dir_path.exists():
            return f"❌ Directory not found: {path}"
        
        if not dir_path.is_dir():
            return f"❌ Not a directory: {path}"
        
        items = []
        for item in sorted(dir_path.iterdir()):
            # Skip hidden files if requested
            if not show_hidden and item.name.startswith('.'):
                continue
            
            if item.is_dir():
                items.append(f"📁 {item.name}/")
            else:
                size = item.stat().st_size
                items.append(f"📄 {item.name} ({size} bytes)")
        
        if not items:
            return f"📂 {dir_path} is empty"
        
        return f"📂 {dir_path}\n\n" + "\n".join(items)
    
    except Exception as e:
        return f"❌ Error listing directory: {str(e)}"


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
    try:
        if cwd:
            work_dir = Path(cwd).expanduser().resolve()
        else:
            work_dir = BASE_DIR
        
        # Security check
        if not str(work_dir).startswith(str(BASE_DIR)):
            return f"❌ Access denied: working directory outside allowed area"
        
        # Execute command
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        output = []
        output.append(f"🦚 Executed: {command}")
        output.append(f"📍 Working directory: {work_dir}")
        output.append(f"↩️  Exit code: {result.returncode}")
        
        if result.stdout:
            output.append(f"\n📤 STDOUT:\n{result.stdout}")
        
        if result.stderr:
            output.append(f"\n📤 STDERR:\n{result.stderr}")
        
        return "\n".join(output)
    
    except subprocess.TimeoutExpired:
        return f"❌ Command timed out after 30 seconds"
    except Exception as e:
        return f"❌ Error executing command: {str(e)}"


@mcp.tool()
def search_files(pattern: str, directory: str = ".", max_results: int = 50) -> str:
    """
    Search for files matching a pattern.
    
    Args:
        pattern: Glob pattern (e.g., "*.py", "test_*.txt")
        directory: Directory to search in
        max_results: Maximum number of results
    
    Returns:
        List of matching files
    """
    try:
        search_dir = Path(directory).expanduser().resolve()
        
        # Security check
        if not str(search_dir).startswith(str(BASE_DIR)):
            return f"❌ Access denied: {directory} is outside allowed directory"
        
        if not search_dir.exists():
            return f"❌ Directory not found: {directory}"
        
        matches = []
        for path in search_dir.rglob(pattern):
            if len(matches) >= max_results:
                matches.append(f"... and more (limit: {max_results})")
                break
            
            relative = path.relative_to(search_dir)
            if path.is_dir():
                matches.append(f"📁 {relative}/")
            else:
                matches.append(f"📄 {relative}")
        
        if not matches:
            return f"❌ No files matching '{pattern}' found in {directory}"
        
        return f"🔍 Found {len(matches)} matches for '{pattern}':\n\n" + "\n".join(matches)
    
    except Exception as e:
        return f"❌ Error searching files: {str(e)}"


@mcp.tool()
def get_file_info(path: str) -> str:
    """
    Get detailed information about a file or directory.
    
    Args:
        path: Path to file or directory
    
    Returns:
        Detailed file information
    """
    try:
        file_path = Path(path).expanduser().resolve()
        
        # Security check
        if not str(file_path).startswith(str(BASE_DIR)):
            return f"❌ Access denied: {path} is outside allowed directory"
        
        if not file_path.exists():
            return f"❌ Path not found: {path}"
        
        stat = file_path.stat()
        
        info = []
        info.append(f"📋 File Information: {file_path}")
        info.append(f"Type: {'📁 Directory' if file_path.is_dir() else '📄 File'}")
        info.append(f"Size: {stat.st_size} bytes")
        info.append(f"Modified: {stat.st_mtime}")
        info.append(f"Permissions: {oct(stat.st_mode)[-3:]}")
        
        if file_path.is_file():
            info.append(f"Extension: {file_path.suffix}")
        
        return "\n".join(info)
    
    except Exception as e:
        return f"❌ Error getting file info: {str(e)}"


if __name__ == "__main__":
    print("🦚 PEACOCK MCP SERVER 🦚")
    print("Let's Drive!")
    print(f"📁 Base directory: {BASE_DIR}")
    print("🚀 Starting server...")
    
    # Run the server
    mcp.run()
