<#
.SYNOPSIS
    Manga AI Colorization Studio - One-Click Launcher for Windows 11
.DESCRIPTION
    Launches FastAPI Backend (NVIDIA RTX 5060 accelerated) and opens the Studio Web UI.
#>

param(
    [switch]$Dev = $false,
    [int]$Port = 8000
)

$Host.UI.RawUI.WindowTitle = "Manga AI Colorization Studio"
Write-Host ""
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "            MANGA AI COLORIZATION STUDIO                    " -ForegroundColor Cyan
Write-Host "     NVIDIA RTX 5060 Accelerated &bull; Zero Paid Cloud APIs  " -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 1. Check Python Virtual Environment
$VenvPython = Join-Path $ScriptDir "backend\.venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "[1/3] Setting up Python virtual environment with uv..." -ForegroundColor Yellow
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv venv --python 3.11 backend/.venv
        uv pip install --python $VenvPython -r backend/requirements.txt
    } else {
        py -3.11 -m venv backend/.venv
        & $VenvPython -m pip install -r backend/requirements.txt
    }
} else {
    Write-Host "[1/3] Python virtual environment verified." -ForegroundColor Green
}

# 2. Check Hardware
Write-Host "[2/3] Checking NVIDIA Hardware Telemetry..." -ForegroundColor Yellow
& $VenvPython -c "from backend.app.core.hardware import get_hardware_telemetry; t=get_hardware_telemetry(); print(f'      GPU: {t[\"gpu\"][\"device_name\"]} ({t[\"gpu\"][\"total_vram_mb\"]} MB VRAM)'); print(f'      RAM: {t[\"ram\"][\"total_gb\"]} GB | CPU Cores: {t[\"cpu\"][\"cores\"]}')"

# 3. Check / Build Frontend
$DistIndex = Join-Path $ScriptDir "frontend\dist\index.html"
if (-not (Test-Path $DistIndex) -and -not $Dev) {
    Write-Host "      Building frontend distribution..." -ForegroundColor Yellow
    Push-Location (Join-Path $ScriptDir "frontend")
    npm run build
    Pop-Location
}

Write-Host "[3/3] Launching Studio Web Server..." -ForegroundColor Green
Write-Host ""
Write-Host "  -> Studio URL: http://localhost:$Port" -ForegroundColor Cyan
Write-Host "  -> API Docs:   http://localhost:$Port/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop the studio." -ForegroundColor Yellow
Write-Host ""

# Automatically open browser
Start-Process "http://localhost:$Port"

# Start Uvicorn Server
& $VenvPython -m uvicorn backend.app.main:app --host 0.0.0.0 --port $Port
