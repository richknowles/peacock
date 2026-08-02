# 🦚 PEACOCK INSTALLATION SCRIPT — Windows — v1.1.2
# Built by Rich Knowles
# Run in PowerShell as Administrator: .\install_windows.ps1

$ErrorActionPreference = "Stop"
$VERSION = "1.1.2"

Write-Host "🦚 Installing Peacock MCP Server v$VERSION for Windows..." -ForegroundColor Cyan

# Python check
try {
    $pyVersion = & python --version 2>&1
    Write-Host "✅ $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Download from https://python.org" -ForegroundColor Red
    Write-Host "   Make sure to check 'Add Python to PATH' during install." -ForegroundColor Yellow
    exit 1
}

# pip install dependencies
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Cyan
& python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ pip install failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Dependencies installed" -ForegroundColor Green

# Chrome check
$chromePaths = @(
    "$env:PROGRAMFILES\Google\Chrome\Application\chrome.exe",
    "${env:PROGRAMFILES(X86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)
$chromeFound = $false
foreach ($p in $chromePaths) {
    if (Test-Path $p) { $chromeFound = $true; break }
}
if (-not $chromeFound) {
    Write-Host ""
    Write-Host "⚠️  Google Chrome not detected. Download from https://google.com/chrome" -ForegroundColor Yellow
    Write-Host "   Peacock attaches to your running Chrome — no WebDriver needed." -ForegroundColor Yellow
}

# Edge is built into Windows — no check needed

# Compute absolute path to server
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerPath = Join-Path $ScriptDir "peacock_server.py"

# Claude Desktop config location
$ClaudeConfig = "$env:APPDATA\Claude\claude_desktop_config.json"

Write-Host ""
Write-Host "🎉 Peacock v$VERSION installed on Windows!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Add this to your Claude Desktop config:" -ForegroundColor Cyan
Write-Host "   $ClaudeConfig" -ForegroundColor White
Write-Host ""
$configJson = @"
{
  "mcpServers": {
    "peacock": {
      "command": "python",
      "args": ["$($ServerPath.Replace('\','\\'))"]
    }
  }
}
"@
Write-Host $configJson -ForegroundColor White
Write-Host ""
Write-Host "   Then restart Claude Desktop." -ForegroundColor Yellow
Write-Host ""
Write-Host "🌐 Chrome control: Peacock attaches to your running Chrome via CDP." -ForegroundColor Cyan
Write-Host "🧭 Edge control:   Built into Windows — no setup needed." -ForegroundColor Cyan
Write-Host "🖥️  VM control:     pip install proxmoxer requests vncdotool" -ForegroundColor Cyan
Write-Host ""
Write-Host "🦚 Ready. Watch it drive." -ForegroundColor Magenta
