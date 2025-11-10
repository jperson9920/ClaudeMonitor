# launch.ps1
# Claude Usage Monitor - Windows Launcher Script

param(
    [switch]$SkipVenv,
    [switch]$Debug
)

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Claude Usage Monitor v1.0.0" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Activate virtual environment
if (-not $SkipVenv) {
    if (Test-Path "venv\Scripts\Activate.ps1") {
        Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
        & .\venv\Scripts\Activate.ps1
        Write-Host "✅ Virtual environment activated" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Virtual environment not found. Run setup first:" -ForegroundColor Yellow
        Write-Host "   python -m venv venv" -ForegroundColor White
        Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor White
        Write-Host "   pip install -r requirements.txt" -ForegroundColor White
        exit 1
    }
}

# Check dependencies
Write-Host "🔍 Checking dependencies..." -ForegroundColor Yellow
$depCheck = python -c "import playwright; import PyQt5; import qdarktheme; import atomicwrites; print('OK')" 2>&1

if ($depCheck -like "*OK*") {
    Write-Host "✅ All dependencies installed" -ForegroundColor Green
} else {
    Write-Host "❌ Missing dependencies. Installing..." -ForegroundColor Red
    pip install -r requirements.txt
    playwright install chromium
}

# Launch system
Write-Host ""
Write-Host "🚀 Starting Claude Usage Monitor..." -ForegroundColor Green
Write-Host ""

if ($Debug) {
    # Debug mode - keep output visible
    python src\run_system.py
} else {
    # Normal mode
    python src\run_system.py
}

Write-Host ""
Write-Host "System stopped." -ForegroundColor Yellow
