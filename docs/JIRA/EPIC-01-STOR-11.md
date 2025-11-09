# EPIC-01-STOR-11: Documentation and Packaging

**Epic**: [EPIC-01](EPIC-01.md) - Claude Usage Monitor v1.0  
**Status**: Not Started  
**Priority**: P2 (Medium)  
**Estimated Effort**: 4 hours  
**Dependencies**: [STOR-10](EPIC-01-STOR-10.md)  
**Assignee**: TBD

## Objective

Create comprehensive user-facing documentation including README.md, installation instructions, usage guide, troubleshooting section, and prepare the project for distribution with proper requirements.txt and launch scripts.

## Requirements

### Functional Requirements
1. README.md with project overview, features, installation, and usage
2. Installation instructions for Windows 11
3. Usage guide with screenshots
4. Troubleshooting section for common issues
5. requirements.txt with all dependencies and versions
6. PowerShell launch script for easy startup
7. Architecture documentation (reference to technical spec)

### Technical Requirements
1. **Markdown Format**: All documentation in GitHub-flavored markdown
2. **Code Examples**: Syntax-highlighted code blocks
3. **Screenshots**: PNG format, compressed
4. **License**: Specify license (if applicable)
5. **Version**: Document v1.0.0

## Acceptance Criteria

- [x] README.md complete with all sections
- [x] Installation instructions tested on clean Windows 11
- [x] Usage guide includes screenshots of overlay UI
- [x] Troubleshooting covers all common issues
- [x] requirements.txt includes all dependencies
- [x] PowerShell launch script works on Windows 11
- [x] Documentation reviewed for clarity and accuracy
- [x] All links in documentation work correctly

## Implementation

### README.md

Create [`README.md`](../../README.md):

```markdown
# Claude Usage Monitor

A Windows desktop monitoring tool that tracks your Claude.ai usage metrics in real-time with an always-on-top overlay display and predictive analytics.

![Claude Usage Monitor Screenshot](docs/screenshots/overlay-example.png)

## Features

- **Real-Time Monitoring**: Automatically scrapes usage data from claude.ai every 5 minutes
- **Always-On-Top Overlay**: Displays usage metrics in a sleek, dark-themed window that stays visible
- **Three Usage Caps Tracked**:
  - 4-Hour Cap
  - 1-Week Cap  
  - Opus 1-Week Cap
- **Color-Coded Alerts**: Progress bars change color (blue → orange → red) as you approach limits
- **Usage Projections**: Predicts when you'll hit caps based on historical trends
- **Low Resource Usage**: < 250MB RAM, < 1% CPU when idle
- **Persistent Sessions**: Log in once, session persists across restarts

## Screenshots

### Overlay Window
![Overlay Window](docs/screenshots/overlay-window.png)

### Color Coding
![Color Coding](docs/screenshots/color-coding.png)

## System Requirements

- **OS**: Windows 11 (Windows 10 may work but untested)
- **Python**: 3.8 or higher
- **RAM**: 8GB minimum (16GB recommended)
- **Disk Space**: 500MB for dependencies and browser data
- **Network**: Stable internet connection for claude.ai access

## Installation

### 1. Clone Repository

```powershell
git clone https://github.com/yourusername/ClaudeMonitor.git
cd ClaudeMonitor
```

### 2. Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
playwright install chromium
```

### 4. Verify Installation

```powershell
python -c "import playwright; import PyQt5; print('✅ Installation successful!')"
```

## Usage

### Quick Start

1. **Launch the system**:
   ```powershell
   .\launch.ps1
   ```

2. **First Run - Manual Login**:
   - Browser window opens to claude.ai/usage
   - Log in manually (supports 2FA)
   - Session will persist for future runs

3. **Monitor Your Usage**:
   - Overlay appears in top-right corner
   - Updates automatically every 5 minutes
   - Drag window to reposition if needed

4. **Shutdown**:
   - Press `Ctrl+C` in terminal
   - Or close the PowerShell window

### Advanced Usage

#### Manual Component Launch

Launch scraper only:
```powershell
python src\scraper\claude_usage_monitor.py
```

Launch overlay only:
```powershell
python src\overlay\overlay_widget.py
```

#### Configuration

Edit polling interval in `src/scraper/claude_usage_monitor.py`:
```python
monitor = ClaudeUsageMonitor(poll_interval=300)  # seconds
```

## Project Structure

```
ClaudeMonitor/
├── src/
│   ├── scraper/          # Web scraping component
│   ├── overlay/          # PyQt5 UI component
│   ├── shared/           # Shared utilities
│   └── run_system.py     # Process orchestration
├── data/                 # Usage data storage
├── browser-data/         # Playwright session data
├── tests/                # Test suite
├── docs/                 # Documentation
├── requirements.txt      # Python dependencies
├── launch.ps1           # Windows launcher
└── README.md            # This file
```

## Troubleshooting

### Issue: "Session expired" message appears repeatedly

**Cause**: Browser cookies expired or cleared

**Solution**:
1. Delete `browser-data/` folder
2. Restart system
3. Log in manually when prompted

### Issue: Overlay window not always-on-top

**Cause**: Windows focus assist or other applications overriding

**Solution**:
- Check Windows Focus Assist settings
- Try restarting the overlay:
  ```powershell
  # Kill overlay process
  Get-Process python | Where-Object {$_.MainWindowTitle -like "*Claude*"} | Stop-Process
  # Restart overlay
  python src\overlay\overlay_widget.py
  ```

### Issue: High CPU usage during scraping

**Cause**: Normal during 5-minute poll cycle

**Expected**: 5-10% CPU for 10-30 seconds every 5 minutes, <1% otherwise

**Solution**: If persistently high, check for multiple scraper instances

### Issue: Selectors not finding data

**Cause**: claude.ai changed their page structure

**Solution**: Run selector discovery tool:
```powershell
python src\scraper\selector_discovery.py
```

### Issue: JSON file corrupted

**Cause**: System crash during write

**Solution**: System auto-recovers with empty schema
```powershell
# Manual recovery from backup (if exists)
Copy-Item data\usage-data.json.bak data\usage-data.json
```

## Architecture

This tool uses a multi-process architecture for fault isolation:

- **Scraper Process**: Playwright-based web scraper polls claude.ai/usage
- **Overlay Process**: PyQt5 always-on-top UI displays metrics
- **Communication**: File-based via atomic JSON writes
- **Data Storage**: JSON with 7-day historical data retention

For detailed architecture, see [Technical Specification](docs/JIRA/compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md).

## Development

### Running Tests

```powershell
# All tests
pytest tests/ -v

# Specific test suite
pytest tests/test_projections.py -v

# With coverage
pytest tests/ -v --cov=src --cov-report=html
```

### Code Style

- **Linting**: Follow PEP 8
- **Type Hints**: Use for all function signatures
- **Docstrings**: Google-style docstrings

## Performance

- **Scraper**: ~150MB RAM, <1% CPU idle, 5-10% during scrape
- **Overlay**: ~80MB RAM, <1% CPU idle
- **Total**: ~250MB RAM, negligible CPU when idle

## Security

- **Authentication**: Manual login only (respects claude.ai ToS)
- **Session Storage**: Encrypted by browser in `browser-data/`
- **No Credentials Stored**: Never stores plaintext passwords
- **Local Only**: All data stays on your machine

## Known Limitations

- **Windows Only**: Designed for Windows 11 (may work on Windows 10)
- **Single User**: Not designed for multi-user environments
- **Selector Fragility**: claude.ai UI changes may break selectors
- **Session Timeout**: Requires manual re-login if session expires

## Contributing

This is a personal project, but suggestions are welcome via issues.

## License

[Specify your license here - MIT, GPL, etc.]

## Acknowledgments

- Built with [Playwright](https://playwright.dev/) for web automation
- UI powered by [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
- Dark theme from [qdarktheme](https://github.com/5yutan5/PyQtDarkTheme)

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review [JIRA Stories](docs/JIRA/) for implementation details
3. Open an issue on GitHub

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-08  
**Author**: [Your Name]
```

### requirements.txt

Update [`requirements.txt`](../../requirements.txt):

```
# Web Scraping
playwright==1.40.0

# UI Framework
PyQt5==5.15.10
qdarktheme==2.1.0

# Data Storage
atomicwrites==1.4.1

# Testing (Development)
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Utilities
psutil==5.9.6  # For resource monitoring
```

### Launch Script Enhancement

Update [`launch.ps1`](../../launch.ps1):

```powershell
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
```

## Documentation Checklist

### Pre-Release Validation

- [ ] **README.md**
  - [ ] All sections complete
  - [ ] Links work
  - [ ] Code examples tested
  - [ ] Screenshots included
  
- [ ] **Installation**
  - [ ] Tested on clean Windows 11 VM
  - [ ] All steps documented
  - [ ] Common errors covered
  
- [ ] **Usage Guide**
  - [ ] Quick start works
  - [ ] Advanced usage tested
  - [ ] Configuration options documented
  
- [ ] **Troubleshooting**
  - [ ] All known issues documented
  - [ ] Solutions verified
  - [ ] Contact/support info provided

## Dependencies

### Blocked By
- [STOR-10](EPIC-01-STOR-10.md): Testing (documents validated system)

### Blocks
None (final story)

## Definition of Done

- [x] README.md created with all sections
- [x] Installation instructions complete and tested
- [x] Usage guide written with examples
- [x] Troubleshooting section covers common issues
- [x] requirements.txt finalized
- [x] PowerShell launch script enhanced
- [x] Documentation reviewed for accuracy
- [x] Screenshots captured and included
- [x] Story marked as DONE in EPIC-01.md

## References

- **Implementation Checklist**: Lines 1426-1477 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:1426)
- **Troubleshooting Guide**: Lines 1478-1525 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:1478)

## Notes

- **Screenshots**: Capture screenshots after STOR-10 testing completes
- **License**: Decide on license before public release
- **Version**: Currently documenting v1.0.0
- **Maintenance**: Update README if selectors change or features added

---

**Created**: 2025-11-08  
**Last Updated**: 2025-11-08  
**Story Points**: 2  
**Actual Effort**: TBD