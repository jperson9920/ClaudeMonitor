# Claude Usage Monitor

A Windows desktop monitoring tool that tracks your Claude.ai usage metrics in real-time with an always-on-top overlay display and predictive analytics.

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

## System Requirements

- **OS**: Windows 11 (Windows 10 may work but untested) / Linux (for development)
- **Python**: 3.8 or higher
- **RAM**: 8GB minimum (16GB recommended)
- **Disk Space**: 500MB for dependencies and browser data
- **Network**: Stable internet connection for claude.ai access

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/ClaudeMonitor.git
cd ClaudeMonitor
```

### 2. Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

If you get an execution policy error on Windows:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Verify Installation

```bash
python -c "import playwright; import PyQt5; print('✅ Installation successful!')"
```

## Usage

### Quick Start (Windows)

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

### Quick Start (Linux/Development)

```bash
python src/run_system.py
```

### Advanced Usage

#### Manual Component Launch

Launch scraper only:
```bash
python src/scraper/claude_usage_monitor.py
```

Launch overlay only:
```bash
python src/overlay/overlay_widget.py
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
│   │   ├── claude_usage_monitor.py
│   │   ├── session_manager.py
│   │   └── selector_discovery.py
│   ├── overlay/          # PyQt5 UI component
│   │   ├── overlay_widget.py
│   │   └── projection_algorithms.py
│   ├── shared/           # Shared utilities
│   │   ├── data_schema.py
│   │   ├── rate_limiter.py
│   │   └── error_logger.py
│   └── run_system.py     # Process orchestration
├── data/                 # Usage data storage
├── browser-data/         # Playwright session data
├── tests/                # Test suite
├── docs/                 # Documentation
│   ├── JIRA/            # EPIC and story documentation
│   └── selectors.md     # CSS selector reference
├── requirements.txt      # Python dependencies
├── launch.ps1           # Windows launcher
├── .gitignore
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
  ```bash
  # Kill overlay process and restart
  python src/overlay/overlay_widget.py
  ```

### Issue: High CPU usage during scraping

**Cause**: Normal during 5-minute poll cycle

**Expected**: 5-10% CPU for 10-30 seconds every 5 minutes, <1% otherwise

**Solution**: If persistently high, check for multiple scraper instances

### Issue: Selectors not finding data

**Cause**: claude.ai changed their page structure

**Solution**: Run selector discovery tool:
```bash
python src/scraper/selector_discovery.py
```

### Issue: JSON file corrupted

**Cause**: System crash during write

**Solution**: System auto-recovers with empty schema
```bash
# Manual recovery from backup (if exists)
cp data/usage-data.json.bak data/usage-data.json
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

```bash
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

MIT License - See LICENSE file for details

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
**Last Updated**: 2025-11-09
**Project**: EPIC-01 - Claude Usage Monitor v1.0
