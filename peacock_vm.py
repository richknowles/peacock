#!/usr/bin/env python3
"""
🦚 Peacock VM Control — v1.1.2
Built by Rich Knowles

Connects to Proxmox VE via its REST API.
Supports: VM inventory, start/stop, status, command execution via QEMU Guest Agent,
VNC screenshot, and launching a browser session inside a guest OS.
"""

import time
from pathlib import Path
from typing import Dict, Optional, Any

# ─── Connection Registry ──────────────────────────────────────────────────────

_connections: Dict[str, dict] = {}
_active_cid: Optional[str] = None
_cid_counter = 0


def _new_cid() -> str:
    global _cid_counter
    _cid_counter += 1
    return f"proxmox_{_cid_counter}"


def _get_conn(conn_id: Optional[str] = None) -> Optional[dict]:
    return _connections.get(conn_id or _active_cid)


def _find_node(proxmox, vm_id: int) -> Optional[str]:
    """Locate which Proxmox node hosts a given VM ID."""
    try:
        for node in proxmox.nodes.get():
            try:
                proxmox.nodes(node["node"]).qemu(vm_id).status.current.get()
                return node["node"]
            except Exception:
                continue
    except Exception:
        pass
    return None


# ─── Public Tool Implementations ──────────────────────────────────────────────

def vm_connect(host: str, username: str, password: str,
               port: int = 8006, verify_ssl: bool = False) -> str:
    """
    Connect to a Proxmox VE server.
    host: IP or hostname (without https://).
    username: e.g. root@pam or user@pve.
    Returns a connection ID used by all other vm_ tools.
    """
    global _active_cid
    try:
        from proxmoxer import ProxmoxAPI
    except ImportError:
        return "❌ proxmoxer not installed: pip install proxmoxer requests"

    host_clean = host.replace("https://", "").replace("http://", "").split(":")[0]
    try:
        proxmox = ProxmoxAPI(
            host_clean,
            port=port,
            user=username,
            password=password,
            verify_ssl=verify_ssl,
            timeout=15,
        )
        version = proxmox.version.get()
        cid = _new_cid()
        _connections[cid] = {"client": proxmox, "host": host_clean, "port": port}
        _active_cid = cid
        return (
            f"✅ Connected to Proxmox VE\n"
            f"🖥️  Host: {host_clean}:{port}\n"
            f"📦 PVE version: {version.get('version', 'unknown')}\n"
            f"🔑 Connection ID: {cid}"
        )
    except Exception as e:
        return f"❌ Proxmox connection failed: {e}"


def vm_list(conn_id: Optional[str] = None) -> str:
    """List all virtual machines across all nodes on the connected Proxmox server."""
    conn = _get_conn(conn_id)
    if not conn:
        return "❌ No Proxmox connection. Run vm_connect first."
    proxmox = conn["client"]
    try:
        nodes = proxmox.nodes.get()
        lines = [f"🖥️  VMs on {conn['host']}:"]
        total = 0
        for node in nodes:
            name = node["node"]
            try:
                for vm in proxmox.nodes(name).qemu.get():
                    total += 1
                    icon = "🟢" if vm.get("status") == "running" else "🔴"
                    ram_mb = vm.get("maxmem", 0) // 1024 // 1024
                    lines.append(
                        f"  {icon} [{vm['vmid']}] {vm.get('name', 'unnamed')} "
                        f"| {vm.get('status', '?')} | node:{name} "
                        f"| {vm.get('cpus', '?')} vCPU | {ram_mb}MB RAM"
                    )
            except Exception:
                pass
        lines.append(f"\n📊 Total: {total} VMs")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ vm_list failed: {e}"


def vm_status(vm_id: int, node: Optional[str] = None, conn_id: Optional[str] = None) -> str:
    """Get detailed runtime status of a specific VM."""
    conn = _get_conn(conn_id)
    if not conn:
        return "❌ No Proxmox connection."
    proxmox = conn["client"]
    node = node or _find_node(proxmox, vm_id)
    if not node:
        return f"❌ VM {vm_id} not found on any node"
    try:
        s = proxmox.nodes(node).qemu(vm_id).status.current.get()
        cpu_pct = s.get("cpu", 0) * 100
        ram_used = s.get("mem", 0) // 1024 // 1024
        ram_max = s.get("maxmem", 0) // 1024 // 1024
        return (
            f"📊 VM {vm_id} — {s.get('name', 'unnamed')}\n"
            f"  Status:  {s.get('status', '?')}\n"
            f"  Node:    {node}\n"
            f"  CPU:     {cpu_pct:.1f}% across {s.get('cpus', 1)} vCPUs\n"
            f"  RAM:     {ram_used}MB / {ram_max}MB\n"
            f"  Uptime:  {s.get('uptime', 0)}s"
        )
    except Exception as e:
        return f"❌ vm_status failed: {e}"


def vm_start(vm_id: int, node: Optional[str] = None, conn_id: Optional[str] = None) -> str:
    """Start a stopped or paused VM."""
    conn = _get_conn(conn_id)
    if not conn:
        return "❌ No Proxmox connection."
    proxmox = conn["client"]
    node = node or _find_node(proxmox, vm_id)
    if not node:
        return f"❌ VM {vm_id} not found"
    try:
        task = proxmox.nodes(node).qemu(vm_id).status.start.post()
        return f"✅ VM {vm_id} starting on node {node}. Task: {task}"
    except Exception as e:
        return f"❌ vm_start failed: {e}"


def vm_stop(vm_id: int, force: bool = False,
             node: Optional[str] = None, conn_id: Optional[str] = None) -> str:
    """
    Stop a VM.
    force=False: graceful ACPI shutdown (recommended).
    force=True: immediate power-off (data loss risk).
    """
    conn = _get_conn(conn_id)
    if not conn:
        return "❌ No Proxmox connection."
    proxmox = conn["client"]
    node = node or _find_node(proxmox, vm_id)
    if not node:
        return f"❌ VM {vm_id} not found"
    try:
        if force:
            task = proxmox.nodes(node).qemu(vm_id).status.stop.post()
            return f"⚡ VM {vm_id} force-stopped. Task: {task}"
        else:
            task = proxmox.nodes(node).qemu(vm_id).status.shutdown.post()
            return f"✅ VM {vm_id} shutting down gracefully. Task: {task}"
    except Exception as e:
        return f"❌ vm_stop failed: {e}"


def vm_screenshot(vm_id: int, save_path: Optional[str] = None,
                   node: Optional[str] = None, conn_id: Optional[str] = None) -> str:
    """
    Capture a screenshot of a running VM's display via the Proxmox VNC proxy.
    Requires vncdotool: pip install vncdotool
    Returns the path to the saved PNG file.
    """
    conn = _get_conn(conn_id)
    if not conn:
        return "❌ No Proxmox connection."
    proxmox = conn["client"]
    node = node or _find_node(proxmox, vm_id)
    if not node:
        return f"❌ VM {vm_id} not found"

    if not save_path:
        save_path = str(Path.home() / f"peacock_vm{vm_id}_{int(time.time())}.png")

    try:
        vnc = proxmox.nodes(node).qemu(vm_id).vncproxy.post(websocket=0)
        vnc_port = vnc.get("port")
        vnc_ticket = vnc.get("ticket")
    except Exception as e:
        return f"❌ Could not obtain VNC proxy from Proxmox: {e}"

    try:
        from vncdotool import api as vnc_api
        client = vnc_api.connect(conn["host"], password=vnc_ticket, port=int(vnc_port))
        client.captureScreen(save_path)
        client.disconnect()
        return f"✅ VM {vm_id} screenshot saved: {save_path}"
    except ImportError:
        return (
            f"⚠️  vncdotool not installed: pip install vncdotool\n"
            f"VNC details — host: {conn['host']}, port: {vnc_port}\n"
            f"You can connect manually with any VNC client using the ticket as the password."
        )
    except Exception as e:
        return f"❌ VNC screenshot failed: {e}"


def vm_execute(vm_id: int, command: str, timeout: int = 30,
                node: Optional[str] = None, conn_id: Optional[str] = None) -> str:
    """
    Execute a shell command inside a running VM via the QEMU Guest Agent.
    Requires qemu-guest-agent installed and running inside the guest OS.
    """
    conn = _get_conn(conn_id)
    if not conn:
        return "❌ No Proxmox connection."
    proxmox = conn["client"]
    node = node or _find_node(proxmox, vm_id)
    if not node:
        return f"❌ VM {vm_id} not found"
    try:
        result = proxmox.nodes(node).qemu(vm_id).agent.exec.post(**{"command": command})
        pid = result.get("pid")
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(1)
            try:
                status = proxmox.nodes(node).qemu(vm_id).agent("exec-status").get(pid=pid)
                if status.get("exited"):
                    out = status.get("out-data", "")
                    err = status.get("err-data", "")
                    rc = status.get("exitcode", -1)
                    parts = [f"✅ VM {vm_id} command executed | exit code: {rc}"]
                    if out:
                        parts.append(f"STDOUT:\n{out}")
                    if err:
                        parts.append(f"STDERR:\n{err}")
                    return "\n".join(parts)
            except Exception:
                continue
        return f"⏱️ Command submitted (PID {pid}) but did not complete within {timeout}s"
    except Exception as e:
        return (
            f"❌ vm_execute failed: {e}\n"
            f"💡 Ensure qemu-guest-agent is installed and running in the guest OS."
        )


def vm_browser_open(vm_id: int, url: str, browser: str = "chrome",
                     node: Optional[str] = None, conn_id: Optional[str] = None) -> str:
    """
    Launch a browser inside a VM and open a URL.
    Uses the QEMU Guest Agent to run the browser command.
    Supports chrome, firefox, edge (Windows/Linux).
    """
    cmds: Dict[str, Dict[str, str]] = {
        "chrome": {
            "linux": f'google-chrome --new-window "{url}" &',
            "windows": f'cmd /c start chrome "{url}"',
        },
        "firefox": {
            "linux": f'firefox "{url}" &',
            "windows": f'cmd /c start firefox "{url}"',
        },
        "edge": {
            "windows": f'cmd /c start msedge "{url}"',
            "linux": f'microsoft-edge "{url}" &',
        },
    }
    browser = browser.lower()
    browser_cmds = cmds.get(browser, cmds["chrome"])

    # Try Linux first, then Windows
    for os_type in ("linux", "windows"):
        cmd = browser_cmds.get(os_type)
        if not cmd:
            continue
        result = vm_execute(vm_id, cmd, timeout=10, node=node, conn_id=conn_id)
        if "✅" in result or "exit code: 0" in result:
            return f"✅ {browser} opened in VM {vm_id}: {url}"

    return f"❌ Could not open {browser} in VM {vm_id}. Is the guest agent running and {browser} installed?"


def vm_list_connections() -> str:
    """List all active Proxmox connections."""
    if not _connections:
        return "📭 No active Proxmox connections. Run vm_connect first."
    lines = ["🖥️  Proxmox Connections:"]
    for cid, c in _connections.items():
        marker = " ← active" if cid == _active_cid else ""
        lines.append(f"  • {cid} | {c['host']}:{c['port']}{marker}")
    return "\n".join(lines)


def vm_disconnect(conn_id: Optional[str] = None) -> str:
    """Disconnect from Proxmox (frees the connection entry)."""
    global _active_cid
    cid = conn_id or _active_cid
    if cid not in _connections:
        return f"❌ Connection not found: {cid}"
    del _connections[cid]
    if cid == _active_cid:
        _active_cid = next(iter(_connections), None)
    return f"✅ Disconnected: {cid}"
