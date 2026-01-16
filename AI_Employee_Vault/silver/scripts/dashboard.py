#!/usr/bin/env python3
"""
Silver Tier Monitoring Dashboard

Real-time monitoring dashboard for Silver tier AI assistant:
- Service status and health
- Activity metrics
- Error rates
- Recent logs
- System resources
"""

import os
import sys
from pathlib import Path
import time
from datetime import datetime, timedelta
from collections import defaultdict
import subprocess

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: 'rich' library not installed. Install with: pip install rich")
    print("Falling back to basic display mode.\n")


class DashboardMonitor:
    """Monitor for Silver tier system."""

    def __init__(self, vault_path: Path):
        """
        Initialize dashboard monitor.

        Args:
            vault_path: Path to vault directory
        """
        self.vault_path = vault_path
        self.silver_path = vault_path / "silver"
        self.pid_path = self.silver_path / ".pids"
        self.logs_path = vault_path / "Logs"

        if RICH_AVAILABLE:
            self.console = Console()

    def check_service_status(self, service_name: str) -> dict:
        """
        Check if a service is running.

        Args:
            service_name: Service name

        Returns:
            Dictionary with status information
        """
        pid_file = self.pid_path / f"{service_name}.pid"

        if not pid_file.exists():
            return {"running": False, "pid": None, "uptime": None}

        try:
            pid = int(pid_file.read_text().strip())
            # Check if process exists
            os.kill(pid, 0)

            # Get process start time for uptime
            try:
                result = subprocess.run(
                    ["ps", "-p", str(pid), "-o", "etime="],
                    capture_output=True,
                    text=True
                )
                uptime = result.stdout.strip() if result.returncode == 0 else "unknown"
            except Exception:
                uptime = "unknown"

            return {"running": True, "pid": pid, "uptime": uptime}
        except (OSError, ValueError):
            return {"running": False, "pid": None, "uptime": None}

    def get_activity_metrics(self, hours: int = 24) -> dict:
        """
        Get activity metrics from vault folders.

        Args:
            hours: Number of hours to look back

        Returns:
            Dictionary with activity counts
        """
        metrics = {
            "Needs_Action": 0,
            "Pending_Approval": 0,
            "Approved": 0,
            "Rejected": 0,
            "Done": 0,
            "Failed": 0
        }

        cutoff_time = time.time() - (hours * 3600)

        for folder in metrics.keys():
            folder_path = self.vault_path / folder
            if not folder_path.exists():
                continue

            for file in folder_path.glob("*.md"):
                if file.stat().st_mtime > cutoff_time:
                    metrics[folder] += 1

        return metrics

    def get_log_errors(self, service_name: str, minutes: int = 60) -> dict:
        """
        Get error count from log file.

        Args:
            service_name: Service name
            minutes: Minutes to look back

        Returns:
            Dictionary with error information
        """
        log_file = self.logs_path / f"{service_name}.log"

        if not log_file.exists():
            return {"errors": 0, "warnings": 0, "recent": []}

        errors = []
        warnings = []

        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                # Get last 100 lines for performance
                for line in lines[-100:]:
                    if 'ERROR' in line or 'CRITICAL' in line:
                        errors.append(line.strip())
                    elif 'WARNING' in line:
                        warnings.append(line.strip())

            return {
                "errors": len(errors),
                "warnings": len(warnings),
                "recent": errors[-3:] if errors else []
            }
        except Exception:
            return {"errors": 0, "warnings": 0, "recent": []}

    def get_system_stats(self) -> dict:
        """
        Get system resource statistics.

        Returns:
            Dictionary with system stats
        """
        stats = {
            "cpu_percent": "N/A",
            "memory_mb": "N/A",
            "disk_usage": "N/A"
        }

        try:
            # Get CPU usage for Silver tier processes
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )

            cpu_total = 0.0
            mem_total = 0.0

            for line in result.stdout.split('\n'):
                if any(s in line for s in ['gmail_watcher', 'whatsapp_watcher', 'approval_checker', 'scheduler']):
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            cpu_total += float(parts[2])
                            mem_total += float(parts[3])
                        except ValueError:
                            pass

            stats["cpu_percent"] = f"{cpu_total:.1f}%"
            stats["memory_mb"] = f"{mem_total:.1f}%"

            # Get disk usage for vault
            result = subprocess.run(
                ["du", "-sh", str(self.vault_path)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                stats["disk_usage"] = result.stdout.split()[0]

        except Exception:
            pass

        return stats

    def render_rich_dashboard(self) -> Layout:
        """
        Render dashboard using rich library.

        Returns:
            Rich Layout object
        """
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )

        # Header
        header_text = Text("Silver Tier Monitoring Dashboard", style="bold cyan")
        header_text.append(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
        layout["header"].update(Panel(header_text, border_style="cyan"))

        # Body - split into sections
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )

        layout["left"].split_column(
            Layout(name="services"),
            Layout(name="activity")
        )

        layout["right"].split_column(
            Layout(name="errors"),
            Layout(name="system")
        )

        # Services table
        services_table = Table(title="Service Status", show_header=True)
        services_table.add_column("Service", style="cyan")
        services_table.add_column("Status", style="green")
        services_table.add_column("PID", style="yellow")
        services_table.add_column("Uptime", style="blue")

        services = {
            "gmail_watcher": "Gmail Watcher",
            "whatsapp_watcher": "WhatsApp Watcher",
            "approval_checker": "Approval Checker",
            "scheduler": "Scheduler"
        }

        for service_id, service_name in services.items():
            status = self.check_service_status(service_id)
            status_text = "🟢 Running" if status["running"] else "🔴 Stopped"
            pid_text = str(status["pid"]) if status["pid"] else "-"
            uptime_text = status["uptime"] if status["uptime"] else "-"
            services_table.add_row(service_name, status_text, pid_text, uptime_text)

        layout["services"].update(Panel(services_table, border_style="green"))

        # Activity metrics
        activity_table = Table(title="Activity (Last 24h)", show_header=True)
        activity_table.add_column("Folder", style="cyan")
        activity_table.add_column("Count", style="yellow", justify="right")

        metrics = self.get_activity_metrics(hours=24)
        for folder, count in metrics.items():
            activity_table.add_row(folder, str(count))

        layout["activity"].update(Panel(activity_table, border_style="blue"))

        # Error summary
        error_table = Table(title="Error Summary (Last Hour)", show_header=True)
        error_table.add_column("Service", style="cyan")
        error_table.add_column("Errors", style="red", justify="right")
        error_table.add_column("Warnings", style="yellow", justify="right")

        for service_id, service_name in services.items():
            log_info = self.get_log_errors(service_id, minutes=60)
            error_table.add_row(
                service_name,
                str(log_info["errors"]),
                str(log_info["warnings"])
            )

        layout["errors"].update(Panel(error_table, border_style="red"))

        # System stats
        stats = self.get_system_stats()
        system_text = Text()
        system_text.append("CPU Usage: ", style="bold")
        system_text.append(f"{stats['cpu_percent']}\n")
        system_text.append("Memory: ", style="bold")
        system_text.append(f"{stats['memory_mb']}\n")
        system_text.append("Disk Usage: ", style="bold")
        system_text.append(f"{stats['disk_usage']}")

        layout["system"].update(Panel(system_text, title="System Resources", border_style="magenta"))

        # Footer
        footer_text = Text("Press Ctrl+C to exit | Refreshes every 5 seconds", style="dim")
        layout["footer"].update(Panel(footer_text, border_style="dim"))

        return layout

    def render_basic_dashboard(self):
        """Render dashboard in basic text mode (no rich library)."""
        os.system('clear' if os.name == 'posix' else 'cls')

        print("=" * 80)
        print("Silver Tier Monitoring Dashboard".center(80))
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S').center(80))
        print("=" * 80)
        print()

        # Services
        print("SERVICE STATUS:")
        print("-" * 80)
        services = {
            "gmail_watcher": "Gmail Watcher",
            "whatsapp_watcher": "WhatsApp Watcher",
            "approval_checker": "Approval Checker",
            "scheduler": "Scheduler"
        }

        for service_id, service_name in services.items():
            status = self.check_service_status(service_id)
            status_text = "RUNNING" if status["running"] else "STOPPED"
            pid_text = f"PID: {status['pid']}" if status["pid"] else "PID: -"
            uptime_text = f"Uptime: {status['uptime']}" if status["uptime"] else "Uptime: -"
            print(f"  {service_name:20} [{status_text:8}] {pid_text:12} {uptime_text}")
        print()

        # Activity
        print("ACTIVITY (LAST 24 HOURS):")
        print("-" * 80)
        metrics = self.get_activity_metrics(hours=24)
        for folder, count in metrics.items():
            print(f"  {folder:20} {count:5} files")
        print()

        # Errors
        print("ERROR SUMMARY (LAST HOUR):")
        print("-" * 80)
        for service_id, service_name in services.items():
            log_info = self.get_log_errors(service_id, minutes=60)
            print(f"  {service_name:20} Errors: {log_info['errors']:3}  Warnings: {log_info['warnings']:3}")
        print()

        # System
        print("SYSTEM RESOURCES:")
        print("-" * 80)
        stats = self.get_system_stats()
        print(f"  CPU Usage:  {stats['cpu_percent']}")
        print(f"  Memory:     {stats['memory_mb']}")
        print(f"  Disk Usage: {stats['disk_usage']}")
        print()

        print("=" * 80)
        print("Press Ctrl+C to exit | Refreshes every 5 seconds".center(80))
        print("=" * 80)

    def run(self, refresh_interval: int = 5):
        """
        Run dashboard with auto-refresh.

        Args:
            refresh_interval: Seconds between refreshes
        """
        if RICH_AVAILABLE:
            try:
                with Live(self.render_rich_dashboard(), refresh_per_second=1/refresh_interval, screen=True) as live:
                    while True:
                        time.sleep(refresh_interval)
                        live.update(self.render_rich_dashboard())
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Dashboard stopped by user[/yellow]")
        else:
            try:
                while True:
                    self.render_basic_dashboard()
                    time.sleep(refresh_interval)
            except KeyboardInterrupt:
                print("\nDashboard stopped by user")


def main():
    """Main entry point."""
    vault_path = Path(os.getenv(
        "VAULT_PATH",
        "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    ))

    dashboard = DashboardMonitor(vault_path)

    if RICH_AVAILABLE:
        print("Starting dashboard with rich UI...")
    else:
        print("Starting dashboard in basic mode...")
        print("For better UI, install: pip install rich\n")

    time.sleep(1)
    dashboard.run(refresh_interval=5)


if __name__ == "__main__":
    main()
