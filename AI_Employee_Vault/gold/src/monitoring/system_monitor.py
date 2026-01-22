#!/usr/bin/env python3
"""
Gold Tier System Monitor

Automatically monitors system health and alerts on issues.
Runs every 15 minutes to check:
- PM2 process status
- Error logs
- Memory usage
- Output generation
- System stability
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class SystemMonitor:
    """Monitor Gold Tier system health and alert on issues."""

    def __init__(self, vault_path: str):
        """Initialize system monitor."""
        self.vault_path = Path(vault_path)
        self.monitoring_dir = self.vault_path / 'Monitoring'
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)

        self.alerts_file = self.monitoring_dir / 'alerts.log'
        self.status_file = self.monitoring_dir / 'system_status.json'
        self.history_file = self.monitoring_dir / 'monitoring_history.jsonl'

        # Expected processes
        self.expected_processes = [
            'gold-health-monitor',
            'gold-watchdog',
            'gold-facebook-watcher',
            'gold-instagram-watcher',
            'gold-twitter-watcher',
            'gold-ceo-briefing'
        ]

        # Thresholds
        self.max_memory_mb = 100  # Alert if process uses >100MB
        self.max_restarts = 10    # Alert if process restarts >10 times
        self.max_error_rate = 5   # Alert if >5 errors per hour

    def check_pm2_processes(self) -> Dict[str, Any]:
        """Check PM2 process status."""
        try:
            result = subprocess.run(
                ['pm2', 'jlist'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return {
                    'status': 'error',
                    'message': 'Failed to get PM2 process list',
                    'processes': []
                }

            processes = json.loads(result.stdout)
            gold_processes = [p for p in processes if p['name'].startswith('gold-')]

            issues = []
            process_status = {}

            for proc in gold_processes:
                name = proc['name']
                status = proc['pm2_env']['status']
                restarts = proc['pm2_env'].get('restart_time', 0)
                memory_mb = proc['monit']['memory'] / (1024 * 1024)

                process_status[name] = {
                    'status': status,
                    'restarts': restarts,
                    'memory_mb': round(memory_mb, 2),
                    'uptime': proc['pm2_env'].get('pm_uptime', 0)
                }

                # Check for issues
                if status != 'online':
                    issues.append(f"{name} is {status}")

                if restarts > self.max_restarts:
                    issues.append(f"{name} has restarted {restarts} times")

                if memory_mb > self.max_memory_mb:
                    issues.append(f"{name} using {memory_mb:.1f}MB memory")

            # Check for missing processes
            found_names = [p['name'] for p in gold_processes]
            for expected in self.expected_processes:
                if expected not in found_names:
                    issues.append(f"{expected} is not running")

            return {
                'status': 'ok' if not issues else 'warning',
                'message': 'All processes healthy' if not issues else f"{len(issues)} issues found",
                'processes': process_status,
                'issues': issues
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error checking PM2: {e}",
                'processes': {}
            }

    def check_error_logs(self) -> Dict[str, Any]:
        """Check for recent errors in logs."""
        try:
            log_dir = self.vault_path / 'Logs' / 'pm2'

            if not log_dir.exists():
                return {
                    'status': 'warning',
                    'message': 'Log directory not found',
                    'errors': []
                }

            # Check error logs from last hour
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_errors = []

            for error_log in log_dir.glob('*-error-*.log'):
                if error_log.stat().st_mtime < one_hour_ago.timestamp():
                    continue

                try:
                    with open(error_log, 'r') as f:
                        lines = f.readlines()

                    # Count error lines (skip KeyboardInterrupt)
                    errors = [
                        line for line in lines[-50:]  # Last 50 lines
                        if 'Error' in line or 'Exception' in line
                        and 'KeyboardInterrupt' not in line
                    ]

                    if errors:
                        recent_errors.append({
                            'file': error_log.name,
                            'count': len(errors),
                            'sample': errors[-1].strip()[:200]
                        })

                except Exception as e:
                    pass

            total_errors = sum(e['count'] for e in recent_errors)

            return {
                'status': 'ok' if total_errors < self.max_error_rate else 'warning',
                'message': f"{total_errors} errors in last hour",
                'errors': recent_errors
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error checking logs: {e}",
                'errors': []
            }

    def check_output_generation(self) -> Dict[str, Any]:
        """Check if system is generating expected outputs."""
        try:
            checks = {}

            # Check health reports (should be generated every 60 seconds)
            health_dir = self.vault_path / 'Health_Reports'
            if health_dir.exists():
                recent_reports = [
                    f for f in health_dir.glob('*.json')
                    if f.stat().st_mtime > (datetime.now() - timedelta(minutes=5)).timestamp()
                ]
                checks['health_reports'] = {
                    'status': 'ok' if len(recent_reports) >= 3 else 'warning',
                    'count': len(recent_reports),
                    'expected': '3-5 in last 5 minutes'
                }
            else:
                checks['health_reports'] = {
                    'status': 'error',
                    'count': 0,
                    'expected': 'Directory not found'
                }

            # Check social media action items (should be generated periodically)
            needs_action = self.vault_path / 'Needs_Action'
            if needs_action.exists():
                recent_items = [
                    f for f in needs_action.glob('fb_*')
                    if f.stat().st_mtime > (datetime.now() - timedelta(hours=24)).timestamp()
                ]
                checks['social_action_items'] = {
                    'status': 'ok',
                    'count': len(recent_items),
                    'expected': 'Variable (depends on engagement)'
                }

            # Check CEO briefings
            briefing_dir = self.vault_path / 'Reports' / 'CEO_Briefings'
            if briefing_dir.exists():
                briefings = list(briefing_dir.glob('*.md'))
                checks['ceo_briefings'] = {
                    'status': 'ok',
                    'count': len(briefings),
                    'expected': 'Weekly (Sunday 7 AM)'
                }

            issues = [
                f"{k}: {v['status']}" for k, v in checks.items()
                if v['status'] != 'ok'
            ]

            return {
                'status': 'ok' if not issues else 'warning',
                'message': 'All outputs generating' if not issues else f"{len(issues)} issues",
                'checks': checks,
                'issues': issues
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error checking outputs: {e}",
                'checks': {}
            }

    def generate_alert(self, severity: str, message: str):
        """Generate an alert and log it."""
        timestamp = datetime.now().isoformat()
        alert = f"[{timestamp}] {severity.upper()}: {message}\n"

        # Append to alerts file
        with open(self.alerts_file, 'a') as f:
            f.write(alert)

        # Print to console
        icon = "🚨" if severity == "critical" else "⚠️" if severity == "warning" else "ℹ️"
        print(f"{icon} {alert.strip()}")

    def run_check(self) -> Dict[str, Any]:
        """Run complete system check."""
        timestamp = datetime.now()

        print("=" * 70)
        print(f"GOLD TIER SYSTEM MONITOR - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()

        # Run all checks
        pm2_check = self.check_pm2_processes()
        log_check = self.check_error_logs()
        output_check = self.check_output_generation()

        # Determine overall status
        statuses = [pm2_check['status'], log_check['status'], output_check['status']]
        if 'error' in statuses:
            overall_status = 'error'
        elif 'warning' in statuses:
            overall_status = 'warning'
        else:
            overall_status = 'ok'

        # Generate alerts for issues
        if pm2_check['status'] != 'ok':
            for issue in pm2_check.get('issues', []):
                self.generate_alert('warning', f"PM2: {issue}")

        if log_check['status'] != 'ok':
            for error in log_check.get('errors', []):
                self.generate_alert('warning', f"Errors in {error['file']}: {error['count']}")

        if output_check['status'] != 'ok':
            for issue in output_check.get('issues', []):
                self.generate_alert('info', f"Output: {issue}")

        # Print summary
        print("📊 PM2 PROCESSES")
        print("-" * 70)
        print(f"Status: {pm2_check['status'].upper()}")
        print(f"Message: {pm2_check['message']}")
        if pm2_check.get('processes'):
            for name, info in pm2_check['processes'].items():
                status_icon = "✅" if info['status'] == 'online' else "❌"
                print(f"{status_icon} {name}: {info['status']} (restarts: {info['restarts']}, mem: {info['memory_mb']}MB)")
        print()

        print("📝 ERROR LOGS")
        print("-" * 70)
        print(f"Status: {log_check['status'].upper()}")
        print(f"Message: {log_check['message']}")
        if log_check.get('errors'):
            for error in log_check['errors']:
                print(f"  - {error['file']}: {error['count']} errors")
        print()

        print("📁 OUTPUT GENERATION")
        print("-" * 70)
        print(f"Status: {output_check['status'].upper()}")
        print(f"Message: {output_check['message']}")
        if output_check.get('checks'):
            for name, info in output_check['checks'].items():
                status_icon = "✅" if info['status'] == 'ok' else "⚠️"
                print(f"{status_icon} {name}: {info['count']} ({info['expected']})")
        print()

        print("=" * 70)
        status_icon = "✅" if overall_status == 'ok' else "⚠️" if overall_status == 'warning' else "❌"
        print(f"{status_icon} OVERALL STATUS: {overall_status.upper()}")
        print("=" * 70)
        print()

        # Save status to file
        status_data = {
            'timestamp': timestamp.isoformat(),
            'overall_status': overall_status,
            'pm2': pm2_check,
            'logs': log_check,
            'outputs': output_check
        }

        with open(self.status_file, 'w') as f:
            json.dump(status_data, f, indent=2)

        # Append to history
        with open(self.history_file, 'a') as f:
            f.write(json.dumps(status_data) + '\n')

        return status_data

    def run_continuous(self, interval_minutes: int = 15):
        """Run monitoring continuously."""
        import time

        print(f"🔍 Starting continuous monitoring (interval: {interval_minutes} minutes)")
        print(f"📁 Monitoring directory: {self.monitoring_dir}")
        print(f"📊 Status file: {self.status_file}")
        print(f"🚨 Alerts file: {self.alerts_file}")
        print()

        while True:
            try:
                self.run_check()
                print(f"⏰ Next check in {interval_minutes} minutes...")
                print()
                time.sleep(interval_minutes * 60)
            except KeyboardInterrupt:
                print("\n⏹️  Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Gold Tier System Monitor")
    parser.add_argument(
        '--vault-path',
        default=os.getenv('VAULT_PATH', '/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault'),
        help='Path to Obsidian vault'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuously'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=15,
        help='Check interval in minutes (default: 15)'
    )

    args = parser.parse_args()

    monitor = SystemMonitor(args.vault_path)

    if args.continuous:
        monitor.run_continuous(args.interval)
    else:
        monitor.run_check()


if __name__ == '__main__':
    main()
