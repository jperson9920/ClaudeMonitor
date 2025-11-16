# Claude Usage Monitor

Project description

A minimal Tauri + React + Python scaffold to monitor Claude usage and provide a desktop widget and scraper.

## Prerequisites

- Node.js: 18+
- Rust: 1.70+
- Python: 3.9+
- Chrome/Chromium: Latest stable version

## Setup (verbatim from docs/Research.md)

Install Rust (if not already installed)

bash# macOS/Linux
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Windows
# Download from: https://rustup.rs

Install Node.js (if not already installed)

bash# macOS with Homebrew
brew install node

# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Windows
# Download from: https://nodejs.org

Install Python 3.9+ (if not already installed)

bash# macOS with Homebrew
brew install python@3.9

# Ubuntu/Debian
sudo apt-get install python3.9 python3.9-venv

# Windows
# Download from: https://www.python.org/downloads/

Install Tauri CLI

bashnpm install -g @tauri-apps/cli
# Or use cargo:
cargo install tauri-cli

Install Chrome/Chromium

Download from: https://www.google.com/chrome/
Or use system package manager
Note: undetected-chromedriver auto-downloads matching ChromeDriver

Project Initialization

bash# Create project directory
mkdir claude-usage-monitor
cd claude-usage-monitor

# Initialize Tauri project
npm create tauri-app@latest
# Choose:
# - Package name: claude-usage-monitor
# - Window title: Claude Usage Monitor
# - Frontend: React with TypeScript
# - Package manager: npm

# Set up Python virtual environment
python3 -m venv scraper-env
source scraper-env/bin/activate  # On Windows: scraper-env\Scripts\activate

# Install Python dependencies
pip install undetected-chromedriver selenium

## Run (development)

- npm install
- npm run tauri dev

## Scraper (Python)

Create and activate venv:

- python3 -m venv scraper-env && source scraper-env/bin/activate
- (Windows) scraper-env\Scripts\activate

Install dependencies:

- pip install -r scraper/requirements.txt

## Tests

- pytest scraper/  # Python tests (to be added in EPIC-02)
- npm test         # Frontend tests (to be added in EPIC-05)

## Local validation checklist

1. Create Python venv: python3 -m venv scraper-env
2. Activate venv and pip install -r scraper/requirements.txt
3. Run npm install at repo root
4. Run npm run tauri dev and verify the Tauri app launches

## Created files & directories

- src-tauri/ (Tauri Rust backend)
- src/ (React frontend)
- scraper/ (Python scraper module)
  - scraper/claude_scraper.py
  - scraper/requirements.txt

## References

See [`docs/Research.md`](docs/Research.md:121-201) for original toolchain and setup instructions.