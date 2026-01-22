"""
Health Monitor Module

Monitors health of all MCP servers and system components.
Provides health checks, status reporting, and alerting.

Gold Tier Requirement #8: Error Recovery & Graceful Degradation
"""

import subprocess
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status for a single component"""
    name: str
    status: HealthStatus
    last_check: str
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class HealthMonitor:
    """
    Monitor health of MCP servers and system components.

    Usage:
        monitor = HealthMonitor(vault_path="/Vault")
        health = monitor.check_all()
        if not health['overall_healthy']:
            monitor.alert_unhealthy_components()
    """

    def __init__(
        self,
        vault_path: str,
        check_interval: int = 60,
        timeout: int = 5
    ):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

        # MCP servers to monitor
        self.mcp_servers = [
            "email",      # Silver Tier
            "xero",       # Gold Tier (Phase 4)
            "social",     # Gold Tier (optional)
        ]

        # System components to monitor
        self.system_components = [
            "vault_access",
            "log_directory",
            "disk_space",
        ]

    def check_mcp_server(self, server_name: str) -> ComponentHealth:
        """
        Check health of a single MCP server.

        Args:
            server_name: Name of MCP server to check

        Returns:
            ComponentHealth object with status
        """
        start_time = time.time()

        try:
            # Try to call MCP server health check
            result = subprocess.run(
                ['claude', 'mcp', 'list'],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            response_time_ms = (time.time() - start_time) * 1000

            # Check if server is in the list
            if server_name in result.stdout:
                return ComponentHealth(
                    name=f"mcp_{server_name}",
                    status=HealthStatus.HEALTHY,
                    last_check=datetime.now().isoformat(),
                    response_time_ms=response_time_ms,
                    metadata={"server_name": server_name}
                )
            else:
                return ComponentHealth(
                    name=f"mcp_{server_name}",
                    status=HealthStatus.UNHEALTHY,
                    last_check=datetime.now().isoformat(),
                    response_time_ms=response_time_ms,
                    error_message=f"Server {server_name} not found in MCP list",
                    metadata={"server_name": server_name}
                )

        except subprocess.TimeoutExpired:
            return ComponentHealth(
                name=f"mcp_{server_name}",
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.now().isoformat(),
                error_message=f"Health check timeout after {self.timeout}s",
                metadata={"server_name": server_name}
            )

        except Exception as e:
            return ComponentHealth(
                name=f"mcp_{server_name}",
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.now().isoformat(),
                error_message=str(e),
                metadata={"server_name": server_name}
            )

    def check_vault_access(self) -> ComponentHealth:
        """Check if vault directory is accessible"""
        try:
            if not self.vault_path.exists():
                return ComponentHealth(
                    name="vault_access",
                    status=HealthStatus.UNHEALTHY,
                    last_check=datetime.now().isoformat(),
                    error_message=f"Vault path does not exist: {self.vault_path}"
                )

            # Try to read a file
            test_file = self.vault_path / "Dashboard.md"
            if test_file.exists():
                test_file.read_text()

            return ComponentHealth(
                name="vault_access",
                status=HealthStatus.HEALTHY,
                last_check=datetime.now().isoformat(),
                metadata={"vault_path": str(self.vault_path)}
            )

        except Exception as e:
            return ComponentHealth(
                name="vault_access",
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.now().isoformat(),
                error_message=str(e)
            )

    def check_log_directory(self) -> ComponentHealth:
        """Check if log directory is accessible and writable"""
        try:
            log_dir = self.vault_path / "Logs"

            if not log_dir.exists():
                log_dir.mkdir(parents=True, exist_ok=True)

            # Try to write a test file
            test_file = log_dir / ".health_check"
            test_file.write_text("health_check")
            test_file.unlink()

            return ComponentHealth(
                name="log_directory",
                status=HealthStatus.HEALTHY,
                last_check=datetime.now().isoformat(),
                metadata={"log_dir": str(log_dir)}
            )

        except Exception as e:
            return ComponentHealth(
                name="log_directory",
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.now().isoformat(),
                error_message=str(e)
            )

    def check_disk_space(self) -> ComponentHealth:
        """Check available disk space"""
        try:
            import shutil
            stat = shutil.disk_usage(self.vault_path)

            # Calculate percentages
            used_percent = (stat.used / stat.total) * 100
            free_gb = stat.free / (1024 ** 3)

            # Determine status based on free space
            if free_gb < 1:  # Less than 1GB free
                status = HealthStatus.UNHEALTHY
                error_message = f"Critical: Only {free_gb:.2f}GB free"
            elif free_gb < 5:  # Less than 5GB free
                status = HealthStatus.DEGRADED
                error_message = f"Warning: Only {free_gb:.2f}GB free"
            else:
                status = HealthStatus.HEALTHY
                error_message = None

            return ComponentHealth(
                name="disk_space",
                status=status,
                last_check=datetime.now().isoformat(),
                error_message=error_message,
                metadata={
                    "total_gb": round(stat.total / (1024 ** 3), 2),
                    "used_gb": round(stat.used / (1024 ** 3), 2),
                    "free_gb": round(free_gb, 2),
                    "used_percent": round(used_percent, 2)
                }
            )

        except Exception as e:
            return ComponentHealth(
                name="disk_space",
                status=HealthStatus.UNKNOWN,
                last_check=datetime.now().isoformat(),
                error_message=str(e)
            )

    def check_all(self) -> Dict[str, Any]:
        """
        Check health of all components.

        Returns:
            Dictionary with overall health status and component details
        """
        components = []

        # Check MCP servers
        for server in self.mcp_servers:
            health = self.check_mcp_server(server)
            components.append(health)

        # Check system components
        components.append(self.check_vault_access())
        components.append(self.check_log_directory())
        components.append(self.check_disk_space())

        # Calculate overall health
        unhealthy_count = sum(
            1 for c in components if c.status == HealthStatus.UNHEALTHY
        )
        degraded_count = sum(
            1 for c in components if c.status == HealthStatus.DEGRADED
        )

        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        return {
            "overall_status": overall_status.value,
            "overall_healthy": overall_status == HealthStatus.HEALTHY,
            "timestamp": datetime.now().isoformat(),
            "components": [asdict(c) for c in components],
            "summary": {
                "total": len(components),
                "healthy": sum(1 for c in components if c.status == HealthStatus.HEALTHY),
                "degraded": degraded_count,
                "unhealthy": unhealthy_count,
                "unknown": sum(1 for c in components if c.status == HealthStatus.UNKNOWN)
            }
        }

    def get_unhealthy_components(self) -> List[ComponentHealth]:
        """Get list of unhealthy components"""
        health = self.check_all()
        return [
            ComponentHealth(**c)
            for c in health['components']
            if c['status'] in [HealthStatus.UNHEALTHY.value, HealthStatus.DEGRADED.value]
        ]

    def alert_unhealthy_components(self) -> None:
        """Log alerts for unhealthy components"""
        unhealthy = self.get_unhealthy_components()

        if not unhealthy:
            return

        self.logger.warning(f"⚠️  {len(unhealthy)} unhealthy components detected:")

        for component in unhealthy:
            self.logger.warning(
                f"  - {component.name}: {component.status.value} - {component.error_message}"
            )

    def save_health_report(self) -> Path:
        """
        Save health report to file.

        Returns:
            Path to saved report
        """
        health = self.check_all()

        report_dir = self.vault_path / "Health_Reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = report_dir / f"health_report_{timestamp}.json"

        # Convert enum values to strings for JSON serialization
        def convert_enums(obj):
            if isinstance(obj, dict):
                return {k: convert_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enums(item) for item in obj]
            elif isinstance(obj, HealthStatus):
                return obj.value
            else:
                return obj

        health_serializable = convert_enums(health)

        import json
        with open(report_file, 'w') as f:
            json.dump(health_serializable, f, indent=2)

        self.logger.info(f"Health report saved: {report_file}")
        return report_file

    def run_continuous_monitoring(self) -> None:
        """
        Run continuous health monitoring loop.

        This should be run in a separate process/thread.
        """
        self.logger.info(
            f"Starting continuous health monitoring (interval: {self.check_interval}s)"
        )

        try:
            while True:
                health = self.check_all()

                if not health['overall_healthy']:
                    self.alert_unhealthy_components()

                    # Save report for unhealthy state
                    self.save_health_report()

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Health monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Health monitoring error: {e}")
            raise


def main():
    """Main entry point for health monitor"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Gold Tier Health Monitor")
    parser.add_argument(
        '--vault-path',
        default='/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault',
        help='Path to Obsidian vault'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuous monitoring'
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    monitor = HealthMonitor(
        vault_path=args.vault_path,
        check_interval=args.interval
    )

    if args.continuous:
        monitor.run_continuous_monitoring()
    else:
        # Single check
        health = monitor.check_all()

        print("\n" + "=" * 70)
        print("GOLD TIER HEALTH CHECK")
        print("=" * 70)
        print(f"\nOverall Status: {health['overall_status'].upper()}")
        print(f"Timestamp: {health['timestamp']}")
        print(f"\nSummary:")
        print(f"  Total Components: {health['summary']['total']}")
        print(f"  ✅ Healthy: {health['summary']['healthy']}")
        print(f"  ⚠️  Degraded: {health['summary']['degraded']}")
        print(f"  ❌ Unhealthy: {health['summary']['unhealthy']}")
        print(f"  ❓ Unknown: {health['summary']['unknown']}")

        print(f"\nComponent Details:")
        for component in health['components']:
            status_icon = {
                'healthy': '✅',
                'degraded': '⚠️',
                'unhealthy': '❌',
                'unknown': '❓'
            }.get(component['status'], '?')

            print(f"  {status_icon} {component['name']}: {component['status']}")
            if component.get('error_message'):
                print(f"     Error: {component['error_message']}")
            if component.get('response_time_ms'):
                print(f"     Response Time: {component['response_time_ms']:.2f}ms")

        print("\n" + "=" * 70)

        # Exit with error code if unhealthy
        if not health['overall_healthy']:
            sys.exit(1)


if __name__ == "__main__":
    main()
