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
