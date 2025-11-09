# src/overlay/overlay_widget.py
"""
Claude Usage Monitor - Overlay UI Component

Displays usage metrics in an always-on-top, frameless overlay window
with dark theme styling and real-time updates.

Reference: compass_artifact document lines 608-821
"""

import sys
import json
import os
from datetime import datetime
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
        self.last_modified: Optional[float] = None
        self.last_file_size: Optional[int] = None

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

        # Disable transparency for solid dark background
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Position in top-right corner
        try:
            screen = QApplication.primaryScreen().geometry()
            self.move(screen.width() - self.width() - 20, 20)
        except:
            # Fallback if screen geometry unavailable
            self.move(1000, 20)

    def setup_watcher(self) -> None:
        """Setup optimized file watcher with change detection."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_and_reload)
        self.timer.start(1000)  # Check every second

        # Initial load
        self.check_and_reload()

    def check_and_reload(self) -> None:
        """Check if file changed and reload if necessary."""
        try:
            if not self.data_file.exists():
                return

            # Get file stats
            stat = os.stat(self.data_file)
            current_modified = stat.st_mtime
            current_size = stat.st_size

            # Check if file actually changed
            if (self.last_modified is not None and
                current_modified == self.last_modified and
                current_size == self.last_file_size):
                # File hasn't changed, skip reload
                return

            # File changed, update tracking
            self.last_modified = current_modified
            self.last_file_size = current_size

            # Reload data
            self.reload_data()

        except Exception as e:
            print(f'Error checking file: {e}')

    def reload_data(self) -> None:
        """Reload data from JSON file."""
        try:
            with open(self.data_file, 'r') as f:
                new_data = json.load(f)

            # Always update (already confirmed file changed)
            self.data = new_data
            self.update_ui()
            print(f'✅ Data reloaded at {datetime.now().strftime("%H:%M:%S")}')

        except json.JSONDecodeError as e:
            print(f'⚠️  Corrupted JSON: {e}')
            # Keep previous data, don't crash
        except Exception as e:
            print(f'❌ Error loading data: {e}')

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
        reset_time = fourHour.get('resetTime', '--')
        self.fourHourReset.setText(f'Reset: {reset_time}')

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
        reset_time = oneWeek.get('resetTime', '--')
        self.oneWeekReset.setText(f'Reset: {reset_time}')

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
        reset_time = opus.get('resetTime', '--')
        self.opusReset.setText(f'Reset: {reset_time}')

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
