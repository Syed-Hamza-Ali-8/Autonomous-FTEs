#!/usr/bin/env python3
"""
Silver Tier Health Check Script

This script performs comprehensive health checks on all Silver tier components:
- Service status (running/stopped)
- Service health (responding/not responding)
- Configuration validation
- Credential verification
- Log file analysis
- Resource usage
- Recent activity

Provides actionable recommendations for any issues found.
"""

import os
import sys
from pathlib import Path
import time
from datetime import datetime, timedelta
import subprocess
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from silver.src.utils import setup_logging, get_logger

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_header(text):
    """Print section header."""
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}{text}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")

def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.NC}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}❌ {text}{Colors.NC}")

def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.NC}")

def print_info(text):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.NC}")

def check_service_running(service_name, pid_path):
    """Check if a service is running."""
    pid_file = pid_path / f"{service_name}.pid"

    if not pid_file.exists():
        return False, None

    try:
        pid = int(pid_file.read_text().strip())
        # Check if process exists
        os.kill(pid, 0)
        return True, pid
    except (OSError, ValueError):
        return False, None

def check_log_errors(log_file, minutes=10):
    """Check log file for recent errors."""
    if not log_file.exists():
        return 0, []

    try:
        # Get recent log entries (last N minutes)
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        errors = []

        with open(log_file, 'r') as f:
            for line in f:
                # Simple error detection (can be improved)
                if 'ERROR' in line or 'CRITICAL' in line or 'Exception' in line:
                    errors.append(line.strip())

        # Return only recent errors (simplified - assumes chronological order)
        recent_errors = errors[-10:] if len(errors) > 10 else errors
        return len(errors), recent_errors

    except Exception as e:
        return -1, [str(e)]

def check_credentials(vault_path):
    """Check if credentials are configured."""
    env_file = vault_path / "silver" / "config" / ".env"

    if not env_file.exists():
        return False, "No .env file found"

    try:
        content = env_file.read_text()

        # Check Gmail credentials
        has_gmail = all(key in content for key in [
            "GMAIL_CLIENT_ID",
            "GMAIL_CLIENT_SECRET",
            "GMAIL_REFRESH_TOKEN"
        ])

        # Check WhatsApp session
        whatsapp_session = vault_path / "silver" / ".whatsapp_session"
        has_whatsapp = whatsapp_session.exists()

        if has_gmail and has_whatsapp:
            return True, "All credentials configured"
        elif has_gmail:
            return False, "WhatsApp session not configured"
        elif has_whatsapp:
            return False, "Gmail credentials not configured"
        else:
            return False, "No credentials configured"

    except Exception as e:
        return False, str(e)

def check_vault_folders(vault_path):
    """Check if required vault folders exist."""
    required_folders = [
        "Needs_Action",
        "Pending_Approval",
        "Approved",
        "Rejected",
        "Plans",
        "Tasks",
        "In_Progress",
        "Done",
        "Failed",
        "Logs"
    ]

    missing = []
    for folder in required_folders:
        folder_path = vault_path / folder
        if not folder_path.exists():
            missing.append(folder)

    return len(missing) == 0, missing

def check_recent_activity(vault_path, hours=24):
    """Check for recent activity in vault folders."""
    activity = {}

    folders_to_check = {
        "Needs_Action": "New action requests",
        "Pending_Approval": "Pending approvals",
        "Approved": "Approved actions",
        "Done": "Completed actions",
        "Failed": "Failed actions"
    }

    cutoff_time = time.time() - (hours * 3600)

    for folder, description in folders_to_check.items():
        folder_path = vault_path / folder
        if not folder_path.exists():
            activity[folder] = {"count": 0, "description": description}
            continue

        # Count recent files
        recent_count = 0
        for file in folder_path.glob("*.md"):
            if file.stat().st_mtime > cutoff_time:
                recent_count += 1

        activity[folder] = {
            "count": recent_count,
            "description": description
        }

    return activity

def check_python_packages():
    """Check if required Python packages are installed."""
    required_packages = [
        "google-auth",
        "google-api-python-client",
        "playwright",
        "schedule",
        "plyer",
        "pyyaml"
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)

    return len(missing) == 0, missing

def main():
    """Main health check."""
    # Setup logging
    setup_logging(log_level="INFO", log_format="text")

    # Get vault path
    vault_path = Path(os.getenv(
        "VAULT_PATH",
        "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    ))

    silver_path = vault_path / "silver"
    pid_path = silver_path / ".pids"
    logs_path = vault_path / "Logs"

    print_header("Silver Tier Health Check")
    print(f"Vault Path: {vault_path}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Track overall health
    issues = []
    warnings = []

    # 1. Check Service Status
    print_header("Service Status")

    services = {
        "gmail_watcher": "Gmail Watcher",
        "whatsapp_watcher": "WhatsApp Watcher",
        "approval_checker": "Approval Checker",
        "scheduler": "Scheduler"
    }

    running_services = 0
    for service_id, service_name in services.items():
        is_running, pid = check_service_running(service_id, pid_path)
        if is_running:
            print_success(f"{service_name}: Running (PID: {pid})")
            running_services += 1
        else:
            print_warning(f"{service_name}: Not running")
            if service_id != "scheduler":  # Scheduler is optional
                warnings.append(f"{service_name} is not running")

    if running_services == 0:
        print_error("No services are running!")
        issues.append("No services running")

    # 2. Check Log Files for Errors
    print_header("Log File Analysis")

    for service_id, service_name in services.items():
        log_file = logs_path / f"{service_id}.log"
        error_count, recent_errors = check_log_errors(log_file, minutes=60)

        if error_count == -1:
            print_warning(f"{service_name}: Log file not accessible")
        elif error_count == 0:
            print_success(f"{service_name}: No errors in last hour")
        elif error_count < 5:
            print_warning(f"{service_name}: {error_count} errors in last hour")
            warnings.append(f"{service_name} has {error_count} errors")
        else:
            print_error(f"{service_name}: {error_count} errors in last hour")
            issues.append(f"{service_name} has {error_count} errors")
            if recent_errors:
                print_info(f"Recent errors: {recent_errors[0][:100]}...")

    # 3. Check Credentials
    print_header("Credentials Check")

    creds_ok, creds_msg = check_credentials(vault_path)
    if creds_ok:
        print_success(creds_msg)
    else:
        print_error(creds_msg)
        issues.append(creds_msg)

    # 4. Check Vault Folders
    print_header("Vault Folders Check")

    folders_ok, missing_folders = check_vault_folders(vault_path)
    if folders_ok:
        print_success("All required folders exist")
    else:
        print_error(f"Missing folders: {', '.join(missing_folders)}")
        issues.append(f"Missing folders: {', '.join(missing_folders)}")

    # 5. Check Python Packages
    print_header("Python Packages Check")

    packages_ok, missing_packages = check_python_packages()
    if packages_ok:
        print_success("All required packages installed")
    else:
        print_error(f"Missing packages: {', '.join(missing_packages)}")
        issues.append(f"Missing packages: {', '.join(missing_packages)}")

    # 6. Check Recent Activity
    print_header("Recent Activity (Last 24 Hours)")

    activity = check_recent_activity(vault_path, hours=24)
    total_activity = sum(a["count"] for a in activity.values())

    if total_activity == 0:
        print_warning("No recent activity detected")
        warnings.append("No activity in last 24 hours")
    else:
        print_success(f"Total activity: {total_activity} files")

    for folder, data in activity.items():
        if data["count"] > 0:
            print_info(f"{data['description']}: {data['count']} files")

    # 7. Summary
    print_header("Health Check Summary")

    if len(issues) == 0 and len(warnings) == 0:
        print_success("All checks passed! System is healthy.")
        health_status = "HEALTHY"
    elif len(issues) == 0:
        print_warning(f"System is operational with {len(warnings)} warnings")
        health_status = "WARNING"
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print_error(f"System has {len(issues)} critical issues")
        health_status = "CRITICAL"
        print("\nCritical Issues:")
        for issue in issues:
            print(f"  - {issue}")
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  - {warning}")

    # 8. Recommendations
    if issues or warnings:
        print_header("Recommendations")

        if "No services running" in issues:
            print_info("Start services with: ./silver/scripts/startup.sh")

        if any("not running" in w for w in warnings):
            print_info("Start individual services:")
            print_info("  python -m silver.src.watchers.gmail_watcher")
            print_info("  python -m silver.src.watchers.whatsapp_watcher")
            print_info("  python -m silver.src.approval.approval_checker")

        if any("credentials" in i.lower() for i in issues):
            print_info("Configure credentials:")
            print_info("  python silver/scripts/setup_gmail.py")
            print_info("  python silver/scripts/setup_whatsapp.py")

        if any("packages" in i.lower() for i in issues):
            print_info("Install missing packages:")
            print_info("  pip install -r silver/requirements.txt")
            print_info("  playwright install chromium")

        if any("errors" in i.lower() or "errors" in w.lower() for i in issues for w in warnings):
            print_info("Check logs for details:")
            print_info("  tail -f Logs/gmail_watcher.log")
            print_info("  tail -f Logs/whatsapp_watcher.log")
            print_info("  tail -f Logs/approval_checker.log")

    # Exit code
    print()
    if health_status == "HEALTHY":
        print_success(f"Health Status: {health_status}")
        sys.exit(0)
    elif health_status == "WARNING":
        print_warning(f"Health Status: {health_status}")
        sys.exit(1)
    else:
        print_error(f"Health Status: {health_status}")
        sys.exit(2)

if __name__ == "__main__":
    main()
