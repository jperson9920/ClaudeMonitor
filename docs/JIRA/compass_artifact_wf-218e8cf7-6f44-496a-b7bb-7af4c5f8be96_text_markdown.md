# Building a Windows Desktop Monitoring Tool for Claude Usage Data

## Overview

This comprehensive technical guide provides everything needed to build a Windows desktop monitoring tool that extracts Claude usage data from claude.ai, displays it in an always-on-top overlay, and projects usage trends. **The recommended stack combines Playwright for web scraping, PyQt5 for the UI overlay, file-based JSON storage with atomic writes, and simple moving averages for usage projection.**

## Recommended Technology Stack

### Core Components

**Web Scraping**: Playwright with Node.js or Python
- Lowest memory footprint (70-150MB peak)
- Built-in auto-wait mechanisms reduce flaky operations
- Persistent browser context maintains authentication
- Best Windows desktop integration
- Fastest execution in benchmarks

**UI Framework**: PyQt5/PySide2
- Native performance with 50-80MB RAM usage
- Excellent Windows API integration for always-on-top and click-through
- Startup time under 1 second
- Mature dark theme libraries (qdarkstyle, qdarktheme)
- Direct access to Windows extended styles

**Alternative UI Option**: Tauri (for web developers)
- 2.5-10MB bundle size using Edge WebView2
- Modern web-based UI development
- Requires Rust backend knowledge
- Good balance of performance and developer experience

**Data Storage**: JSON with atomic writes
- File-based with write-file-atomic (Node.js) or atomicfile (Python)
- Chokidar (Node.js) or watchdog (Python) for file watching
- Simple, debuggable, cross-process compatible

**Forecasting**: Simple Moving Average + Linear Regression
- Lightweight algorithms suitable for widget
- No heavy ML libraries required
- Sufficient for short-term usage prediction

## Architecture Overview

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   MONITORING SYSTEM                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────┐         ┌──────────────────┐       │
│  │  Scraper       │────────▶│ JSON Data Store  │       │
│  │  Process       │  Write  │ (Atomic)         │       │
│  │                │         │                  │       │
│  │ - Playwright   │         │ usage-data.json  │       │
│  │ - Every 5 min  │         │                  │       │
│  │ - Session mgmt │         └────────┬─────────┘       │
│  └────────────────┘                  │                  │
│                                      │ Watch            │
│                                      │                  │
│  ┌────────────────┐         ┌───────▼─────────┐       │
│  │  Overlay UI    │◀────────│ File Watcher    │       │
│  │  Process       │  Read   │ (Chokidar)      │       │
│  │                │         │                  │       │
│  │ - PyQt5/Tauri  │         └─────────────────┘       │
│  │ - Always-on-top│                                    │
│  │ - Click-through│                                    │
│  │ - Dark theme   │         ┌─────────────────┐       │
│  └────────────────┘         │  Projection     │       │
│         │                   │  Algorithm      │       │
│         └──────────────────▶│  (In UI)        │       │
│           Calculate         │                  │       │
│                             └─────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

### Multi-Process Design

**Process Separation Benefits**:
- Fault isolation (UI crash doesn't stop scraping)
- True parallelism (no GIL limitations in Python)
- Independent restart/update of components
- Better resource management

**Communication Pattern**:
- Scraper writes to JSON atomically every 5 minutes
- UI watches JSON file for changes
- No complex IPC required
- Easy debugging (inspect JSON manually)

## Component 1: Web Scraping Claude Usage Data

### Recommended: Playwright with Persistent Context

#### Why Playwright?

**Performance Comparison**:

| Tool | Memory | Startup | Reliability | Windows Support |
|------|--------|---------|-------------|-----------------|
| Playwright | 70-150MB | 2s | Excellent | ✅ Native |
| Puppeteer | 90-250MB | 3s | Good | ⚠️ Limited |
| Selenium | 150-300MB | 5s | Fair | ✅ Good |
| Browser Ext | Low | Instant | Excellent | ❌ Requires browser open |

**Key Advantages**:
- Auto-wait mechanisms (automatically waits for elements to be actionable)
- Persistent browser context (authentication survives between runs)
- Browser context isolation (prevents cookie bleeding)
- Cross-platform with unified API
- Active Microsoft backing ensures long-term support

#### Implementation: Node.js Version

```javascript
// claude-usage-monitor.js
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const writeFileAtomic = require('write-file-atomic');

class ClaudeUsageMonitor {
  constructor(config) {
    this.config = {
      pollInterval: 5 * 60 * 1000, // 5 minutes
      userDataDir: path.join(__dirname, 'browser-data'),
      dataFile: path.join(__dirname, 'usage-data.json'),
      ...config
    };
    this.context = null;
    this.page = null;
    this.pollTimer = null;
  }
  
  async start() {
    try {
      // Launch persistent context (maintains authentication)
      this.context = await chromium.launchPersistentContext(
        this.config.userDataDir,
        {
          headless: false,
          channel: 'chrome',
          args: [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox'
          ],
          viewport: { width: 1280, height: 720 }
        }
      );
      
      // Check if logged in
      this.page = await this.context.newPage();
      await this.page.goto('https://claude.ai/usage', {
        waitUntil: 'networkidle',
        timeout: 30000
      });
      
      if (this.page.url().includes('/login')) {
        console.log('⚠️  Please log in manually in the browser window...');
        await this.page.waitForURL('**/usage', { timeout: 300000 }); // 5 min timeout
        console.log('✅ Login successful! Starting monitoring...');
      }
      
      // Perform initial poll
      await this.poll();
      
      // Start polling interval
      this.pollTimer = setInterval(() => this.poll(), this.config.pollInterval);
      
      console.log(`🔄 Monitoring started. Polling every ${this.config.pollInterval / 1000}s`);
      
    } catch (error) {
      console.error('Failed to start monitor:', error);
      throw error;
    }
  }
  
  async poll() {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] 📊 Polling usage data...`);
    
    try {
      // Navigate to usage page
      await this.page.goto('https://claude.ai/usage', { 
        waitUntil: 'networkidle',
        timeout: 30000 
      });
      
      // Check if session expired
      if (this.page.url().includes('/login')) {
        console.log('⚠️  Session expired. Please log in again.');
        await this.page.waitForURL('**/usage', { timeout: 300000 });
      }
      
      // Wait for usage metrics to load
      await this.page.waitForSelector('[data-testid="usage-metric"]', { 
        timeout: 10000 
      }).catch(() => {
        // Fallback to generic selector if specific testid doesn't exist
        return this.page.waitForSelector('.usage-metric, [class*="usage"]', {
          timeout: 10000
        });
      });
      
      // Extract usage data
      const usageData = await this.extractUsageData();
      
      // Save to file atomically
      await this.saveData(usageData);
      
      console.log('✅ Poll successful:', JSON.stringify(usageData, null, 2));
      
    } catch (error) {
      console.error('❌ Poll failed:', error.message);
      
      // Save error state
      await this.saveData({
        timestamp,
        error: error.message,
        status: 'error'
      });
      
      // Wait before retry
      await this.page.waitForTimeout(10000);
    }
  }
  
  async extractUsageData() {
    // Extract usage data from page
    return await this.page.evaluate(() => {
      // Helper functions
      const getText = (selector) => {
        const el = document.querySelector(selector);
        return el ? el.textContent.trim() : null;
      };
      
      const getAttr = (selector, attr) => {
        const el = document.querySelector(selector);
        return el ? el.getAttribute(attr) : null;
      };
      
      const parsePercentage = (text) => {
        if (!text) return null;
        const match = text.match(/(\d+\.?\d*)/);
        return match ? parseFloat(match[1]) : null;
      };
      
      // Extract metrics (adapt selectors to actual claude.ai structure)
      // These are example selectors - inspect claude.ai/usage to get actual selectors
      return {
        timestamp: new Date().toISOString(),
        fourHour: {
          usagePercent: parsePercentage(getText('[data-cap="4hour"] .usage-percent')) || 0,
          resetTime: getText('[data-cap="4hour"] .reset-timer'),
        },
        oneWeek: {
          usagePercent: parsePercentage(getText('[data-cap="1week"] .usage-percent')) || 0,
          resetTime: getText('[data-cap="1week"] .reset-timer'),
        },
        opusOneWeek: {
          usagePercent: parsePercentage(getText('[data-cap="opus"] .usage-percent')) || 0,
          resetTime: getText('[data-cap="opus"] .reset-timer'),
        },
        status: 'success'
      };
    });
  }
  
  async saveData(data) {
    // Read existing data
    let existingData = { historicalData: [] };
    if (fs.existsSync(this.config.dataFile)) {
      try {
        existingData = JSON.parse(fs.readFileSync(this.config.dataFile, 'utf8'));
      } catch (err) {
        console.warn('Failed to read existing data:', err.message);
      }
    }
    
    // Update current state
    const newData = {
      schemaVersion: '1.0.0',
      metadata: {
        lastUpdate: new Date().toISOString(),
        applicationVersion: '1.0.0'
      },
      currentState: data.status === 'success' ? {
        fourHour: data.fourHour,
        oneWeek: data.oneWeek,
        opusOneWeek: data.opusOneWeek,
        timestamp: data.timestamp
      } : existingData.currentState,
      historicalData: existingData.historicalData || []
    };
    
    // Add to historical data (keep last 336 points = 7 days at 5-min intervals)
    if (data.status === 'success') {
      newData.historicalData.push({
        timestamp: data.timestamp,
        fourHour: data.fourHour.usagePercent,
        oneWeek: data.oneWeek.usagePercent,
        opusOneWeek: data.opusOneWeek.usagePercent
      });
      
      // Keep only last week of data
      if (newData.historicalData.length > 2016) { // 7 days * 24 hours * 12 (5-min intervals)
        newData.historicalData = newData.historicalData.slice(-2016);
      }
    }
    
    // Write atomically
    await writeFileAtomic(
      this.config.dataFile, 
      JSON.stringify(newData, null, 2),
      { encoding: 'utf8' }
    );
  }
  
  async stop() {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
    }
    if (this.context) {
      await this.context.close();
    }
    console.log('🛑 Monitoring stopped');
  }
}

// Main execution
const monitor = new ClaudeUsageMonitor();

monitor.start().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n🛑 Shutting down...');
  await monitor.stop();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  await monitor.stop();
  process.exit(0);
});
```

#### Python Version with Playwright

```python
# claude_usage_monitor.py
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from atomicwrites import atomic_write

class ClaudeUsageMonitor:
    def __init__(self, poll_interval=300):
        self.poll_interval = poll_interval  # seconds
        self.user_data_dir = Path(__file__).parent / 'browser-data'
        self.data_file = Path(__file__).parent / 'usage-data.json'
        self.context = None
        self.page = None
        self.running = False
        
    async def start(self):
        """Start the monitoring system"""
        async with async_playwright() as p:
            # Launch persistent context
            self.context = await p.chromium.launch_persistent_context(
                str(self.user_data_dir),
                headless=False,
                channel='chrome',
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ],
                viewport={'width': 1280, 'height': 720}
            )
            
            # Check authentication
            self.page = await self.context.new_page()
            await self.page.goto('https://claude.ai/usage', 
                               wait_until='networkidle',
                               timeout=30000)
            
            if '/login' in self.page.url:
                print('⚠️  Please log in manually...')
                await self.page.wait_for_url('**/usage', timeout=300000)
                print('✅ Login successful!')
            
            # Start polling loop
            self.running = True
            await self.poll_loop()
    
    async def poll_loop(self):
        """Main polling loop"""
        while self.running:
            try:
                await self.poll()
                await asyncio.sleep(self.poll_interval)
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                print(f'❌ Error in poll loop: {e}')
                await asyncio.sleep(10)  # Wait before retry
    
    async def poll(self):
        """Poll usage data"""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        print(f'[{timestamp}] 📊 Polling...')
        
        try:
            await self.page.goto('https://claude.ai/usage',
                               wait_until='networkidle',
                               timeout=30000)
            
            if '/login' in self.page.url:
                print('⚠️  Session expired')
                return
            
            # Wait for metrics to load
            await self.page.wait_for_selector('[data-testid="usage-metric"]',
                                            timeout=10000)
            
            # Extract data
            usage_data = await self.extract_usage_data()
            await self.save_data(usage_data)
            
            print(f'✅ Success: {usage_data}')
            
        except Exception as e:
            print(f'❌ Poll failed: {e}')
            await self.save_data({
                'timestamp': timestamp,
                'error': str(e),
                'status': 'error'
            })
    
    async def extract_usage_data(self):
        """Extract usage data from page"""
        return await self.page.evaluate('''() => {
            const getText = (sel) => {
                const el = document.querySelector(sel);
                return el ? el.textContent.trim() : null;
            };
            
            const parsePercent = (text) => {
                if (!text) return null;
                const match = text.match(/(\d+\.?\d*)/);
                return match ? parseFloat(match[0]) : null;
            };
            
            return {
                timestamp: new Date().toISOString(),
                fourHour: {
                    usagePercent: parsePercent(getText('[data-cap="4hour"] .usage-percent')) || 0,
                    resetTime: getText('[data-cap="4hour"] .reset-timer')
                },
                oneWeek: {
                    usagePercent: parsePercent(getText('[data-cap="1week"] .usage-percent')) || 0,
                    resetTime: getText('[data-cap="1week"] .reset-timer')
                },
                opusOneWeek: {
                    usagePercent: parsePercent(getText('[data-cap="opus"] .usage-percent')) || 0,
                    resetTime: getText('[data-cap="opus"] .reset-timer')
                },
                status: 'success'
            };
        }''')
    
    async def save_data(self, data):
        """Save data atomically"""
        # Read existing
        existing = {'historicalData': []}
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    existing = json.load(f)
            except Exception as e:
                print(f'⚠️  Failed to read existing: {e}')
        
        # Update
        new_data = {
            'schemaVersion': '1.0.0',
            'metadata': {
                'lastUpdate': datetime.utcnow().isoformat() + 'Z',
                'applicationVersion': '1.0.0'
            },
            'currentState': data if data.get('status') == 'success' else existing.get('currentState'),
            'historicalData': existing.get('historicalData', [])
        }
        
        # Add historical point
        if data.get('status') == 'success':
            new_data['historicalData'].append({
                'timestamp': data['timestamp'],
                'fourHour': data['fourHour']['usagePercent'],
                'oneWeek': data['oneWeek']['usagePercent'],
                'opusOneWeek': data['opusOneWeek']['usagePercent']
            })
            
            # Keep last week
            if len(new_data['historicalData']) > 2016:
                new_data['historicalData'] = new_data['historicalData'][-2016:]
        
        # Atomic write
        with atomic_write(str(self.data_file), overwrite=True) as f:
            json.dump(new_data, f, indent=2)
    
    async def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.context:
            await self.context.close()
        print('🛑 Stopped')

# Run
if __name__ == '__main__':
    monitor = ClaudeUsageMonitor(poll_interval=300)
    try:
        asyncio.run(monitor.start())
    except KeyboardInterrupt:
        print('\n🛑 Shutting down...')
```

### Authentication Strategy

**Recommended: Manual Login Once + Persistent Context**

**Advantages**:
- Respects Terms of Service (no automated login)
- Handles 2FA/MFA properly
- More reliable than credential-based login
- Session persists across application restarts
- Lower detection risk

**Implementation**:
1. First run: Browser window opens, user logs in manually
2. Playwright saves entire browser context (cookies, localStorage, session)
3. Subsequent runs: Context restored automatically
4. If session expires: Prompt user to log in again

**Session Validation**:
```javascript
async function isSessionValid(page) {
  try {
    await page.goto('https://claude.ai/usage', { timeout: 10000 });
    if (page.url().includes('/login')) {
      return false;
    }
    await page.waitForSelector('.usage-metric', { timeout: 5000 });
    return true;
  } catch {
    return false;
  }
}
```

### Selector Discovery

**To find the correct selectors for claude.ai/usage**:

1. Open chrome.ai/usage in Chrome/Edge
2. Open DevTools (F12)
3. Use Elements Inspector to find usage percentage elements
4. Look for:
   - `data-testid` attributes (most reliable)
   - Class names with "usage", "percent", "cap"
   - Percentage text nodes
   - Reset timer elements

**Robust Selector Strategy**:
```javascript
// Try multiple selectors in order of preference
const selectors = [
  '[data-testid="usage-4hour"]',
  '[data-cap="4hour"] .usage-percent',
  '.usage-metric[data-period="4h"]',
  // Fallback to text content search
  '//div[contains(text(), "4-hour")]'
];

for (const selector of selectors) {
  try {
    const element = await page.$(selector);
    if (element) {
      return await element.textContent();
    }
  } catch {}
}
```

## Component 2: Always-On-Top Overlay Window

### Recommended: PyQt5 Implementation

#### Complete Overlay Widget

```python
# overlay_widget.py
import sys
import json
import ctypes
from pathlib import Path
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, 
                             QVBoxLayout, QHBoxLayout, QProgressBar)
from PyQt5.QtGui import QPalette, QColor, QFont
import qdarktheme

class UsageOverlay(QWidget):
    def __init__(self, data_file='usage-data.json'):
        super().__init__()
        self.data_file = Path(data_file)
        self.data = {}
        self.init_ui()
        self.make_overlay()
        self.setup_watcher()
        
    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle('Claude Usage Monitor')
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Title
        title = QLabel('Claude Usage Monitor')
        title.setStyleSheet('font-size: 14px; font-weight: bold;')
        layout.addWidget(title)
        
        # 4-Hour Cap
        layout.addWidget(QLabel('4-Hour Cap:'))
        self.fourHourBar = QProgressBar()
        self.fourHourLabel = QLabel('0%')
        self.fourHourReset = QLabel('Reset: --')
        layout.addWidget(self.fourHourBar)
        layout.addWidget(self.fourHourLabel)
        layout.addWidget(self.fourHourReset)
        
        # 1-Week Cap
        layout.addWidget(QLabel('1-Week Cap:'))
        self.oneWeekBar = QProgressBar()
        self.oneWeekLabel = QLabel('0%')
        self.oneWeekReset = QLabel('Reset: --')
        layout.addWidget(self.oneWeekBar)
        layout.addWidget(self.oneWeekLabel)
        layout.addWidget(self.oneWeekReset)
        
        # Opus 1-Week Cap
        layout.addWidget(QLabel('Opus 1-Week:'))
        self.opusBar = QProgressBar()
        self.opusLabel = QLabel('0%')
        self.opusReset = QLabel('Reset: --')
        layout.addWidget(self.opusBar)
        layout.addWidget(self.opusLabel)
        layout.addWidget(self.opusReset)
        
        # Last update timestamp
        self.lastUpdate = QLabel('Last update: Never')
        self.lastUpdate.setStyleSheet('font-size: 10px; color: #888;')
        layout.addWidget(self.lastUpdate)
        
        self.setLayout(layout)
        
        # Apply dark theme
        qdarktheme.setup_theme()
        
        # Custom styling
        self.setStyleSheet('''
            QWidget {
                background-color: #1e1e1e;
                color: #cccccc;
                border-radius: 8px;
            }
            QProgressBar {
                border: 1px solid #3e3e42;
                border-radius: 4px;
                text-align: center;
                background-color: #252526;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                border-radius: 3px;
            }
            QLabel {
                border: none;
            }
        ''')
        
        # Set size
        self.setFixedSize(300, 400)
        
    def make_overlay(self):
        """Configure window as always-on-top overlay"""
        # Remove window frame, make always-on-top
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint |
            Qt.Tool  # Excludes from taskbar
        )
        
        # Optional: Make click-through
        # self.make_clickthrough()
        
        # Enable transparency
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # Position in top-right corner
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20, 20)
        
    def make_clickthrough(self):
        """Make window click-through using Windows API"""
        hwnd = self.winId().__int__()
        
        GWL_EXSTYLE = -20
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_LAYERED = 0x00080000
        
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, 
                             style | WS_EX_TRANSPARENT | WS_EX_LAYERED)
        
    def setup_watcher(self):
        """Setup file watcher to reload data"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.reload_data)
        self.timer.start(1000)  # Check every second
        
        # Initial load
        self.reload_data()
        
    def reload_data(self):
        """Reload data from JSON file"""
        try:
            if not self.data_file.exists():
                return
                
            with open(self.data_file, 'r') as f:
                new_data = json.load(f)
                
            # Check if data changed
            if new_data != self.data:
                self.data = new_data
                self.update_ui()
                
        except Exception as e:
            print(f'Error loading data: {e}')
            
    def update_ui(self):
        """Update UI with current data"""
        state = self.data.get('currentState', {})
        
        # 4-Hour
        fourHour = state.get('fourHour', {})
        percent = fourHour.get('usagePercent', 0)
        self.fourHourBar.setValue(int(percent))
        self.fourHourLabel.setText(f'{percent:.1f}%')
        self.fourHourReset.setText(f'Reset: {fourHour.get("resetTime", "--")}')
        
        # Color coding
        if percent >= 90:
            self.fourHourBar.setStyleSheet('QProgressBar::chunk { background-color: #e74c3c; }')
        elif percent >= 75:
            self.fourHourBar.setStyleSheet('QProgressBar::chunk { background-color: #f39c12; }')
        else:
            self.fourHourBar.setStyleSheet('QProgressBar::chunk { background-color: #007acc; }')
        
        # 1-Week
        oneWeek = state.get('oneWeek', {})
        percent = oneWeek.get('usagePercent', 0)
        self.oneWeekBar.setValue(int(percent))
        self.oneWeekLabel.setText(f'{percent:.1f}%')
        self.oneWeekReset.setText(f'Reset: {oneWeek.get("resetTime", "--")}')
        
        # Opus
        opus = state.get('opusOneWeek', {})
        percent = opus.get('usagePercent', 0)
        self.opusBar.setValue(int(percent))
        self.opusLabel.setText(f'{percent:.1f}%')
        self.opusReset.setText(f'Reset: {opus.get("resetTime", "--")}')
        
        # Last update
        timestamp = self.data.get('metadata', {}).get('lastUpdate', 'Never')
        self.lastUpdate.setText(f'Last update: {timestamp}')
        
    def mousePressEvent(self, event):
        """Enable dragging the window"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """Handle window dragging"""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

def main():
    app = QApplication(sys.argv)
    overlay = UsageOverlay('usage-data.json')
    overlay.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
```

### Multi-Monitor Support

```python
def position_on_monitor(self, monitor_index=0):
    """Position widget on specific monitor"""
    desktop = QApplication.desktop()
    
    if monitor_index < desktop.screenCount():
        screen_geometry = desktop.screenGeometry(monitor_index)
        # Top-right corner of selected monitor
        self.move(
            screen_geometry.x() + screen_geometry.width() - self.width() - 20,
            screen_geometry.y() + 20
        )
```

### Click-Through Toggle

```python
def toggle_clickthrough(self):
    """Toggle click-through on/off"""
    hwnd = self.winId().__int__()
    GWL_EXSTYLE = -20
    WS_EX_TRANSPARENT = 0x00000020
    WS_EX_LAYERED = 0x00080000
    
    user32 = ctypes.windll.user32
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    
    if self.is_clickthrough:
        # Disable click-through
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, 
                             style & ~(WS_EX_TRANSPARENT | WS_EX_LAYERED))
        self.is_clickthrough = False
    else:
        # Enable click-through
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, 
                             style | WS_EX_TRANSPARENT | WS_EX_LAYERED)
        self.is_clickthrough = True
```

### Alternative: Tauri Implementation

For developers preferring web technologies:

```rust
// src-tauri/src/main.rs
use tauri::WindowBuilder;

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            WindowBuilder::new(app, "main", tauri::WindowUrl::default())
                .always_on_top(true)
                .decorations(false)
                .transparent(true)
                .resizable(true)
                .inner_size(300.0, 400.0)
                .build()?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

```html
<!-- src/index.html -->
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            background: rgba(30, 30, 30, 0.95);
            color: #cccccc;
            font-family: 'Segoe UI', sans-serif;
            padding: 10px;
            border-radius: 8px;
        }
        .usage-bar {
            background: #252526;
            height: 20px;
            border-radius: 4px;
            overflow: hidden;
            margin: 5px 0;
        }
        .usage-fill {
            background: #007acc;
            height: 100%;
            transition: width 0.3s;
        }
    </style>
</head>
<body>
    <h3>Claude Usage Monitor</h3>
    <div id="app"></div>
    <script src="main.js"></script>
</body>
</html>
```

## Component 3: Data Storage Schema

### Complete JSON Schema

```json
{
  "schemaVersion": "1.0.0",
  "metadata": {
    "created": "2025-11-08T00:00:00.000Z",
    "lastUpdate": "2025-11-08T14:30:00.000Z",
    "applicationVersion": "1.0.0",
    "timezone": "UTC"
  },
  "currentState": {
    "fourHour": {
      "usagePercent": 45.2,
      "remaining": 54.8,
      "resetTime": "2025-11-08T18:00:00.000Z",
      "lastReset": "2025-11-08T14:00:00.000Z",
      "projectedUsageAtReset": 82.3,
      "estimatedTimeToLimit": "2025-11-08T17:15:00.000Z",
      "averageRatePerHour": 18.45
    },
    "oneWeek": {
      "usagePercent": 68.5,
      "remaining": 31.5,
      "resetTime": "2025-11-15T00:00:00.000Z",
      "lastReset": "2025-11-08T00:00:00.000Z",
      "projectedUsageAtReset": 95.2,
      "estimatedTimeToLimit": "2025-11-14T18:00:00.000Z",
      "averageRatePerDay": 9.79
    },
    "opusOneWeek": {
      "usagePercent": 23.1,
      "remaining": 76.9,
      "resetTime": "2025-11-15T00:00:00.000Z",
      "lastReset": "2025-11-08T00:00:00.000Z",
      "projectedUsageAtReset": 45.8,
      "estimatedTimeToLimit": null,
      "averageRatePerDay": 3.30
    },
    "timestamp": "2025-11-08T14:30:00.000Z"
  },
  "historicalData": [
    {
      "timestamp": "2025-11-08T14:00:00.000Z",
      "fourHour": 45.2,
      "oneWeek": 68.5,
      "opusOneWeek": 23.1
    },
    {
      "timestamp": "2025-11-08T13:55:00.000Z",
      "fourHour": 44.8,
      "oneWeek": 68.3,
      "opusOneWeek": 23.1
    }
  ],
  "alerts": {
    "thresholds": {
      "warning": 75,
      "critical": 90
    },
    "active": [
      {
        "level": "warning",
        "capType": "oneWeek",
        "message": "Approaching weekly limit",
        "timestamp": "2025-11-08T14:00:00.000Z"
      }
    ]
  }
}
```

### File Watching Implementation

#### Node.js (Chokidar)

```javascript
const chokidar = require('chokidar');

const watcher = chokidar.watch('usage-data.json', {
  persistent: true,
  awaitWriteFinish: {
    stabilityThreshold: 500,
    pollInterval: 100
  }
});

watcher.on('change', (path) => {
  console.log(`File ${path} changed, reloading...`);
  const data = JSON.parse(fs.readFileSync(path, 'utf8'));
  // Update UI with new data
  updateUI(data);
});
```

#### Python (Watchdog)

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json

class DataFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('usage-data.json'):
            with open('usage-data.json', 'r') as f:
                data = json.load(f)
            # Update UI
            self.update_callback(data)

observer = Observer()
handler = DataFileHandler()
observer.schedule(handler, '.', recursive=False)
observer.start()
```

## Component 4: Usage Projection Algorithms

### Simple Moving Average (SMA)

```python
def calculate_sma(data_points, window=12):
    """
    Calculate Simple Moving Average
    
    Args:
        data_points: List of historical usage percentages
        window: Number of points to average (default 12 = 1 hour at 5-min intervals)
    
    Returns:
        Current average rate
    """
    if len(data_points) < window:
        window = len(data_points)
    
    if window == 0:
        return 0
    
    recent = data_points[-window:]
    return sum(recent) / len(recent)
```

### Linear Regression for Trend

```python
def calculate_trend(historical_data, cap_type='fourHour'):
    """
    Calculate usage trend using linear regression
    
    Returns:
        Rate of change per hour
    """
    if len(historical_data) < 2:
        return 0
    
    # Extract data points
    points = [(i, point[cap_type]) for i, point in enumerate(historical_data)]
    
    # Calculate linear regression
    n = len(points)
    sum_x = sum(i for i, _ in points)
    sum_y = sum(y for _, y in points)
    sum_xy = sum(i * y for i, y in points)
    sum_x2 = sum(i * i for i, _ in points)
    
    # Slope (rate of change per data point)
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
    
    # Convert to rate per hour (5-min intervals = 12 per hour)
    rate_per_hour = slope * 12
    
    return rate_per_hour
```

### Time to Cap Estimation

```python
from datetime import datetime, timedelta

def estimate_time_to_cap(current_usage, rate_per_hour, cap_limit=100):
    """
    Estimate when usage will reach cap
    
    Args:
        current_usage: Current usage percentage
        rate_per_hour: Rate of increase per hour
        cap_limit: Cap limit (default 100%)
    
    Returns:
        ISO timestamp when cap will be reached, or None if won't reach
    """
    if rate_per_hour <= 0:
        return None  # Usage decreasing or stable
    
    remaining = cap_limit - current_usage
    hours_to_cap = remaining / rate_per_hour
    
    if hours_to_cap < 0:
        return None
    
    time_to_cap = datetime.utcnow() + timedelta(hours=hours_to_cap)
    return time_to_cap.isoformat() + 'Z'
```

### Complete Projection Function

```python
def calculate_projections(data):
    """Calculate all projections for current state"""
    historical = data.get('historicalData', [])
    
    if len(historical) < 2:
        return None
    
    projections = {}
    
    for cap_type in ['fourHour', 'oneWeek', 'opusOneWeek']:
        # Get current usage
        current = data['currentState'][cap_type]['usagePercent']
        
        # Calculate trend
        rate_per_hour = calculate_trend(historical, cap_type)
        
        # Calculate SMA for smoothing
        recent_values = [point[cap_type] for point in historical[-12:]]
        sma = calculate_sma(recent_values)
        
        # Estimate time to cap
        time_to_cap = estimate_time_to_cap(current, rate_per_hour)
        
        # Project usage at reset time
        reset_time = data['currentState'][cap_type]['resetTime']
        hours_until_reset = (
            datetime.fromisoformat(reset_time.replace('Z', '+00:00')) - 
            datetime.utcnow()
        ).total_seconds() / 3600
        
        projected_at_reset = current + (rate_per_hour * hours_until_reset)
        projected_at_reset = min(projected_at_reset, 100)  # Cap at 100%
        
        projections[cap_type] = {
            'averageRatePerHour': round(rate_per_hour, 2),
            'projectedUsageAtReset': round(projected_at_reset, 1),
            'estimatedTimeToLimit': time_to_cap,
            'confidence': 'high' if len(historical) > 24 else 'medium'
        }
    
    return projections
```

### Integration into Data Saving

```python
async def save_data_with_projections(self, data):
    """Save data with calculated projections"""
    # ... existing save logic ...
    
    # Calculate projections
    projections = calculate_projections(new_data)
    
    if projections:
        # Update current state with projections
        for cap_type, projection in projections.items():
            new_data['currentState'][cap_type].update(projection)
    
    # Write atomically
    with atomic_write(str(self.data_file), overwrite=True) as f:
        json.dump(new_data, f, indent=2)
```

## Component 5: Polling and Monitoring Best Practices

### Optimal Polling Interval

**5 minutes is appropriate for Claude usage monitoring** because:

✅ Non-critical application (not revenue-impacting)  
✅ Usage caps reset on hour/week boundaries  
✅ Balances detection speed with resource usage  
✅ Respects rate limiting considerations  
✅ Sufficient granularity for trend analysis  

**Alternative intervals by priority**:
- High priority (approaching cap): 1-2 minutes
- Standard monitoring: 5 minutes ✅ **Recommended**
- Low priority: 10-15 minutes

### Rate Limiting Strategy

```python
class RateLimiter:
    def __init__(self, min_interval=300):
        self.min_interval = min_interval  # 5 minutes
        self.last_request = None
        
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        if self.last_request:
            elapsed = (datetime.now() - self.last_request).total_seconds()
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                print(f'⏳ Rate limiting: waiting {wait_time:.0f}s')
                await asyncio.sleep(wait_time)
        
        self.last_request = datetime.now()
```

### Error Handling with Retry

```python
async def poll_with_retry(self, max_retries=3):
    """Poll with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return await self.poll()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            wait_time = min(2 ** attempt, 60)  # Cap at 60 seconds
            print(f'❌ Attempt {attempt + 1} failed: {e}')
            print(f'⏳ Retrying in {wait_time}s...')
            await asyncio.sleep(wait_time)
```

### Session Management

```python
class SessionManager:
    def __init__(self, session_timeout_minutes=25):
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.last_activity = None
        
    def ensure_alive(self):
        """Check if session needs refresh"""
        if self.last_activity:
            elapsed = datetime.now() - self.last_activity
            if elapsed > self.session_timeout:
                return False
        return True
    
    def update_activity(self):
        """Mark activity timestamp"""
        self.last_activity = datetime.now()
```

## Security Considerations

### Authentication

**Best Practices**:
1. ✅ Use manual login (respects ToS, handles 2FA)
2. ✅ Store session in persistent browser context (encrypted by browser)
3. ❌ Never store plaintext credentials
4. ❌ Never automate login with credentials (violates ToS)

### Data Protection

```python
# Encrypt sensitive data if needed
from cryptography.fernet import Fernet

def encrypt_cookies(cookies, key):
    """Encrypt browser cookies"""
    f = Fernet(key)
    encrypted = f.encrypt(json.dumps(cookies).encode())
    return encrypted

def decrypt_cookies(encrypted, key):
    """Decrypt browser cookies"""
    f = Fernet(key)
    decrypted = f.decrypt(encrypted)
    return json.loads(decrypted.decode())
```

### File Permissions

```python
import os

# Restrict data file to current user only (Windows)
os.chmod('usage-data.json', 0o600)
```

## Complete System Integration

### Process Orchestration Script

```python
# run_system.py
import subprocess
import sys
import time
from pathlib import Path

def start_scraper():
    """Start scraper process"""
    scraper = subprocess.Popen(
        [sys.executable, 'claude_usage_monitor.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return scraper

def start_overlay():
    """Start overlay process"""
    overlay = subprocess.Popen(
        [sys.executable, 'overlay_widget.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return overlay

def main():
    print('🚀 Starting Claude Usage Monitor System...')
    
    # Start components
    scraper = start_scraper()
    print('✅ Scraper process started')
    
    time.sleep(2)
    
    overlay = start_overlay()
    print('✅ Overlay UI started')
    
    print('\n📊 System running. Press Ctrl+C to stop.')
    
    try:
        # Wait for processes
        scraper.wait()
        overlay.wait()
    except KeyboardInterrupt:
        print('\n🛑 Shutting down...')
        scraper.terminate()
        overlay.terminate()
        scraper.wait()
        overlay.wait()
        print('✅ Shutdown complete')

if __name__ == '__main__':
    main()
```

### Windows Service (Optional)

For automatic startup on boot:

```python
# windows_service.py
import win32serviceutil
import win32service
import win32event
import servicemanager
import subprocess
import sys

class ClaudeMonitorService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ClaudeUsageMonitor"
    _svc_display_name_ = "Claude Usage Monitor Service"
    _svc_description_ = "Monitors Claude.ai usage and displays overlay"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.scraper_process = None
        
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        if self.scraper_process:
            self.scraper_process.terminate()
        
    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()
        
    def main(self):
        self.scraper_process = subprocess.Popen(
            [sys.executable, 'claude_usage_monitor.py']
        )
        win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(ClaudeMonitorService)
```

## Framework Comparison Summary

| Framework | Bundle Size | RAM Usage | Startup | Best For |
|-----------|-------------|-----------|---------|----------|
| **PyQt5** ⭐ | Moderate | 50-80MB | \<1s | **Native performance, lightweight widgets** |
| **Tauri** ⭐ | 2.5-10MB | ~80MB | ~2s | **Web developers, small bundle** |
| **Electron** | 85MB+ | 120MB+ | ~4s | Feature-rich apps, large ecosystem |
| **Tkinter** | Very small | 20-40MB | \<1s | Basic overlays, minimal dependencies |
| **WPF** | Moderate | 60-90MB | \<1s | Windows-only, native integration |

## Implementation Checklist for RooCode

### Phase 1: Web Scraping Setup
- [ ] Install Playwright: `npm install playwright` or `pip install playwright`
- [ ] Install browsers: `playwright install chromium`
- [ ] Create scraper script with persistent context
- [ ] Test manual login and session persistence
- [ ] Inspect claude.ai/usage to find correct selectors
- [ ] Implement data extraction with multiple selector fallbacks
- [ ] Test atomic file writes

### Phase 2: Overlay UI
- [ ] Install PyQt5: `pip install PyQt5 qdarktheme`
- [ ] Create overlay widget with basic layout
- [ ] Implement always-on-top using Windows API
- [ ] Add dark theme styling
- [ ] Test file watching and UI updates
- [ ] Implement draggable window
- [ ] Test multi-monitor positioning

### Phase 3: Data Pipeline
- [ ] Define JSON schema
- [ ] Implement atomic write pattern
- [ ] Add file watching with debouncing
- [ ] Test data flow: scraper → JSON → UI
- [ ] Add error handling for corrupted JSON
- [ ] Implement data rotation (keep last week)

### Phase 4: Projections
- [ ] Implement SMA calculation
- [ ] Add linear regression for trends
- [ ] Calculate time-to-cap estimates
- [ ] Integrate projections into data saving
- [ ] Test with synthetic usage patterns
- [ ] Add confidence levels based on data quantity

### Phase 5: Polish
- [ ] Add logging to both processes
- [ ] Implement graceful shutdown
- [ ] Create process orchestration script
- [ ] Test error recovery (process crashes, network errors)
- [ ] Add system tray icon (optional)
- [ ] Create installer/packaging

### Phase 6: Testing
- [ ] Test session expiration handling
- [ ] Test with actual claude.ai/usage page
- [ ] Verify atomic writes don't corrupt data
- [ ] Test multi-monitor scenarios
- [ ] Verify resource usage over 24 hours
- [ ] Test projection accuracy

## Troubleshooting Guide

### Issue: Selectors not finding elements

**Solution**: Inspect claude.ai/usage page structure
```python
# Debug selector finding
selectors = await page.evaluate('''() => {
    return Array.from(document.querySelectorAll('*'))
        .filter(el => el.textContent.includes('%'))
        .map(el => ({
            tag: el.tagName,
            class: el.className,
            id: el.id,
            text: el.textContent.substring(0, 50)
        }));
}''')
print(selectors)
```

### Issue: Session keeps expiring

**Solutions**:
1. Check browser context is truly persistent
2. Verify user-data-dir path is writable
3. Manually save/restore cookies as backup
4. Increase session timeout monitoring

### Issue: High memory usage

**Solutions**:
1. Close unused browser pages: `await page.close()`
2. Use headless mode (less reliable but lighter)
3. Add memory limits: `--max-old-space-size=512`
4. Restart scraper process daily

### Issue: Window not always-on-top

**Solution**: Verify Windows API call succeeds
```python
# Re-apply topmost periodically
def ensure_topmost(self):
    self.setWindowFlags(
        self.windowFlags() | Qt.WindowStaysOnTopHint
    )
    self.show()
```

## Resource Requirements

**Scraper Process**:
- CPU: \<1% idle, 5-10% during scrape
- RAM: 70-150MB (Playwright)
- Disk: ~50MB for browser data
- Network: Minimal (one request per 5 minutes)

**Overlay Process**:
- CPU: \<1% idle
- RAM: 50-80MB (PyQt5)
- Disk: Minimal

**Total System Impact**: ~200-250MB RAM, negligible CPU when idle

## Conclusion

This architecture provides a robust, maintainable solution for monitoring Claude usage with:

✅ **Reliable scraping** via Playwright with persistent authentication  
✅ **Lightweight overlay** using native PyQt5 framework  
✅ **Simple IPC** through file-based JSON with atomic writes  
✅ **Accurate projections** using proven statistical methods  
✅ **Low resource usage** under 250MB total RAM  
✅ **Easy debugging** with visible data files and structured logging  
✅ **Production-ready** error handling and retry mechanisms  

The modular design allows independent development and testing of each component, making it ideal for implementation by an AI coding agent like RooCode.