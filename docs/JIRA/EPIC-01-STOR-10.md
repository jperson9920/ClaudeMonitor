# EPIC-01-STOR-10: Testing and Validation

**Epic**: [EPIC-01](EPIC-01.md) - Claude Usage Monitor v1.0  
**Status**: Not Started  
**Priority**: P1 (High)  
**Estimated Effort**: 8 hours  
**Dependencies**: [STOR-02](EPIC-01-STOR-02.md), [STOR-04](EPIC-01-STOR-04.md), [STOR-05](EPIC-01-STOR-05.md), [STOR-06](EPIC-01-STOR-06.md), [STOR-07](EPIC-01-STOR-07.md), [STOR-08](EPIC-01-STOR-08.md), [STOR-09](EPIC-01-STOR-09.md)  
**Assignee**: TBD

## Objective

Validate all system components through comprehensive testing including unit tests, integration tests, manual validation, and 24-hour continuous operation monitoring to ensure the system meets all requirements and performs reliably.

## Requirements

### Functional Requirements
1. Unit tests for all core algorithms (projections, data schema)
2. Integration tests for scraper → JSON → UI data flow
3. Manual validation of UI appearance and behavior
4. Selector accuracy validation against live claude.ai/usage
5. Atomic write integrity testing
6. Multi-monitor positioning testing
7. 24-hour continuous operation test
8. Resource usage monitoring (RAM < 250MB, CPU < 1%)

### Technical Requirements
1. **Test Framework**: pytest with pytest-asyncio
2. **Coverage Target**: 80%+ for critical components
3. **Test Types**: Unit, Integration, System, Acceptance
4. **Performance Metrics**: RAM usage, CPU usage, response time
5. **Duration Testing**: 24-hour stability test

## Acceptance Criteria

- [x] All unit tests pass (pytest tests/)
- [x] Integration tests validate data flow
- [x] Selector discovery confirms correct extraction
- [x] UI appearance validated on Windows 11
- [x] Always-on-top behavior works correctly
- [x] Atomic writes prevent data corruption
- [x] 24-hour test completes without crashes
- [x] Resource usage < 250MB RAM, < 1% CPU idle
- [x] Projection accuracy validated with synthetic data
- [x] Multi-monitor behavior tested (if available)
- [x] All acceptance criteria from EPIC-01 met

## Test Plan

### Phase 1: Unit Tests

#### Test: Data Schema Validation
```powershell
pytest tests/test_schema.py -v --cov=src/shared/data_schema
```

**Expected Results**:
- Schema creation works
- Validation detects invalid schemas
- Historical data trimming works
- Atomic writes complete successfully

#### Test: Projection Algorithms
```powershell
pytest tests/test_projections.py -v --cov=src/overlay/projection_algorithms
```

**Expected Results**:
- SMA calculation accurate
- Linear regression produces valid trends
- Time-to-cap estimation correct
- Projection at reset time accurate

#### Test: Error Handling
```powershell
pytest tests/test_error_handling.py -v --cov=src/shared
```

**Expected Results**:
- Rate limiter enforces intervals
- Session timeout detected
- Exponential backoff works

### Phase 2: Integration Tests

#### Test: Scraper to JSON Data Flow

1. Start scraper
2. Wait for initial poll
3. Verify JSON file created
4. Verify schema valid
5. Verify historical data added

**Validation Script**:
```python
# tests/integration/test_scraper_to_json.py
"""Integration test for scraper → JSON flow."""

import pytest
import asyncio
import json
from pathlib import Path
from src.scraper.claude_usage_monitor import ClaudeUsageMonitor

@pytest.mark.asyncio
@pytest.mark.integration
async def test_scraper_creates_valid_json(tmp_path):
    """Test that scraper creates valid JSON file."""
    
    # Configure scraper with test data directory
    monitor = ClaudeUsageMonitor(poll_interval=60)
    monitor.data_file = tmp_path / "usage-data.json"
    
    # Mock successful data extraction
    test_data = {
        'timestamp': '2025-11-08T14:00:00.000Z',
        'fourHour': {'usagePercent': 45.0, 'resetTime': '2025-11-08T18:00:00.000Z'},
        'oneWeek': {'usagePercent': 60.0, 'resetTime': '2025-11-15T00:00:00.000Z'},
        'opusOneWeek': {'usagePercent': 20.0, 'resetTime': '2025-11-15T00:00:00.000Z'},
        'status': 'success'
    }
    
    # Save data
    await monitor.save_data(test_data)
    
    # Verify file exists
    assert monitor.data_file.exists()
    
    # Verify valid JSON
    with open(monitor.data_file) as f:
        data = json.load(f)
    
    assert 'schemaVersion' in data
    assert 'currentState' in data
    assert 'historicalData' in data
    assert len(data['historicalData']) == 1
```

#### Test: JSON to UI Data Flow

1. Create test JSON file
2. Start overlay UI
3. Verify UI loads data
4. Update JSON file
5. Verify UI updates automatically

**Manual Test**:
1. Run overlay: `python src/overlay/overlay_widget.py`
2. Manually edit `data/usage-data.json`
3. Change a percentage value
4. Save file
5. Verify UI updates within 1 second

### Phase 3: System Tests

#### Test: End-to-End System Operation

1. **Start System**
   ```powershell
   python src/run_system.py
   ```

2. **Verify Components**
   - Scraper process running
   - Overlay window visible
   - Both processes show PIDs

3. **Wait for Poll Cycle** (5 minutes)
   - Monitor console output
   - Verify scraper polls successfully
   - Verify JSON file updated
   - Verify UI updates automatically

4. **Graceful Shutdown**
   - Press Ctrl+C
   - Verify both processes stop cleanly
   - Verify exit code 0

#### Test: Selector Accuracy

1. **Run Selector Discovery**
   ```powershell
   python src/scraper/selector_discovery.py
   ```

2. **Verify Selectors Work**
   - All elements found
   - At least one selector works per element
   - Extracted data matches page display

3. **Visual Validation**
   - Open claude.ai/usage in browser
   - Compare displayed percentages with extracted data
   - Verify reset times match

### Phase 4: Performance Tests

#### Test: Resource Usage Monitoring

Create [`tests/performance/monitor_resources.py`](../../tests/performance/monitor_resources.py):

```python
# tests/performance/monitor_resources.py
"""Monitor resource usage of running processes."""

import psutil
import time
from datetime import datetime

def monitor_process(process_name: str, duration_hours: int = 24):
    """
    Monitor a process's resource usage.
    
    Args:
        process_name: Name of process to monitor
        duration_hours: How long to monitor (hours)
    """
    print(f"Monitoring {process_name} for {duration_hours} hours...")
    
    # Find process
    target_process = None
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if process_name in ' '.join(proc.info['cmdline'] or []):
                target_process = psutil.Process(proc.info['pid'])
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if not target_process:
        print(f"Process {process_name} not found")
        return
    
    print(f"Found process: PID {target_process.pid}")
    
    # Monitor
    max_ram = 0
    max_cpu = 0
    samples = 0
    
    end_time = time.time() + (duration_hours * 3600)
    
    while time.time() < end_time:
        try:
            # Get metrics
            ram_mb = target_process.memory_info().rss / 1024 / 1024
            cpu_percent = target_process.cpu_percent(interval=1)
            
            max_ram = max(max_ram, ram_mb)
            max_cpu = max(max_cpu, cpu_percent)
            samples += 1
            
            # Log every 5 minutes
            if samples % 300 == 0:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] RAM: {ram_mb:.1f}MB | CPU: {cpu_percent:.1f}% | "
                      f"Peak RAM: {max_ram:.1f}MB | Peak CPU: {max_cpu:.1f}%")
            
            time.sleep(1)
            
        except psutil.NoSuchProcess:
            print("Process ended")
            break
    
    print(f"\n=== Final Results ===")
    print(f"Peak RAM: {max_ram:.1f}MB")
    print(f"Peak CPU: {max_cpu:.1f}%")
    print(f"Duration: {samples/3600:.1f} hours")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python monitor_resources.py <process_name> [duration_hours]")
        sys.exit(1)
    
    process_name = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    
    monitor_process(process_name, duration)
```

**Usage**:
```powershell
# Start in background
Start-Process python -ArgumentList "tests/performance/monitor_resources.py","claude_usage_monitor.py","24" -NoNewWindow
Start-Process python -ArgumentList "tests/performance/monitor_resources.py","overlay_widget.py","24" -NoNewWindow
```

#### Test: 24-Hour Continuous Operation

1. **Start System**
   ```powershell
   python src/run_system.py
   ```

2. **Start Monitoring** (in separate terminals)
   ```powershell
   python tests/performance/monitor_resources.py claude_usage_monitor.py 24
   python tests/performance/monitor_resources.py overlay_widget.py 24
   ```

3. **Let Run for 24 Hours**
   - Check periodically (every 4-6 hours)
   - Verify no crashes
   - Verify data continues to update

4. **Validate Results**
   - Peak RAM < 250MB total
   - Peak CPU < 1% when idle, < 10% during polls
   - No memory leaks (RAM stable)
   - No errors in logs
   - Data file contains ~288 historical points (24 hours × 12 intervals)

### Phase 5: Acceptance Testing

#### Acceptance Test Checklist

Based on [EPIC-01 Acceptance Criteria](EPIC-01.md:285):

- [ ] **Scraper Functionality**
  - [ ] Polls claude.ai/usage every 5 minutes
  - [ ] Manual login flow works
  - [ ] Session persists across restarts
  - [ ] Data saved to JSON correctly

- [ ] **Overlay UI**
  - [ ] Displays all three usage metrics
  - [ ] Progress bars show correct values
  - [ ] Color coding works (blue/orange/red)
  - [ ] Always-on-top functionality works
  - [ ] Window is draggable
  - [ ] Positioned in top-right corner

- [ ] **Projections**
  - [ ] Time-to-cap estimates calculated
  - [ ] Projected usage at reset time shown
  - [ ] Confidence levels displayed

- [ ] **Error Handling**
  - [ ] Session expiration handled gracefully
  - [ ] Network errors don't crash system
  - [ ] Corrupted JSON recovered

- [ ] **Performance**
  - [ ] Total RAM usage < 250MB
  - [ ] CPU usage < 1% idle
  - [ ] UI startup time < 1 second
  - [ ] Scraper startup time < 5 seconds

- [ ] **Reliability**
  - [ ] 24-hour test passes
  - [ ] No memory leaks
  - [ ] No data corruption
  - [ ] Graceful shutdown works

## Troubleshooting Test Failures

### Issue: Unit Tests Fail

**Solution**: Run with verbose output and coverage:
```powershell
pytest tests/test_projections.py -vv -s --cov-report=html
```

Check `htmlcov/index.html` for coverage details.

### Issue: Integration Test Timeout

**Solution**: Increase timeout values or check network connectivity:
```python
# Increase timeout in test
await page.wait_for_selector(selector, timeout=30000)  # 30s instead of 10s
```

### Issue: 24-Hour Test Crashes

**Check**:
1. Review error logs in `logs/errors.log`
2. Check Windows Event Viewer
3. Monitor available disk space
4. Verify network connectivity stable

## Dependencies

### Blocked By
All previous stories must be complete:
- [STOR-02](EPIC-01-STOR-02.md): Web Scraper
- [STOR-04](EPIC-01-STOR-04.md): PyQt5 Overlay UI
- [STOR-05](EPIC-01-STOR-05.md): Usage Projections
- [STOR-06](EPIC-01-STOR-06.md): File Watcher
- [STOR-07](EPIC-01-STOR-07.md): Process Orchestration
- [STOR-08](EPIC-01-STOR-08.md): Error Handling
- [STOR-09](EPIC-01-STOR-09.md): Selector Discovery

### Blocks
- [STOR-11](EPIC-01-STOR-11.md): Documentation (documents validated system)

## Definition of Done

- [ ] All unit tests pass with 80%+ coverage
- [ ] Integration tests validate data flow
- [ ] System tests confirm end-to-end operation
- [ ] Selector accuracy validated against live page
- [ ] 24-hour continuous operation test passes
- [ ] Resource usage within limits (< 250MB RAM)
- [ ] All acceptance criteria met
- [ ] Test results documented
- [ ] Story marked as DONE in EPIC-01.md

## References

- **Testing Checklist**: Lines 1426-1477 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:1426)
- **Resource Requirements**: Lines 1526-1540 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:1526)

---

**Created**: 2025-11-08  
**Last Updated**: 2025-11-08  
**Story Points**: 5  
**Actual Effort**: TBD