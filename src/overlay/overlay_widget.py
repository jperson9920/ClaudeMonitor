<<<<<<< HEAD
=======
# src/overlay/overlay_widget.py
>>>>>>> claude/epic-01-complete-011CUwRBinhBsie6yCw3DBYD
"""
Claude Usage Monitor - Overlay UI Component

Displays usage metrics in an always-on-top, frameless overlay window
with dark theme styling and real-time updates.

<<<<<<< HEAD
Reference: EPIC-01-STOR-04 (PyQt5 Overlay UI with Always-On-Top)
Reference: EPIC-01-STOR-06 (File Watcher Integration)
=======
Reference: compass_artifact document lines 608-821
>>>>>>> claude/epic-01-complete-011CUwRBinhBsie6yCw3DBYD
"""

import sys
import json
import os
<<<<<<< HEAD
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QLabel,
        QVBoxLayout, QProgressBar
    )
    from PyQt5.QtGui import QPalette, QColor
    import qdarktheme
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("Warning: PyQt5 not available. UI will not be functional.")
=======
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
>>>>>>> claude/epic-01-complete-011CUwRBinhBsie6yCw3DBYD


class UsageOverlay(QWidget):
    """Main overlay window for displaying usage metrics."""

    def __init__(self, data_file: str = 'data/usage-data.json'):
        """
        Initialize the overlay widget.

        Args:
            data_file: Path to JSON data file (relative to project root)
        """
<<<<<<< HEAD
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 is required for overlay functionality")

=======
>>>>>>> claude/epic-01-complete-011CUwRBinhBsie6yCw3DBYD
        super().__init__()

        # Resolve data file path
        project_root = Path(__file__).parent.parent.parent
        self.data_file = project_root / data_file

        self.data: Dict[str, Any] = {}
        self.drag_position = None
<<<<<<< HEAD

        # File watching state
=======
>>>>>>> claude/epic-01-complete-011CUwRBinhBsie6yCw3DBYD
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
<<<<<<< HEAD
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Title
        title = QLabel('Claude Usage Monitor')
        title.setStyleSheet('font-size: 16px; font-weight: bold; color: #ffffff;')
        layout.addWidget(title)

        # Separator
        separator = QLabel('')
        separator.setFixedHeight(1)
        separator.setStyleSheet('background-color: #3e3e42;')
        layout.addWidget(separator)

        # 4-Hour Cap Section
        four_hour_label = QLabel('4-Hour Cap')
        four_hour_label.setStyleSheet('font-size: 12px; font-weight: bold; margin-top: 5px;')
        layout.addWidget(four_hour_label)

        self.fourHourBar = QProgressBar()
        self.fourHourBar.setMaximum(100)
        layout.addWidget(self.fourHourBar)

        self.fourHourLabel = QLabel('0 / 0 (0.0%)')
        self.fourHourLabel.setStyleSheet('font-size: 11px; color: #cccccc;')
        layout.addWidget(self.fourHourLabel)

        # 1-Week Cap Section
        one_week_label = QLabel('1-Week Cap')
        one_week_label.setStyleSheet('font-size: 12px; font-weight: bold; margin-top: 10px;')
        layout.addWidget(one_week_label)

        self.oneWeekBar = QProgressBar()
        self.oneWeekBar.setMaximum(100)
        layout.addWidget(self.oneWeekBar)

        self.oneWeekLabel = QLabel('0 / 0 (0.0%)')
        self.oneWeekLabel.setStyleSheet('font-size: 11px; color: #cccccc;')
        layout.addWidget(self.oneWeekLabel)

        # Opus 1-Week Cap Section
        opus_label = QLabel('Opus 1-Week Cap')
        opus_label.setStyleSheet('font-size: 12px; font-weight: bold; margin-top: 10px;')
        layout.addWidget(opus_label)

        self.opusBar = QProgressBar()
        self.opusBar.setMaximum(100)
        layout.addWidget(self.opusBar)

        self.opusLabel = QLabel('0 / 0 (0.0%)')
        self.opusLabel.setStyleSheet('font-size: 11px; color: #cccccc;')
        layout.addWidget(self.opusLabel)

        # Spacer
        layout.addStretch()

        # Last update timestamp
        self.lastUpdate = QLabel('Last update: Never')
        self.lastUpdate.setStyleSheet('font-size: 10px; color: #888888; margin-top: 10px;')
=======
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
>>>>>>> claude/epic-01-complete-011CUwRBinhBsie6yCw3DBYD
        layout.addWidget(self.lastUpdate)

        self.setLayout(layout)

        # Apply dark theme
<<<<<<< HEAD
        if PYQT_AVAILABLE:
            try:
                qdarktheme.setup_theme('dark')
            except Exception:
                pass  # Fallback to default theme
=======
        qdarktheme.setup_theme()
>>>>>>> claude/epic-01-complete-011CUwRBinhBsie6yCw3DBYD

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
<<<<<<< HEAD
                height: 24px;
                color: #ffffff;
                font-weight: bold;
=======
                height: 20px;
>>>>>>> claude/epic-01-complete-011CUwRBinhBsie6yCw3DBYD
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
<<<<<<< HEAD
        self.setFixedSize(320, 450)
=======
        self.setFixedSize(300, 400)
>>>>>>> claude/epic-01-complete-011CUwRBinhBsie6yCw3DBYD

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
<<<<<<< HEAD
        except Exception:
            # Fallback positioning if screen geometry unavailable
            self.move(100, 100)

    def setup_watcher(self) -> None:
        """Setup file watcher to reload data."""
        # Use QTimer for simple polling (1-second interval)
=======
        except:
            # Fallback if screen geometry unavailable
            self.move(1000, 20)

    def setup_watcher(self) -> None:
        """Setup optimized file watcher with change detection."""
>>>>>>> claude/epic-01-complete-011CUwRBinhBsie6yCw3DBYD
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
<<<<<<< HEAD
                    current_size == self.last_file_size):
=======
                current_size == self.last_file_size):
>>>>>>> claude/epic-01-complete-011CUwRBinhBsie6yCw3DBYD
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
<<<<<<< HEAD
            with open(self.data_file, 'r', encoding='utf-8') as f:
                new_data = json.load(f)

            # Update data and UI
            self.data = new_data
            self.update_ui()

        except json.JSONDecodeError as e:
            print(f'Warning: Corrupted JSON: {e}')
            # Keep previous data, don't crash
        except Exception as e:
            print(f'Error loading data: {e}')

    def update_ui(self) -> None:
        """Update UI with current data."""
        metrics = self.data.get('metrics', {})

        if not metrics:
            return

        # Update 4-Hour Cap
        self.update_cap_display(
            metrics.get('fourHourCap', {}),
            self.fourHourBar,
            self.fourHourLabel
        )

        # Update 1-Week Cap
        self.update_cap_display(
            metrics.get('weekCap', {}),
            self.oneWeekBar,
            self.oneWeekLabel
        )

        # Update Opus 1-Week Cap
        self.update_cap_display(
            metrics.get('opusWeekCap', {}),
            self.opusBar,
            self.opusLabel
        )

        # Update last update timestamp
        last_updated = self.data.get('lastUpdated', 'Never')
        if last_updated != 'Never':
            try:
                dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                last_updated = dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                pass

        self.lastUpdate.setText(f'Last update: {last_updated}')

    def update_cap_display(
        self,
        cap_data: Dict[str, Any],
        progress_bar: QProgressBar,
        label: QLabel
    ) -> None:
        """
        Update a single cap's display.

        Args:
            cap_data: Cap data dictionary
            progress_bar: Progress bar widget
            label: Label widget
        """
        used = cap_data.get('used', 0)
        limit = cap_data.get('limit', 0)
        percentage = cap_data.get('percentage', 0.0)

        # Update progress bar
        progress_bar.setValue(int(percentage))

        # Update label
        label.setText(f'{used} / {limit} ({percentage:.1f}%)')

        # Color coding
        if percentage >= 90:
            # Red
            progress_bar.setStyleSheet('''
                QProgressBar::chunk {
                    background-color: #e74c3c;
                    border-radius: 3px;
                }
            ''')
        elif percentage >= 75:
            # Orange
            progress_bar.setStyleSheet('''
                QProgressBar::chunk {
                    background-color: #f39c12;
                    border-radius: 3px;
                }
            ''')
        else:
            # Blue
            progress_bar.setStyleSheet('''
                QProgressBar::chunk {
                    background-color: #007acc;
                    border-radius: 3px;
                }
            ''')
=======
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
>>>>>>> claude/epic-01-complete-011CUwRBinhBsie6yCw3DBYD

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
<<<<<<< HEAD
    if not PYQT_AVAILABLE:
        print("Error: PyQt5 is not installed. Please install it with:")
        print("  pip install PyQt5 qdarktheme")
        sys.exit(1)

=======
>>>>>>> claude/epic-01-complete-011CUwRBinhBsie6yCw3DBYD
    app = QApplication(sys.argv)
    overlay = UsageOverlay('data/usage-data.json')
    overlay.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
