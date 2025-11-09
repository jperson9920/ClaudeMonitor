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
