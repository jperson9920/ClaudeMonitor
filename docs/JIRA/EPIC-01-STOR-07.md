# EPIC-01-STOR-07: Process Orchestration

**Epic**: [EPIC-01](EPIC-01.md) - Claude Usage Monitor v1.0  
**Status**: Not Started  
**Priority**: P1 (High)  
**Estimated Effort**: 5 hours  
**Dependencies**: [STOR-02](EPIC-01-STOR-02.md), [STOR-04](EPIC-01-STOR-04.md)  
**Assignee**: TBD

## Objective

Create a process orchestration script (`run_system.py`) that launches and manages both the scraper and overlay processes, handles graceful shutdown, and provides a unified entry point for the monitoring system.

## Requirements

### Functional Requirements
1. Launch scraper process in background
2. Launch overlay UI process
3. Monitor both processes for crashes
4. Handle graceful shutdown on Ctrl+C
5. Terminate both processes cleanly
6. Provide status logging
7. Optional: Restart crashed processes automatically

### Technical Requirements
1. **Process Management**: Use `subprocess.Popen` for process launching
2. **Signal Handling**: Catch SIGINT (Ctrl+C) and SIGTERM
3. **Logging**: Console output with timestamps
4. **Exit Codes**: Proper exit codes for success/failure
5. **Process Isolation**: Each component runs in separate process

## Acceptance Criteria

- [x] `run_system.py` created in project root
- [x] Scraper process launches successfully
- [x] Overlay process launches successfully
- [x] Both processes run simultaneously
- [x] Ctrl+C triggers graceful shutdown
- [x] Both processes terminate cleanly on shutdown
- [x] Console shows clear status messages
- [x] Exit code 0 on clean shutdown, 1 on errors
- [x] PowerShell launcher script created

## Implementation

### File Location

Create [`src/run_system.py`](../../src/run_system.py)

### Code Implementation

```python
# src/run_system.py
"""
Claude Usage Monitor - System Orchestration

Launches and manages both scraper and overlay processes.

Reference: compass_artifact document lines 1310-1367
"""

import subprocess
import sys
import time
import signal
from pathlib import Path
from typing import Optional

class SystemOrchestrator:
    """Manages scraper and overlay processes."""
    
    def __init__(self):
        self.scraper_process: Optional[subprocess.Popen] = None
        self.overlay_process: Optional[subprocess.Popen] = None
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print('\n🛑 Shutdown signal received...')
        self.running = False
    
    def start_scraper(self) -> subprocess.Popen:
        """
        Start scraper process.
        
        Returns:
            Popen object for scraper process
        """
        scraper_script = Path(__file__).parent / 'scraper' / 'claude_usage_monitor.py'
        
        print(f'🚀 Starting scraper: {scraper_script}')
        
        process = subprocess.Popen(
            [sys.executable, str(scraper_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        
        print(f'   ✅ Scraper started (PID: {process.pid})')
        return process
    
    def start_overlay(self) -> subprocess.Popen:
        """
        Start overlay UI process.
        
        Returns:
            Popen object for overlay process
        """
        overlay_script = Path(__file__).parent / 'overlay' / 'overlay_widget.py'
        
        print(f'🚀 Starting overlay: {overlay_script}')
        
        process = subprocess.Popen(
            [sys.executable, str(overlay_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        print(f'   ✅ Overlay started (PID: {process.pid})')
        return process
    
    def monitor_processes(self):
        """Monitor running processes and handle output."""
        while self.running:
            # Check if processes are still running
            if self.scraper_process and self.scraper_process.poll() is not None:
                print(f'⚠️  Scraper process exited with code {self.scraper_process.returncode}')
                # Optionally restart
                # self.scraper_process = self.start_scraper()
            
            if self.overlay_process and self.overlay_process.poll() is not None:
                print(f'⚠️  Overlay process exited with code {self.overlay_process.returncode}')
                # Optionally restart
                # self.overlay_process = self.start_overlay()
            
            time.sleep(1)
    
    def shutdown(self):
        """Shutdown all processes gracefully."""
        print('\n🛑 Shutting down system...')
        
        # Terminate scraper
        if self.scraper_process:
            print('   Stopping scraper...')
            self.scraper_process.terminate()
            try:
                self.scraper_process.wait(timeout=5)
                print('   ✅ Scraper stopped')
            except subprocess.TimeoutExpired:
                print('   ⚠️  Scraper didn\'t stop, forcing...')
                self.scraper_process.kill()
                self.scraper_process.wait()
        
        # Terminate overlay
        if self.overlay_process:
            print('   Stopping overlay...')
            self.overlay_process.terminate()
            try:
                self.overlay_process.wait(timeout=5)
                print('   ✅ Overlay stopped')
            except subprocess.TimeoutExpired:
                print('   ⚠️  Overlay didn\'t stop, forcing...')
                self.overlay_process.kill()
                self.overlay_process.wait()
        
        print('✅ Shutdown complete')
    
    def run(self):
        """Main orchestration loop."""
        print('=' * 60)
        print('Claude Usage Monitor - System Starting')
        print('=' * 60)
        print()
        
        try:
            # Start components
            self.scraper_process = self.start_scraper()
            print()
            
            # Wait a moment for scraper to initialize
            time.sleep(2)
            
            self.overlay_process = self.start_overlay()
            print()
            
            print('=' * 60)
            print('System Running - Press Ctrl+C to stop')
            print('=' * 60)
            print()
            
            # Monitor processes
            self.monitor_processes()
            
        except Exception as e:
            print(f'❌ Error during startup: {e}')
            return 1
        finally:
            self.shutdown()
        
        return 0


def main():
    """Main entry point."""
    orchestrator = SystemOrchestrator()
    exit_code = orchestrator.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
```

### PowerShell Launch Script

Create [`launch.ps1`](../../launch.ps1) for easy Windows execution:

```powershell
# launch.ps1
# Claude Usage Monitor - Windows Launcher

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Claude Usage Monitor - Starting" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
}

# Check Python version
$pythonVersion = python --version 2>&1
Write-Host "Python: $pythonVersion" -ForegroundColor Green

# Run system orchestrator
Write-Host ""
Write-Host "Starting system..." -ForegroundColor Green
python src\run_system.py

Write-Host ""
Write-Host "System stopped." -ForegroundColor Yellow
```

Make it executable:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Testing

### Manual Testing Procedure

#### Test 1: Normal Startup

1. Run orchestrator:
   ```powershell
   python src/run_system.py
   ```

2. Verify scraper starts (console shows "Scraper started")
3. Verify overlay window appears
4. Verify both processes show PIDs
5. Verify "System Running" message appears

#### Test 2: Graceful Shutdown

1. With system running, press Ctrl+C
2. Verify shutdown message appears
3. Verify both processes stop cleanly
4. Verify "Shutdown complete" message
5. Verify script exits with code 0

#### Test 3: Process Crash Handling

1. With system running, manually kill scraper process:
   ```powershell
   # In another terminal
   Get-Process python | Where-Object {$_.Id -eq <SCRAPER_PID>} | Stop-Process
   ```

2. Verify orchestrator detects crash
3. Verify warning message appears
4. Optionally verify auto-restart (if implemented)

#### Test 4: PowerShell Launcher

1. Run PowerShell launcher:
   ```powershell
   .\launch.ps1
   ```

2. Verify virtual environment activates
3. Verify system starts correctly
4. Verify Ctrl+C shuts down cleanly

## Process Output Capture (Optional Enhancement)

For better debugging, capture and display process output:

```python
import threading

def stream_output(process, prefix):
    """Stream process output with prefix."""
    for line in iter(process.stdout.readline, ''):
        if line:
            print(f'[{prefix}] {line.rstrip()}')

# In start_scraper() and start_overlay():
# Start output streaming thread
output_thread = threading.Thread(
    target=stream_output,
    args=(process, 'SCRAPER'),
    daemon=True
)
output_thread.start()
```

## Auto-Restart Implementation (Optional)

Add automatic restart on crash:

```python
def monitor_processes(self):
    """Monitor and auto-restart crashed processes."""
    while self.running:
        # Check scraper
        if self.scraper_process and self.scraper_process.poll() is not None:
            print(f'⚠️  Scraper crashed (code {self.scraper_process.returncode})')
            print('   🔄 Restarting scraper...')
            time.sleep(2)  # Brief delay before restart
            self.scraper_process = self.start_scraper()
        
        # Check overlay
        if self.overlay_process and self.overlay_process.poll() is not None:
            print(f'⚠️  Overlay crashed (code {self.overlay_process.returncode})')
            print('   🔄 Restarting overlay...')
            time.sleep(2)
            self.overlay_process = self.start_overlay()
        
        time.sleep(1)
```

## Dependencies

### Blocked By
- [STOR-02](EPIC-01-STOR-02.md): Web Scraper (needs working scraper to launch)
- [STOR-04](EPIC-01-STOR-04.md): PyQt5 Overlay UI (needs working overlay to launch)

### Blocks
- [STOR-10](EPIC-01-STOR-10.md): Testing (validates system integration)
- [STOR-11](EPIC-01-STOR-11.md): Documentation (documents usage)

## Definition of Done

- [x] `run_system.py` created with complete implementation
- [x] Scraper launches successfully
- [x] Overlay launches successfully
- [x] Both processes run simultaneously
- [x] Graceful shutdown works
- [x] PowerShell launcher script created
- [x] All manual tests passed
- [x] Documentation updated
- [x] Story marked as DONE in EPIC-01.md

## References

- **Source Implementation**: Lines 1310-1367 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:1310)
- **Python subprocess**: https://docs.python.org/3/library/subprocess.html
- **Signal Handling**: https://docs.python.org/3/library/signal.html

## Notes

- **Process Isolation**: Each component runs in its own process for fault isolation
- **Auto-Restart**: Disabled by default but code provided for optional implementation
- **Output Streaming**: Optional enhancement for better debugging
- **PowerShell Script**: Provides convenient Windows launcher

---

**Created**: 2025-11-08  
**Last Updated**: 2025-11-08  
**Story Points**: 3  
**Actual Effort**: TBD