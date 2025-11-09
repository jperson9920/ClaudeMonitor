# EPIC-01-STOR-04: PyQt5 Overlay UI with Always-On-Top

**Epic**: [EPIC-01](EPIC-01.md) - Claude Usage Monitor v1.0  
**Status**: Not Started  
**Priority**: P0 (Blocker)  
**Estimated Effort**: 10 hours  
**Dependencies**: [STOR-01](EPIC-01-STOR-01.md), [STOR-03](EPIC-01-STOR-03.md)  
**Assignee**: TBD

## Objective

Build a PyQt5-based overlay window that displays Claude usage metrics in an always-on-top, frameless window with dark theme styling, progress bars, and draggable positioning.

## Requirements

### Functional Requirements
1. Always-on-top window that stays above all other applications
2. Frameless window design (no title bar or borders)
3. Dark theme using qdarktheme library
4. Three progress bars for: 4-hour cap, 1-week cap, Opus 1-week cap
5. Color-coded progress bars (blue <75%, orange 75-90%, red >90%)
6. Display reset times for each cap
7. Display last update timestamp
8. Draggable window (click and drag anywhere to move)
9. Positioned in top-right corner by default
10. Fixed size window (300x400 pixels)

### Technical Requirements
1. **Framework**: PyQt5 5.15.10
2. **Theme**: qdarktheme 2.1.0
3. **Window Flags**: 
   - `Qt.WindowStaysOnTopHint`
   - `Qt.FramelessWindowHint`
   - `Qt.Tool` (exclude from taskbar)
4. **Windows API**: Use ctypes for extended window styles if needed
5. **Layout**: QVBoxLayout with consistent spacing
6. **Update Mechanism**: Read from JSON file (via file watcher from STOR-06)

## Acceptance Criteria

- [x] PyQt5 window opens in top-right corner
- [x] Window stays always-on-top over all applications
- [x] Frameless design with dark theme applied
- [x] Three progress bars display with correct values
- [x] Progress bars change color based on percentage thresholds
- [x] Reset times and last update timestamp displayed
- [x] Window can be dragged by clicking anywhere
- [x] Window size fixed at 300x400 pixels
- [x] Dark theme applied correctly (background #1e1e1e, text #cccccc)
- [x] UI updates when data changes (integration with STOR-06)

## Implementation

### File Location

Create [`src/overlay/overlay_widget.py`](../../src/overlay/overlay_widget.py)

### Code Implementation

```python
# src/overlay/overlay_widget.py
"""
Claude Usage Monitor - Overlay UI Component

Displays usage metrics in an always-on-top, frameless overlay window
with dark theme styling and real-time updates.

Reference: compass_artifact document lines 608-821
"""

import sys
import json
import ctypes
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, 
    QVBoxLayout, QProgressBar
)
from PyQt5.QtGui import QPalette, QColor
import qdarktheme


class UsageOverlay(QWidget):
    """Main overlay window for displaying usage metrics."""
    
    def __init__(self, data_file: str = 'data/usage-data.json'):
        """
        Initialize the overlay widget.
        
        Args:
            data_file: Path to JSON data file (relative to project root)
        """
        super().__init__()
        
        # Resolve data file path
        project_root = Path(__file__).parent.parent.parent
        self.data_file = project_root / data_file
        
        self.data: Dict[str, Any] = {}
        self.drag_position = None
        
        # Initialize UI components
        self.init_ui()
        self.make_overlay()
        self.setup_watcher()
        
    def init_ui(self) -> None:
        """Initialize UI components and layout."""
        self.setWindowTitle('Claude Usage Monitor')
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Title
        title = QLabel('Claude Usage Monitor')
        title.setStyleSheet('font-size: 14px; font-weight: bold;')
        layout.addWidget(title)
        
        # 4-Hour Cap Section
        layout.addWidget(QLabel('4-Hour Cap:'))
        self.fourHourBar = QProgressBar()
        self.fourHourLabel = QLabel('0%')
        self.fourHourReset = QLabel('Reset: --')
        layout.addWidget(self.fourHourBar)
        layout.addWidget(self.fourHourLabel)
        layout.addWidget(self.fourHourReset)
        
        # 1-Week Cap Section
        layout.addWidget(QLabel('1-Week Cap:'))
        self.oneWeekBar = QProgressBar()
        self.oneWeekLabel = QLabel('0%')
        self.oneWeekReset = QLabel('Reset: --')
        layout.addWidget(self.oneWeekBar)
        layout.addWidget(self.oneWeekLabel)
        layout.addWidget(self.oneWeekReset)
        
        # Opus 1-Week Cap Section
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
        
        # Set fixed size
        self.setFixedSize(300, 400)
        
    def make_overlay(self) -> None:
        """Configure window as always-on-top overlay."""
        # Remove window frame, make always-on-top
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint |
            Qt.Tool  # Excludes from taskbar
        )
        
        # Optional: Make click-through (disabled by default for dragging)
        # self.make_clickthrough()
        
        # Disable transparency for solid dark background
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # Position in top-right corner
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20, 20)
        
    def make_clickthrough(self) -> None:
        """
        Make window click-through using Windows API.
        
        WARNING: This disables dragging. Only enable if click-through is needed.
        """
        hwnd = self.winId().__int__()
        
        GWL_EXSTYLE = -20
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_LAYERED = 0x00080000
        
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(
            hwnd, 
            GWL_EXSTYLE, 
            style | WS_EX_TRANSPARENT | WS_EX_LAYERED
        )
        
    def setup_watcher(self) -> None:
        """Setup file watcher to reload data."""
        # Use QTimer for simple polling (1-second interval)
        # More sophisticated file watching in STOR-06
        self.timer = QTimer()
        self.timer.timeout.connect(self.reload_data)
        self.timer.start(1000)  # Check every second
        
        # Initial load
        self.reload_data()
        
    def reload_data(self) -> None:
        """Reload data from JSON file."""
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
            
    def update_ui(self) -> None:
        """Update UI with current data."""
        state = self.data.get('currentState', {})
        
        if not state:
            return
        
        # 4-Hour Cap
        fourHour = state.get('fourHour', {})
        percent = fourHour.get('usagePercent', 0)
        self.fourHourBar.setValue(int(percent))
        self.fourHourLabel.setText(f'{percent:.1f}%')
        self.fourHourReset.setText(f'Reset: {fourHour.get("resetTime", "--")}')
        
        # Color coding for 4-hour cap
        if percent >= 90:
            self.fourHourBar.setStyleSheet(
                'QProgressBar::chunk { background-color: #e74c3c; }'
            )
        elif percent >= 75:
            self.fourHourBar.setStyleSheet(
                'QProgressBar::chunk { background-color: #f39c12; }'
            )
        else:
            self.fourHourBar.setStyleSheet(
                'QProgressBar::chunk { background-color: #007acc; }'
            )
        
        # 1-Week Cap
        oneWeek = state.get('oneWeek', {})
        percent = oneWeek.get('usagePercent', 0)
        self.oneWeekBar.setValue(int(percent))
        self.oneWeekLabel.setText(f'{percent:.1f}%')
        self.oneWeekReset.setText(f'Reset: {oneWeek.get("resetTime", "--")}')
        
        # Color coding for 1-week cap
        if percent >= 90:
            self.oneWeekBar.setStyleSheet(
                'QProgressBar::chunk { background-color: #e74c3c; }'
            )
        elif percent >= 75:
            self.oneWeekBar.setStyleSheet(
                'QProgressBar::chunk { background-color: #f39c12; }'
            )
        else:
            self.oneWeekBar.setStyleSheet(
                'QProgressBar::chunk { background-color: #007acc; }'
            )
        
        # Opus 1-Week Cap
        opus = state.get('opusOneWeek', {})
        percent = opus.get('usagePercent', 0)
        self.opusBar.setValue(int(percent))
        self.opusLabel.setText(f'{percent:.1f}%')
        self.opusReset.setText(f'Reset: {opus.get("resetTime", "--")}')
        
        # Color coding for Opus cap
        if percent >= 90:
            self.opusBar.setStyleSheet(
                'QProgressBar::chunk { background-color: #e74c3c; }'
            )
        elif percent >= 75:
            self.opusBar.setStyleSheet(
                'QProgressBar::chunk { background-color: #f39c12; }'
            )
        else:
            self.opusBar.setStyleSheet(
                'QProgressBar::chunk { background-color: #007acc; }'
            )
        
        # Last update timestamp
        timestamp = self.data.get('metadata', {}).get('lastUpdate', 'Never')
        self.lastUpdate.setText(f'Last update: {timestamp}')
        
    def mousePressEvent(self, event) -> None:
        """Enable dragging the window."""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event) -> None:
        """Handle window dragging."""
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()


def main():
    """Main entry point for overlay UI."""
    app = QApplication(sys.argv)
    overlay = UsageOverlay('data/usage-data.json')
    overlay.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
```

## Testing

### Manual Testing Procedure

#### Test 1: Window Appearance

1. Create example data file using STOR-03's example generator
2. Run overlay:
   ```powershell
   python src/overlay/overlay_widget.py
   ```
3. Verify window appears in top-right corner
4. Verify dark theme is applied
5. Verify three progress bars are visible
6. Verify all labels display correctly

#### Test 2: Always-On-Top

1. With overlay running, open other applications
2. Maximize a browser window
3. Verify overlay stays on top
4. Try different application types (VS Code, File Explorer, etc.)
5. Verify overlay remains visible over all windows

#### Test 3: Dragging

1. Click on the overlay window
2. Drag to different positions
3. Verify window moves smoothly
4. Verify window can be positioned anywhere on screen

#### Test 4: Multi-Monitor

If multiple monitors available:
1. Drag overlay to secondary monitor
2. Verify it works correctly
3. Restart overlay (should remember last position if implemented)

#### Test 5: Color Coding

1. Modify example data to have different percentages:
   - Set fourHour to 50% (expect blue)
   - Set oneWeek to 80% (expect orange)
   - Set opusOneWeek to 95% (expect red)
2. Reload data
3. Verify colors change correctly

## Multi-Monitor Support

Add this method to support multiple monitors:

```python
def position_on_monitor(self, monitor_index: int = 0) -> None:
    """
    Position widget on specific monitor.
    
    Args:
        monitor_index: Monitor index (0 for primary, 1+ for secondary)
    """
    desktop = QApplication.desktop()
    
    if monitor_index < desktop.screenCount():
        screen_geometry = desktop.screenGeometry(monitor_index)
        # Top-right corner of selected monitor
        self.move(
            screen_geometry.x() + screen_geometry.width() - self.width() - 20,
            screen_geometry.y() + 20
        )
```

## Dependencies

### Blocked By
- [STOR-01](EPIC-01-STOR-01.md): Project Setup (needs PyQt5 installed)
- [STOR-03](EPIC-01-STOR-03.md): JSON Data Schema (reads data in this format)

### Blocks
- [STOR-06](EPIC-01-STOR-06.md): File Watcher (integrates with this UI)
- [STOR-07](EPIC-01-STOR-07.md): Process Orchestration (launches this UI)
- [STOR-10](EPIC-01-STOR-10.md): Testing (validates UI works)

## Definition of Done

- [ ] `overlay_widget.py` created with complete implementation
- [ ] Window opens in top-right corner
- [ ] Always-on-top functionality works
- [ ] Frameless design with dark theme applied
- [ ] Three progress bars display correctly
- [ ] Color coding works (blue/orange/red)
- [ ] Window is draggable
- [ ] Data updates from JSON file
- [ ] All manual tests passed
- [ ] Multi-monitor support tested (if available)
- [ ] Story marked as DONE in EPIC-01.md

## References

- **Source Implementation**: Lines 608-821 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:608)
- **Multi-Monitor Support**: Lines 823-837 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:823)
- **PyQt5 Documentation**: https://www.riverbankcomputing.com/static/Docs/PyQt5/

---

**Created**: 2025-11-08  
**Last Updated**: 2025-11-08  
**Story Points**: 5  
**Actual Effort**: TBD