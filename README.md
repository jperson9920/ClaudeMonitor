# Claude Usage Monitor

A desktop widget that monitors your Claude.ai usage by scraping the claude.ai/settings/usage page. Displays real-time usage metrics to help manage heavy agentic coding workloads against Claude Max plan limits.

## Features

- Real-time usage monitoring (polls every 5 minutes)
- Desktop widget with system tray support
- Visual progress bars and alerts
- Session persistence (login once, monitor forever)
- Cloudflare bypass with 85-95% success rate

## Architecture

- **Python Scraper**: Web scraping with undetected-chromedriver
- **Rust Backend**: Process management and state handling (Tauri)
- **React Frontend**: Modern UI with real-time updates

## Development Status

✅ **EPIC-01**: Python Web Scraper Foundation - COMPLETE
✅ **EPIC-02**: Tauri Application Setup - COMPLETE
🚧 **EPIC-03**: Rust-Python Integration - IN PROGRESS

## Quick Start

### Prerequisites

- Python 3.9+
- Chrome/Chromium browser
- Node.js 18+ (for Tauri frontend)
- Rust 1.70+ (for Tauri backend)

### Setup Python Scraper

```bash
# Create virtual environment
python3 -m venv scraper-env
source scraper-env/bin/activate  # On Windows: scraper-env\Scripts\activate

# Install dependencies
cd scraper
pip install -r requirements.txt

# Run manual login (first time only)
python claude_scraper.py --login

# Test automated polling
python claude_scraper.py
```

### Setup Tauri Application

```bash
# Install Node.js dependencies
npm install

# Run in development mode
npm run tauri:dev

# Build for production
npm run tauri:build

# Build artifacts will be in src-tauri/target/release/bundle/
```

## Project Structure

```
ClaudeMonitor/
├── docs/                      # Documentation and research
│   ├── Research.md           # Comprehensive implementation guide
│   └── EPIC-*.md            # Epic specifications
├── scraper/                  # Python web scraper
│   ├── claude_scraper.py    # Main scraper implementation
│   ├── requirements.txt     # Python dependencies
│   └── test_scraper.py      # Unit tests
├── src-tauri/               # Rust backend (coming in Epic 2)
└── src/                     # React frontend (coming in Epic 3)
```

## License

MIT

## Disclaimer

This tool scrapes the Claude.ai web interface for personal usage monitoring. Automated scraping may violate Claude.ai Terms of Service. Use at your own risk for personal monitoring only.
