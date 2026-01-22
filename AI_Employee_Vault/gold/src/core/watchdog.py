"""
Watchdog Process Module

Monitors and restarts critical processes automatically.
Ensures always-on operation for Gold Tier autonomous employee.

Gold Tier Requirement #8: Error Recovery & Graceful Degradation
"""

import subprocess
import time
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProcessConfig:
    """Configuration for a monitored process"""
    name: str
    command: str
    args: List[str]
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    restart_on_failure: bool = True
    max_restarts: int = 5
    restart_window_seconds: int = 300  # 5 minutes


class Watchdog:
    """
    Monitor and restart critical processes.

    Usage:
        watchdog = Watchdog(vault_path="/Vault")
        watchdog.add_process(
            name="gmail_watcher",
            command="python3",
            args=["silver/src/watchers/gmail_watcher.py"]
        )
        watchdog.run()
    """

    def __init__(self, vault_path: str, check_interval: int = 30):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.logger = logging.getLogger(__name__)

        # Process tracking
        self.processes: Dict[str, ProcessConfig] = {}
        self.running_processes: Dict[str, subprocess.Popen] = {}
        self.restart_counts: Dict[str, List[datetime]] = {}

        # PID file directory
        self.pid_dir = self.vault_path / ".pids"
        self.pid_dir.mkdir(parents=True, exist_ok=True)

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop_all()
        sys.exit(0)

    def add_process(
        self,
        name: str,
        command: str,
        args: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        restart_on_failure: bool = True,
        max_restarts: int = 5
    ) -> None:
        """
        Add a process to monitor.

        Args:
            name: Unique name for the process
            command: Command to execute
            args: Command arguments
            cwd: Working directory
            env: Environment variables
            restart_on_failure: Whether to restart on failure
            max_restarts: Maximum restarts within restart window
        """
        config = ProcessConfig(
            name=name,
            command=command,
            args=args,
            cwd=cwd,
            env=env,
            restart_on_failure=restart_on_failure,
            max_restarts=max_restarts
        )

        self.processes[name] = config
        self.restart_counts[name] = []

        self.logger.info(f"Added process to watchdog: {name}")

    def _get_pid_file(self, name: str) -> Path:
        """Get PID file path for a process"""
        return self.pid_dir / f"{name}.pid"

    def _write_pid_file(self, name: str, pid: int) -> None:
        """Write PID to file"""
        pid_file = self._get_pid_file(name)
        pid_file.write_text(str(pid))

    def _read_pid_file(self, name: str) -> Optional[int]:
        """Read PID from file"""
        pid_file = self._get_pid_file(name)
        if pid_file.exists():
            try:
                return int(pid_file.read_text().strip())
            except Exception:
                return None
        return None

    def _delete_pid_file(self, name: str) -> None:
        """Delete PID file"""
        pid_file = self._get_pid_file(name)
        if pid_file.exists():
            pid_file.unlink()

    def is_process_running(self, name: str) -> bool:
        """
        Check if a process is running.

        Args:
            name: Process name

        Returns:
            True if running, False otherwise
        """
        # Check if we have a running process object
        if name in self.running_processes:
            proc = self.running_processes[name]
            if proc.poll() is None:  # Still running
                return True
            else:
                # Process died, clean up
                del self.running_processes[name]
                self._delete_pid_file(name)
                return False

        # Check PID file
        pid = self._read_pid_file(name)
        if pid:
            try:
                # Check if process exists
                import psutil
                if psutil.pid_exists(pid):
                    return True
            except ImportError:
                # psutil not available, use kill signal 0
                try:
                    import os
                    os.kill(pid, 0)
                    return True
                except OSError:
                    pass

        return False

    def can_restart(self, name: str) -> bool:
        """
        Check if process can be restarted based on restart limits.

        Args:
            name: Process name

        Returns:
            True if can restart, False if max restarts exceeded
        """
        config = self.processes[name]
        restart_times = self.restart_counts[name]

        # Clean up old restart times outside the window
        cutoff_time = datetime.now().timestamp() - config.restart_window_seconds
        restart_times[:] = [
            t for t in restart_times
            if t.timestamp() > cutoff_time
        ]

        # Check if under limit
        return len(restart_times) < config.max_restarts

    def start_process(self, name: str) -> bool:
        """
        Start a process.

        Args:
            name: Process name

        Returns:
            True if started successfully, False otherwise
        """
        if name not in self.processes:
            self.logger.error(f"Process not found: {name}")
            return False

        config = self.processes[name]

        try:
            # Build command
            cmd = [config.command] + config.args

            # Start process
            proc = subprocess.Popen(
                cmd,
                cwd=config.cwd,
                env=config.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Track process
            self.running_processes[name] = proc
            self._write_pid_file(name, proc.pid)

            self.logger.info(f"✅ Started process: {name} (PID: {proc.pid})")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to start process {name}: {e}")
            return False

    def stop_process(self, name: str, timeout: int = 10) -> bool:
        """
        Stop a process gracefully.

        Args:
            name: Process name
            timeout: Timeout in seconds

        Returns:
            True if stopped successfully, False otherwise
        """
        if name not in self.running_processes:
            self.logger.warning(f"Process not running: {name}")
            return True

        proc = self.running_processes[name]

        try:
            # Try graceful shutdown first
            proc.terminate()

            # Wait for process to exit
            try:
                proc.wait(timeout=timeout)
                self.logger.info(f"✅ Stopped process: {name}")
            except subprocess.TimeoutExpired:
                # Force kill if timeout
                self.logger.warning(f"Process {name} did not stop gracefully, forcing...")
                proc.kill()
                proc.wait()
                self.logger.info(f"✅ Killed process: {name}")

            # Clean up
            del self.running_processes[name]
            self._delete_pid_file(name)

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to stop process {name}: {e}")
            return False

    def restart_process(self, name: str) -> bool:
        """
        Restart a process.

        Args:
            name: Process name

        Returns:
            True if restarted successfully, False otherwise
        """
        # Check restart limits
        if not self.can_restart(name):
            self.logger.error(
                f"❌ Cannot restart {name}: max restarts exceeded in time window"
            )
            return False

        # Record restart
        self.restart_counts[name].append(datetime.now())

        # Stop if running
        if self.is_process_running(name):
            self.stop_process(name)

        # Wait a bit before restart
        time.sleep(2)

        # Start
        return self.start_process(name)

    def check_and_restart(self) -> None:
        """Check all processes and restart if needed"""
        for name, config in self.processes.items():
            if not self.is_process_running(name):
                if config.restart_on_failure:
                    self.logger.warning(f"⚠️  Process {name} not running, restarting...")
                    self.restart_process(name)
                else:
                    self.logger.warning(f"⚠️  Process {name} not running (auto-restart disabled)")

    def start_all(self) -> None:
        """Start all monitored processes"""
        self.logger.info("Starting all processes...")
        for name in self.processes:
            if not self.is_process_running(name):
                self.start_process(name)

    def stop_all(self) -> None:
        """Stop all monitored processes"""
        self.logger.info("Stopping all processes...")
        for name in list(self.running_processes.keys()):
            self.stop_process(name)

    def run(self) -> None:
        """
        Run watchdog monitoring loop.

        This runs indefinitely, checking and restarting processes.
        """
        self.logger.info(
            f"Starting watchdog (check interval: {self.check_interval}s)"
        )

        # Start all processes
        self.start_all()

        try:
            while True:
                self.check_and_restart()
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Watchdog stopped by user")
            self.stop_all()
        except Exception as e:
            self.logger.error(f"Watchdog error: {e}")
            self.stop_all()
            raise


def main():
    """Main entry point for watchdog"""
    import argparse

    parser = argparse.ArgumentParser(description="Gold Tier Watchdog")
    parser.add_argument(
        '--vault-path',
        default='/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault',
        help='Path to Obsidian vault'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Check interval in seconds'
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    watchdog = Watchdog(
        vault_path=args.vault_path,
        check_interval=args.interval
    )

    # Add processes to monitor (example configuration)
    # These will be configured properly in PM2

    print("\n" + "=" * 70)
    print("GOLD TIER WATCHDOG")
    print("=" * 70)
    print(f"\nVault Path: {args.vault_path}")
    print(f"Check Interval: {args.interval}s")
    print(f"\nMonitored Processes: {len(watchdog.processes)}")
    print("\nStarting watchdog...")
    print("=" * 70 + "\n")

    watchdog.run()


if __name__ == "__main__":
    main()
