#!/usr/bin/env python3
"""
🦚 Peacock Browser Automation — v1.1.2
Built by Rich Knowles

Chrome: attaches to a running instance via CDP (zero launch overhead).
Firefox / Safari / Edge: driven via Selenium WebDriver.
Works on macOS, Linux, and Windows.
"""

import base64
import json
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

PLATFORM = platform.system()  # 'Darwin' | 'Linux' | 'Windows'

# ─── Session Registry ─────────────────────────────────────────────────────────

class BrowserSession:
    def __init__(self, session_id: str, browser: str, mode: str):
        self.session_id = session_id
        self.browser = browser    # chrome | firefox | safari | edge
        self.mode = mode          # cdp | selenium
        self.driver = None        # selenium WebDriver
        self.cdp: Optional["CDPSession"] = None
        self.cdp_port: int = 9222

    def close(self):
        if self.cdp:
            try:
                self.cdp.close()
            except Exception:
                pass
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass


_sessions: Dict[str, BrowserSession] = {}
_active_sid: Optional[str] = None
_sid_counter = 0


def _new_sid() -> str:
    global _sid_counter
    _sid_counter += 1
    return f"peacock_{_sid_counter}"


def _get_session(session_id: Optional[str] = None) -> Optional[BrowserSession]:
    return _sessions.get(session_id or _active_sid)


# ─── CDP (Chrome DevTools Protocol) ──────────────────────────────────────────

class CDPSession:
    """Persistent WebSocket channel to one Chrome tab."""

    def __init__(self, ws_url: str):
        try:
            import websocket as _ws
        except ImportError:
            raise RuntimeError("websocket-client is not installed: pip install websocket-client")
        self._ws = _ws.create_connection(ws_url, timeout=15)
        self._id = 0
        self._ws_url = ws_url

    def send(self, method: str, params: dict = None) -> dict:
        self._id += 1
        mid = self._id
        self._ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        for _ in range(100):
            try:
                msg = json.loads(self._ws.recv())
                if msg.get("id") == mid:
                    if "error" in msg:
                        raise RuntimeError(f"CDP error: {msg['error']}")
                    return msg.get("result", {})
            except (json.JSONDecodeError, OSError):
                break
        return {}

    def close(self):
        try:
            self._ws.close()
        except Exception:
            pass


def _cdp_tabs(port: int = 9222) -> List[dict]:
    try:
        import requests
        r = requests.get(f"http://localhost:{port}/json", timeout=3)
        return [t for t in r.json() if t.get("type") == "page"]
    except Exception:
        return []


def _launch_chrome_cdp(port: int = 9222, url: str = "about:blank") -> bool:
    """Launch Chrome with remote-debugging enabled, wait until it responds."""
    exe = _chrome_exe()
    if not exe:
        return False
    profile = Path.home() / ".peacock_chrome"
    cmd = [
        exe,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--no-default-browser-check",
        url,
    ]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):
        time.sleep(0.5)
        if _cdp_tabs(port):
            return True
    return False


# ─── Platform Chrome Paths ────────────────────────────────────────────────────

_CHROME_PATHS = {
    "Darwin": [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
    ],
    "Linux": [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/snap/bin/chromium",
    ],
    "Windows": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
    ],
}


def _chrome_exe() -> Optional[str]:
    for p in _CHROME_PATHS.get(PLATFORM, _CHROME_PATHS["Linux"]):
        if os.path.exists(p):
            return p
    for cmd in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"]:
        found = shutil.which(cmd)
        if found:
            return found
    return None


# ─── Chrome Bookmarks ─────────────────────────────────────────────────────────

def _chrome_bookmarks_path() -> Optional[Path]:
    paths = {
        "Darwin": Path.home() / "Library/Application Support/Google/Chrome/Default/Bookmarks",
        "Linux": Path.home() / ".config/google-chrome/Default/Bookmarks",
        "Windows": Path(os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Bookmarks")),
    }
    p = paths.get(PLATFORM)
    return p if p and p.exists() else None


def _add_chrome_bookmark(url: str, title: str, folder_name: str) -> str:
    """Write a bookmark directly into Chrome's Bookmarks JSON file."""
    bm_path = _chrome_bookmarks_path()
    if not bm_path:
        return "❌ Chrome Bookmarks file not found. Is Chrome installed and has it been opened at least once?"

    with open(bm_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    roots = data.get("roots", {})

    def _find_or_create_folder(root_node: dict, name: str) -> dict:
        for child in root_node.get("children", []):
            if child.get("type") == "folder" and child.get("name") == name:
                return child
        new_folder = {
            "children": [],
            "date_added": str(int(time.time() * 1000000)),
            "date_last_used": "0",
            "date_modified": "0",
            "guid": f"peacock-folder-{int(time.time())}",
            "id": str(int(time.time())),
            "name": name,
            "type": "folder",
        }
        root_node.setdefault("children", []).append(new_folder)
        return new_folder

    bar = roots.get("bookmark_bar", {})

    if folder_name.lower() in ("bookmarks bar", "bookmark_bar", ""):
        target = bar
    else:
        target = _find_or_create_folder(bar, folder_name)

    target.setdefault("children", []).append({
        "date_added": str(int(time.time() * 1000000)),
        "date_last_used": "0",
        "guid": f"peacock-bm-{int(time.time())}",
        "id": str(int(time.time())),
        "name": title or url,
        "type": "url",
        "url": url,
    })

    # Clear checksum so Chrome recomputes it on next launch
    data["checksum"] = ""

    with open(bm_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=3, ensure_ascii=False)

    return f'✅ Bookmarked "{title or url}" in "{folder_name or "Bookmarks bar"}"\n⚠️  Restart Chrome to see new bookmarks.'


# ─── Selenium WebDriver Factory ───────────────────────────────────────────────

def _selenium_driver(browser: str, headless: bool = False):
    try:
        from selenium import webdriver as wd
    except ImportError:
        raise RuntimeError("selenium not installed: pip install selenium webdriver-manager")

    browser = browser.lower()

    if browser in ("chrome", "chromium"):
        from selenium.webdriver.chrome.options import Options
        opts = Options()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            return wd.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
        except ImportError:
            return wd.Chrome(options=opts)

    elif browser == "firefox":
        from selenium.webdriver.firefox.options import Options
        opts = Options()
        if headless:
            opts.add_argument("--headless")
        try:
            from webdriver_manager.firefox import GeckoDriverManager
            from selenium.webdriver.firefox.service import Service
            return wd.Firefox(service=Service(GeckoDriverManager().install()), options=opts)
        except ImportError:
            return wd.Firefox(options=opts)

    elif browser == "safari":
        if PLATFORM != "Darwin":
            raise RuntimeError("Safari WebDriver is macOS-only. Run: safaridriver --enable")
        return wd.Safari()

    elif browser in ("edge", "msedge"):
        from selenium.webdriver.edge.options import Options
        opts = Options()
        if headless:
            opts.add_argument("--headless=new")
        try:
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            from selenium.webdriver.edge.service import Service
            return wd.Edge(service=Service(EdgeChromiumDriverManager().install()), options=opts)
        except ImportError:
            return wd.Edge(options=opts)

    raise ValueError(f"Unknown browser: {browser}. Choose: chrome, firefox, safari, edge")


# ─── Public Tool Implementations ──────────────────────────────────────────────

def browser_open(url: str, browser: str = "chrome", headless: bool = False,
                 attach: bool = True, cdp_port: int = 9222) -> str:
    """
    Open a browser and navigate to a URL.
    For Chrome: attaches to a running instance first (fastest — no launch delay).
    If Chrome is not running, launches it with CDP remote-debugging enabled.
    Falls back to Selenium for Firefox, Safari, and Edge.
    Returns a session_id for use with other browser tools.
    """
    global _active_sid
    browser = browser.lower()
    sid = _new_sid()

    if browser in ("chrome", "chromium") and attach:
        tabs = _cdp_tabs(cdp_port)
        if not tabs:
            _launch_chrome_cdp(cdp_port, url)
            tabs = _cdp_tabs(cdp_port)

        if tabs:
            ws_url = tabs[0]["webSocketDebuggerUrl"]
            cdp = CDPSession(ws_url)
            cdp.send("Page.navigate", {"url": url})
            cdp.send("Page.bringToFront")

            session = BrowserSession(sid, browser, "cdp")
            session.cdp = cdp
            session.cdp_port = cdp_port
            _sessions[sid] = session
            _active_sid = sid
            return f"✅ Chrome attached via CDP | session: {sid}\n🌐 {url}"

    try:
        drv = _selenium_driver(browser, headless)
        drv.get(url)
        session = BrowserSession(sid, browser, "selenium")
        session.driver = drv
        _sessions[sid] = session
        _active_sid = sid
        return f"✅ {browser} launched via Selenium | session: {sid}\n🌐 {url}"
    except Exception as e:
        return f"❌ Failed to open {browser}: {e}"


def browser_navigate(url: str, session_id: Optional[str] = None) -> str:
    """Navigate the active tab to a URL."""
    s = _get_session(session_id)
    if not s:
        return "❌ No active browser session. Run browser_open first."
    try:
        if s.mode == "cdp":
            s.cdp.send("Page.navigate", {"url": url})
        else:
            s.driver.get(url)
        return f"✅ Navigated to {url}"
    except Exception as e:
        return f"❌ Navigate failed: {e}"


def browser_new_tab(url: str = "about:blank", session_id: Optional[str] = None) -> str:
    """Open a new browser tab and navigate to a URL."""
    s = _get_session(session_id)
    if not s:
        return "❌ No active browser session."
    try:
        if s.mode == "cdp":
            import requests
            r = requests.put(f"http://localhost:{s.cdp_port}/json/new", timeout=5)
            tab = r.json()
            if url and url != "about:blank":
                cdp = CDPSession(tab["webSocketDebuggerUrl"])
                cdp.send("Page.navigate", {"url": url})
                cdp.close()
            return f"✅ New tab opened: {url}"
        else:
            s.driver.execute_script(f'window.open("{url}", "_blank");')
            s.driver.switch_to.window(s.driver.window_handles[-1])
            return f"✅ New tab opened: {url}"
    except Exception as e:
        return f"❌ New tab failed: {e}"


def browser_close_tab(session_id: Optional[str] = None) -> str:
    """Close the current tab (keeps the browser open)."""
    s = _get_session(session_id)
    if not s:
        return "❌ No active browser session."
    try:
        if s.mode == "cdp":
            tabs = _cdp_tabs(s.cdp_port)
            if tabs:
                tab_id = tabs[0]["id"]
                import requests
                requests.get(f"http://localhost:{s.cdp_port}/json/close/{tab_id}", timeout=5)
                tabs_remaining = _cdp_tabs(s.cdp_port)
                if tabs_remaining:
                    s.cdp = CDPSession(tabs_remaining[0]["webSocketDebuggerUrl"])
            return "✅ Tab closed"
        else:
            s.driver.close()
            if s.driver.window_handles:
                s.driver.switch_to.window(s.driver.window_handles[-1])
            return "✅ Tab closed"
    except Exception as e:
        return f"❌ Close tab failed: {e}"


def browser_screenshot(save_path: Optional[str] = None, session_id: Optional[str] = None) -> str:
    """Take a screenshot of the current browser tab. Returns the saved file path."""
    s = _get_session(session_id)
    if not s:
        return "❌ No active browser session."
    if not save_path:
        save_path = str(Path.home() / f"peacock_screenshot_{int(time.time())}.png")
    try:
        if s.mode == "cdp":
            result = s.cdp.send("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
            raw = result.get("data", "")
            if not raw:
                return "❌ Screenshot returned no data"
            with open(save_path, "wb") as f:
                f.write(base64.b64decode(raw))
        else:
            s.driver.save_screenshot(save_path)
        return f"✅ Screenshot saved: {save_path}"
    except Exception as e:
        return f"❌ Screenshot failed: {e}"


def browser_click(selector: str, session_id: Optional[str] = None) -> str:
    """Click a page element by CSS selector."""
    s = _get_session(session_id)
    if not s:
        return "❌ No active browser session."
    try:
        if s.mode == "cdp":
            result = s.cdp.send("Runtime.evaluate", {
                "expression": f"""
                    (function() {{
                        var el = document.querySelector({json.dumps(selector)});
                        if (!el) return 'NOT_FOUND';
                        el.click();
                        return 'OK';
                    }})()
                """,
                "returnByValue": True,
            })
            if result.get("result", {}).get("value") == "NOT_FOUND":
                return f"❌ Element not found: {selector}"
        else:
            from selenium.webdriver.common.by import By
            s.driver.find_element(By.CSS_SELECTOR, selector).click()
        return f"✅ Clicked: {selector}"
    except Exception as e:
        return f"❌ Click failed: {e}"


def browser_type(selector: str, text: str, session_id: Optional[str] = None) -> str:
    """Type text into a page element found by CSS selector."""
    s = _get_session(session_id)
    if not s:
        return "❌ No active browser session."
    try:
        if s.mode == "cdp":
            result = s.cdp.send("Runtime.evaluate", {
                "expression": f"""
                    (function() {{
                        var el = document.querySelector({json.dumps(selector)});
                        if (!el) return 'NOT_FOUND';
                        el.focus();
                        el.value = {json.dumps(text)};
                        el.dispatchEvent(new Event('input', {{bubbles: true}}));
                        el.dispatchEvent(new Event('change', {{bubbles: true}}));
                        return 'OK';
                    }})()
                """,
                "returnByValue": True,
            })
            if result.get("result", {}).get("value") == "NOT_FOUND":
                return f"❌ Element not found: {selector}"
        else:
            from selenium.webdriver.common.by import By
            el = s.driver.find_element(By.CSS_SELECTOR, selector)
            el.clear()
            el.send_keys(text)
        return f"✅ Typed into: {selector}"
    except Exception as e:
        return f"❌ Type failed: {e}"


def browser_get_content(session_id: Optional[str] = None) -> str:
    """Return the current page title, URL, and full HTML source."""
    s = _get_session(session_id)
    if not s:
        return "❌ No active browser session."
    try:
        if s.mode == "cdp":
            title_r = s.cdp.send("Runtime.evaluate", {"expression": "document.title", "returnByValue": True})
            url_r = s.cdp.send("Runtime.evaluate", {"expression": "location.href", "returnByValue": True})
            html_r = s.cdp.send("Runtime.evaluate", {"expression": "document.documentElement.outerHTML", "returnByValue": True})
            title = title_r.get("result", {}).get("value", "")
            url = url_r.get("result", {}).get("value", "")
            html = html_r.get("result", {}).get("value", "")
        else:
            title = s.driver.title
            url = s.driver.current_url
            html = s.driver.page_source
        preview = (html[:2000] + "\n... [truncated]") if len(html) > 2000 else html
        return f"📄 Title: {title}\n🌐 URL: {url}\n📏 {len(html)} chars\n\n{preview}"
    except Exception as e:
        return f"❌ Get content failed: {e}"


def browser_get_text(selector: Optional[str] = None, session_id: Optional[str] = None) -> str:
    """Return the visible text of the page or a specific element."""
    s = _get_session(session_id)
    if not s:
        return "❌ No active browser session."
    try:
        if s.mode == "cdp":
            expr = (
                f"document.querySelector({json.dumps(selector)})?.innerText"
                if selector else "document.body.innerText"
            )
            result = s.cdp.send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
            text = result.get("result", {}).get("value") or ""
        else:
            from selenium.webdriver.common.by import By
            if selector:
                text = s.driver.find_element(By.CSS_SELECTOR, selector).text
            else:
                text = s.driver.find_element(By.TAG_NAME, "body").text
        return f"📝 Text ({len(text)} chars):\n{text}"
    except Exception as e:
        return f"❌ Get text failed: {e}"


def browser_scroll(direction: str = "down", pixels: int = 500, session_id: Optional[str] = None) -> str:
    """Scroll the page. direction: up | down | left | right."""
    s = _get_session(session_id)
    if not s:
        return "❌ No active browser session."
    dy = pixels if direction == "down" else (-pixels if direction == "up" else 0)
    dx = pixels if direction == "right" else (-pixels if direction == "left" else 0)
    script = f"window.scrollBy({dx}, {dy})"
    try:
        if s.mode == "cdp":
            s.cdp.send("Runtime.evaluate", {"expression": script})
        else:
            s.driver.execute_script(script)
        return f"✅ Scrolled {direction} {pixels}px"
    except Exception as e:
        return f"❌ Scroll failed: {e}"


def browser_execute_js(script: str, session_id: Optional[str] = None) -> str:
    """Execute arbitrary JavaScript in the current page context and return the result."""
    s = _get_session(session_id)
    if not s:
        return "❌ No active browser session."
    try:
        if s.mode == "cdp":
            result = s.cdp.send("Runtime.evaluate", {
                "expression": script,
                "returnByValue": True,
                "awaitPromise": True,
            })
            value = result.get("result", {}).get("value")
        else:
            value = s.driver.execute_script(f"return ({script})")
        return f"✅ Result: {json.dumps(value, default=str)}"
    except Exception as e:
        return f"❌ JS failed: {e}"


def browser_wait_for(selector: str, timeout: int = 10, session_id: Optional[str] = None) -> str:
    """Wait until a CSS selector appears on the page (polls every 300ms)."""
    s = _get_session(session_id)
    if not s:
        return "❌ No active browser session."
    try:
        if s.mode == "cdp":
            deadline = time.time() + timeout
            while time.time() < deadline:
                result = s.cdp.send("Runtime.evaluate", {
                    "expression": f"!!document.querySelector({json.dumps(selector)})",
                    "returnByValue": True,
                })
                if result.get("result", {}).get("value"):
                    return f"✅ Element ready: {selector}"
                time.sleep(0.3)
            return f"⏱️ Timeout after {timeout}s — element not found: {selector}"
        else:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            WebDriverWait(s.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return f"✅ Element ready: {selector}"
    except Exception as e:
        return f"❌ Wait failed: {e}"


def browser_list_tabs(session_id: Optional[str] = None) -> str:
    """List all open tabs in the current browser session."""
    s = _get_session(session_id)
    if not s:
        return "❌ No active browser session."
    try:
        if s.mode == "cdp":
            tabs = _cdp_tabs(s.cdp_port)
            if not tabs:
                return "📭 No open tabs"
            lines = [f"📑 Open tabs ({len(tabs)}):"]
            for i, t in enumerate(tabs):
                lines.append(f"  {i+1}. {t.get('title', 'Untitled')} — {t.get('url', '')}")
            return "\n".join(lines)
        else:
            cur = s.driver.current_window_handle
            handles = s.driver.window_handles
            lines = [f"📑 Open tabs ({len(handles)}):"]
            for i, h in enumerate(handles):
                s.driver.switch_to.window(h)
                marker = " ← active" if h == cur else ""
                lines.append(f"  {i+1}. {s.driver.title} — {s.driver.current_url}{marker}")
            s.driver.switch_to.window(cur)
            return "\n".join(lines)
    except Exception as e:
        return f"❌ List tabs failed: {e}"


def browser_list_sessions() -> str:
    """List all active Peacock browser sessions."""
    if not _sessions:
        return "📭 No active browser sessions"
    lines = ["🦚 Browser Sessions:"]
    for sid, s in _sessions.items():
        marker = " ← active" if sid == _active_sid else ""
        lines.append(f"  • {sid} | {s.browser} ({s.mode}){marker}")
    return "\n".join(lines)


def browser_close(session_id: Optional[str] = None) -> str:
    """Close a browser session and free its resources."""
    global _active_sid
    sid = session_id or _active_sid
    session = _sessions.pop(sid, None)
    if not session:
        return f"❌ Session not found: {sid}"
    session.close()
    if sid == _active_sid:
        _active_sid = next(iter(_sessions), None)
    return f"✅ Session closed: {sid}"


def browser_bookmark_add(url: str, title: str = "", folder: str = "Peacock Watches",
                          browser: str = "chrome", session_id: Optional[str] = None) -> str:
    """
    Add a bookmark.
    Chrome: writes directly to the Bookmarks JSON file (restart Chrome to see it).
    Firefox: opens the bookmark dialog via keyboard shortcut.
    Safari (macOS): adds to Reading List.
    """
    s = _get_session(session_id)
    bname = s.browser if s else browser.lower()

    if bname in ("chrome", "chromium"):
        return _add_chrome_bookmark(url, title, folder)

    elif bname == "safari" and PLATFORM == "Darwin":
        try:
            script = f'tell application "Safari" to add reading list item "{url}"'
            subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
            return f"✅ Added to Safari Reading List: {url}"
        except Exception as e:
            return f"❌ Safari bookmark failed: {e}"

    elif bname == "firefox" and s and s.driver:
        try:
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.common.action_chains import ActionChains
            modifier = Keys.COMMAND if PLATFORM == "Darwin" else Keys.CONTROL
            ActionChains(s.driver).key_down(modifier).send_keys("d").key_up(modifier).perform()
            time.sleep(0.8)
            return f"✅ Firefox bookmark dialog opened for {url}\n⚠️  Confirm the dialog that appeared in Firefox."
        except Exception as e:
            return f"❌ Firefox bookmark failed: {e}"

    return f"⚠️ Bookmarks not yet supported for {bname} on {PLATFORM}. Chrome is recommended."


def browser_bookmark_group(urls_and_titles: str, folder: str = "Peacock Watches",
                            browser: str = "chrome", session_id: Optional[str] = None) -> str:
    """
    Bookmark a group of URLs into a named folder in one call.
    urls_and_titles: JSON array of {url, title} objects, or one URL per line.
    Example JSON: [{"url": "https://example.com", "title": "Example"}, ...]
    Creates the folder if it does not exist.
    """
    try:
        entries = json.loads(urls_and_titles)
        if isinstance(entries, dict):
            entries = [entries]
    except (json.JSONDecodeError, TypeError):
        lines = [l.strip() for l in str(urls_and_titles).splitlines() if l.strip()]
        entries = [{"url": l, "title": l} for l in lines]

    results = []
    for entry in entries:
        if isinstance(entry, dict):
            u, t = entry.get("url", ""), entry.get("title", "")
        else:
            u, t = str(entry), str(entry)
        results.append(browser_bookmark_add(u, t, folder, browser, session_id))

    ok = sum(1 for r in results if r.startswith("✅"))
    lines = [f"📁 Bookmark folder '{folder}' — {ok}/{len(entries)} added:"]
    lines += [f"  {r}" for r in results]
    return "\n".join(lines)
