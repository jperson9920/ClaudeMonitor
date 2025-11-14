# Build Instructions

This document provides detailed instructions for building and running the Claude Usage Monitor application.

## Prerequisites

### System Requirements
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 2GB free space for dependencies and build artifacts

### Required Software

#### 1. Python 3.9+
```bash
# macOS (Homebrew)
brew install python@3.9

# Ubuntu/Debian
sudo apt-get install python3.9 python3.9-venv python3-pip

# Windows
# Download from https://www.python.org/downloads/
```

#### 2. Node.js 18+
```bash
# macOS (Homebrew)
brew install node

# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Windows
# Download from https://nodejs.org
```

#### 3. Rust 1.70+
```bash
# All platforms
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# After installation, restart your terminal and verify:
rustc --version
cargo --version
```

#### 4. Chrome/Chromium Browser
```bash
# macOS
brew install --cask google-chrome

# Ubuntu/Debian
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb

# Windows
# Download from https://www.google.com/chrome/
```

#### 5. Platform-Specific Dependencies

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install libwebkit2gtk-4.0-dev \
    build-essential \
    curl \
    wget \
    file \
    libssl-dev \
    libgtk-3-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev
```

**macOS:**
```bash
xcode-select --install
```

**Windows:**
- Install Visual Studio Build Tools or Visual Studio with C++ development tools
- Install WebView2 runtime (usually pre-installed on Windows 11)

## Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/jperson9920/ClaudeMonitor.git
cd ClaudeMonitor
```

### 2. Setup Python Scraper
```bash
# Create virtual environment
python3 -m venv scraper-env

# Activate virtual environment
# macOS/Linux:
source scraper-env/bin/activate
# Windows:
scraper-env\Scripts\activate

# Install Python dependencies
cd scraper
pip install -r requirements.txt
cd ..
```

### 3. Setup Tauri Application
```bash
# Install Node.js dependencies
npm install

# This will install:
# - Tauri CLI
# - React and React DOM
# - Vite build tool
# - TypeScript
```

## Development Workflow

### Running in Development Mode

#### Terminal 1: Python Scraper (optional - for manual testing)
```bash
source scraper-env/bin/activate  # or scraper-env\Scripts\activate on Windows
cd scraper

# First time only: Manual login
python claude_scraper.py --login
# Follow browser prompts to log in to Claude.ai

# Test scraper independently
python claude_scraper.py
```

#### Terminal 2: Tauri Application
```bash
# Run Tauri in development mode
npm run tauri:dev

# This will:
# 1. Start Vite dev server on port 1420
# 2. Compile Rust backend
# 3. Launch the desktop application
# 4. Enable hot-reload for frontend changes
```

### Building for Production

#### Complete Build
```bash
# Ensure scraper dependencies are in place
cd scraper && pip install -r requirements.txt && cd ..

# Build Tauri application
npm run tauri:build
```

This will create platform-specific bundles:

**macOS:**
- `src-tauri/target/release/bundle/dmg/Claude Usage Monitor_0.1.0_x64.dmg`
- `src-tauri/target/release/bundle/macos/Claude Usage Monitor.app`

**Windows:**
- `src-tauri/target/release/bundle/msi/Claude Usage Monitor_0.1.0_x64_en-US.msi`
- `src-tauri/target/release/bundle/nsis/Claude Usage Monitor_0.1.0_x64-setup.exe`

**Linux:**
- `src-tauri/target/release/bundle/deb/claude-usage-monitor_0.1.0_amd64.deb`
- `src-tauri/target/release/bundle/appimage/claude-usage-monitor_0.1.0_amd64.AppImage`

#### Frontend-Only Build
```bash
# Build just the React frontend
npm run build

# Output will be in dist/ directory
```

#### Backend-Only Build
```bash
# Build just the Rust backend
cd src-tauri
cargo build --release
cd ..

# Binary will be in src-tauri/target/release/
```

## Testing

### Python Scraper Tests
```bash
source scraper-env/bin/activate
cd scraper

# Run validation tests (no dependencies required)
python validate.py

# Run unit tests (requires dependencies)
python test_scraper.py

# Run integration test (requires Chrome and manual interaction)
python test_scraper.py integration
```

### Rust Backend Tests
```bash
cd src-tauri
cargo test
```

### End-to-End Testing
```bash
# Run the application in dev mode
npm run tauri:dev

# Manual testing checklist:
# 1. Application window opens
# 2. System tray icon appears
# 3. Tray menu works (Show, Hide, Quit)
# 4. IPC communication works (greeting message displays)
```

## Troubleshooting

### Python Scraper Issues

**"ModuleNotFoundError: No module named 'undetected_chromedriver'"**
```bash
# Make sure virtual environment is activated
source scraper-env/bin/activate  # or scraper-env\Scripts\activate
pip install -r scraper/requirements.txt
```

**"ChromeDriver not found"**
- Ensure Google Chrome is installed
- undetected-chromedriver will auto-download matching ChromeDriver
- Check internet connection

### Tauri Build Issues

**"Rust compiler not found"**
```bash
# Install or update Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
rustup update
```

**"Node modules not found"**
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

**Linux: "webkit2gtk not found"**
```bash
sudo apt-get install libwebkit2gtk-4.0-dev
```

**macOS: "Command Line Tools not found"**
```bash
xcode-select --install
```

**Windows: "MSVC not found"**
- Install Visual Studio Build Tools
- Or install Visual Studio Community with "Desktop development with C++"

### Runtime Issues

**"Application won't start"**
```bash
# Check logs
# macOS: ~/Library/Logs/com.claude-usage-monitor.app/
# Linux: ~/.local/share/claude-usage-monitor/logs/
# Windows: %APPDATA%\com.claude-usage-monitor.app\logs\
```

**"System tray icon not appearing"**
- Ensure system tray is enabled in OS
- Try restarting the application
- Check if running in a VM (some VMs have issues with system trays)

## Advanced Build Options

### Custom Build Configuration

#### Change Application Name
Edit `src-tauri/tauri.conf.json`:
```json
{
  "package": {
    "productName": "Your Custom Name"
  }
}
```

#### Change Window Size
Edit `src-tauri/tauri.conf.json`:
```json
{
  "tauri": {
    "windows": [{
      "width": 500,
      "height": 700
    }]
  }
}
```

### Cross-Platform Builds

Tauri builds for the current platform by default. For cross-platform builds, see [Tauri Cross-Compilation Guide](https://tauri.app/v1/guides/building/cross-platform).

### Code Signing

#### macOS
```bash
# Set up in tauri.conf.json
{
  "bundle": {
    "macOS": {
      "signingIdentity": "Developer ID Application: Your Name (TEAMID)"
    }
  }
}
```

#### Windows
```bash
# Set up in tauri.conf.json
{
  "bundle": {
    "windows": {
      "certificateThumbprint": "YOUR_CERT_THUMBPRINT",
      "digestAlgorithm": "sha256",
      "timestampUrl": "http://timestamp.digicert.com"
    }
  }
}
```

## Performance Optimization

### Frontend
```bash
# Analyze bundle size
npm run build
npx vite-bundle-visualizer
```

### Backend
```bash
# Build with optimizations
cd src-tauri
cargo build --release --target-cpu=native
```

## Continuous Integration

Example GitHub Actions workflow is available in `.github/workflows/build.yml` (to be added in future epic).

## Support

For issues, see:
- [Tauri Documentation](https://tauri.app)
- [Project Issues](https://github.com/jperson9920/ClaudeMonitor/issues)
- Research.md for implementation details
