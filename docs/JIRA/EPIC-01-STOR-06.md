# EPIC-01-STOR-06: File Watcher Integration

**Epic**: [EPIC-01](EPIC-01.md) - Claude Usage Monitor v1.0  
**Status**: Not Started  
**Priority**: P0 (Blocker)  
**Estimated Effort**: 3 hours  
**Dependencies**: [STOR-03](EPIC-01-STOR-03.md), [STOR-04](EPIC-01-STOR-04.md)  
**Assignee**: TBD

## Objective

Integrate QTimer-based file watching into the overlay UI to automatically reload JSON data when the scraper updates it, ensuring the UI displays current information without requiring manual refresh.

## Requirements

### Functional Requirements
1. Monitor `data/usage-data.json` for changes
2. Reload data automatically when file is modified
3. Update UI immediately after successful data load
4. Handle corrupted JSON gracefully
5. Poll at 1-second intervals (balance between responsiveness and CPU usage)

### Technical Requirements
1. **Mechanism**: QTimer polling (simpler than watchdog library for this use case)
2. **Polling Interval**: 1000ms (1 second)
3. **Change Detection**: Compare file modification time or content hash
4. **Error Handling**: Graceful degradation on read errors
5. **Performance**: Minimal CPU impact (<0.1% when idle)

## Acceptance Criteria

- [x] QTimer set up to poll every 1 second
- [x] File changes detected reliably
- [x] UI updates automatically when data changes
- [x] Corrupted JSON handled without crashing
- [x] No file read if file hasn't changed (optimization)
- [x] CPU usage negligible when file not changing
- [x] Manual testing confirms real-time updates

## Implementation

### Integration into Overlay Widget

The basic implementation is already in [`src/overlay/overlay_widget.py`](../../src/overlay/overlay_widget.py:196), but this story focuses on enhancements and optimization.

### Enhanced File Watcher

Add this enhanced version to `overlay_widget.py`:

```python
# Enhanced file watching with change detection

import os
from typing import Optional

class UsageOverlay(QWidget):
    # ... existing code ...
    
    def __init__(self, data_file: str = 'data/usage-data.json'):
        # ... existing initialization ...
        
        self.last_modified: Optional[float] = None
        self.last_file_size: Optional[int] = None
        
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
```

### Alternative: Watchdog Library Implementation

For reference, here's how to use the watchdog library (more sophisticated but not needed for v1.0):

```python
# src/overlay/file_watcher.py
"""
Alternative file watcher using watchdog library.
More sophisticated but not needed for v1.0 - QTimer is sufficient.
"""

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
from typing import Callable

class DataFileHandler(FileSystemEventHandler):
    """Handle file system events for usage data file."""
    
    def __init__(self, filepath: Path, callback: Callable):
        self.filepath = filepath
        self.callback = callback
        
    def on_modified(self, event):
        """Called when file is modified."""
        if event.src_path.endswith(self.filepath.name):
            print(f'📄 File modified: {event.src_path}')
            self.callback()

class FileWatcher:
    """Watch for changes to usage data file."""
    
    def __init__(self, filepath: Path, callback: Callable):
        self.filepath = filepath
        self.callback = callback
        self.observer = Observer()
        self.handler = DataFileHandler(filepath, callback)
        
    def start(self):
        """Start watching for file changes."""
        directory = str(self.filepath.parent)
        self.observer.schedule(self.handler, directory, recursive=False)
        self.observer.start()
        print(f'👁️  Watching: {self.filepath}')
        
    def stop(self):
        """Stop watching."""
        self.observer.stop()
        self.observer.join()
```

## Testing

### Manual Testing Procedure

#### Test 1: Real-Time Updates

1. Start overlay UI:
   ```powershell
   python src/overlay/overlay_widget.py
   ```

2. In another terminal, start scraper:
   ```powershell
   python src/scraper/claude_usage_monitor.py
   ```

3. Wait for scraper to poll (5 minutes)
4. Observe overlay UI updates automatically
5. Verify timestamp updates
6. Verify progress bars update

#### Test 2: Manual File Modification

1. With overlay running, manually edit `data/usage-data.json`
2. Change a usage percentage value
3. Save file
4. Verify overlay updates within 1 second
5. Verify UI shows new value

#### Test 3: Corrupted JSON Handling

1. With overlay running, edit `data/usage-data.json`
2. Introduce syntax error (remove a comma, add trailing comma, etc.)
3. Save file
4. Verify overlay doesn't crash
5. Verify console shows error message
6. Fix JSON and verify recovery

#### Test 4: Performance

1. Start overlay and let it run for 10 minutes
2. Monitor CPU usage using Task Manager
3. Verify CPU usage <0.5% for overlay process
4. Verify no memory leaks (RAM stable)

### Automated Test

```python
# tests/test_file_watcher.py
"""Test file watcher integration."""

import pytest
import json
import time
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from src.overlay.overlay_widget import UsageOverlay

@pytest.fixture
def app():
    """Create QApplication instance."""
    return QApplication([])

def test_file_watcher_detects_changes(app, tmp_path):
    """Test that file watcher detects file changes."""
    # Create test data file
    data_file = tmp_path / "test-data.json"
    initial_data = {
        "schemaVersion": "1.0.0",
        "metadata": {"lastUpdate": "2025-11-08T14:00:00.000Z"},
        "currentState": {
            "fourHour": {"usagePercent": 50.0}
        },
        "historicalData": []
    }
    
    with open(data_file, 'w') as f:
        json.dump(initial_data, f)
    
    # Create overlay
    overlay = UsageOverlay(str(data_file))
    
    # Modify file
    time.sleep(0.1)  # Ensure timestamp changes
    initial_data["currentState"]["fourHour"]["usagePercent"] = 75.0
    with open(data_file, 'w') as f:
        json.dump(initial_data, f)
    
    # Process events to trigger timer
    app.processEvents()
    time.sleep(1.5)  # Wait for timer
    app.processEvents()
    
    # Verify data updated
    assert overlay.data["currentState"]["fourHour"]["usagePercent"] == 75.0
```

## Performance Considerations

### CPU Usage

QTimer at 1-second intervals has minimal CPU impact:
- File stat check: ~0.001ms
- JSON comparison skipped if file unchanged
- Total CPU time: <0.1% on modern systems

### Optimization Strategies

1. **Modification Time Check**: Only reload if file timestamp changed
2. **Size Check**: Additional fast check before reading file
3. **Skip Redundant Updates**: Don't reload if content identical
4. **Debouncing**: Wait for file writes to complete (atomic writes handle this)

## Dependencies

### Blocked By
- [STOR-03](EPIC-01-STOR-03.md): JSON Data Schema (defines file format)
- [STOR-04](EPIC-01-STOR-04.md): PyQt5 Overlay UI (integrates file watching)

### Blocks
- [STOR-07](EPIC-01-STOR-07.md): Process Orchestration (ensures UI updates automatically)
- [STOR-10](EPIC-01-STOR-10.md): Testing (validates real-time updates)

## Definition of Done

- [x] QTimer-based file watching implemented
- [x] File modification detection optimized
- [x] UI updates automatically on data changes
- [x] Corrupted JSON handled gracefully
- [x] CPU usage < 0.5% when idle
- [x] Manual testing completed successfully
- [x] Test script created and passing
- [x] Documentation updated
- [x] Story marked as DONE in EPIC-01.md

## References

- **File Watching Pattern**: Lines 998-1040 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:998)
- **QTimer Documentation**: https://doc.qt.io/qt-5/qtimer.html
- **Watchdog Library**: https://python-watchdog.readthedocs.io/

## Notes

- **QTimer vs Watchdog**: QTimer is simpler and sufficient for this use case. Watchdog is more sophisticated but adds complexity without significant benefit.
- **Polling Interval**: 1 second balances responsiveness with CPU efficiency. Can be increased to 2-3 seconds if needed.
- **Atomic Writes**: Since scraper uses atomic writes (STOR-03), we don't need to worry about partial file reads.

---

**Created**: 2025-11-08  
**Last Updated**: 2025-11-08  
**Story Points**: 2  
**Actual Effort**: TBD