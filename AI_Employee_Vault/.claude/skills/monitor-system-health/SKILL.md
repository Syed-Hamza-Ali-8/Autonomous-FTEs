# Monitor System Health Skill

**Skill ID**: monitor-system-health
**Version**: 1.0.0
**User Story**: US-GOLD-3 - System Health Monitoring
**Priority**: P1 (Gold Tier MVP)

## Purpose

Monitor the health and availability of all system components including MCP servers, vault accessibility, disk space, and process status. This skill ensures the AI Employee system remains operational and proactively detects issues before they impact functionality.

## Capabilities

- **MCP Server Health**: Check connectivity and response time of all MCP servers
- **Vault Accessibility**: Verify read/write access to Obsidian vault
- **Disk Space Monitoring**: Track available disk space and alert on low storage
- **Process Status**: Monitor PM2 processes and restart if needed
- **Performance Metrics**: Track CPU, memory, and network usage
- **Error Detection**: Identify and log system errors
- **Automated Recovery**: Attempt automatic recovery for common issues
- **Health Reports**: Generate health status reports

## Architecture

### Core Components

1. **HealthMonitor** (`gold/src/core/health_monitor.py`)
   - `check_all_systems()` → Dict[system: status]
   - `check_mcp_servers()` → Dict[server: health]
   - `check_vault_access()` → bool
   - `check_disk_space()` → Dict[usage]
   - `check_processes()` → List[ProcessStatus]

2. **MCPHealthChecker** (`gold/src/monitoring/mcp_health_checker.py`)
   - `ping_server(server_url)` → Dict[status, latency]
   - `test_tool_call(server_url, tool_name)` → bool

3. **SystemRecovery** (`gold/src/core/system_recovery.py`)
   - `restart_mcp_server(server_name)` → bool
   - `restart_process(process_name)` → bool
   - `clear_temp_files()` → bool

### Monitoring Workflow

```
1. Scheduled Check → Run every 60 seconds
                  → Check all system components
                  → Log results

2. Health Assessment → Evaluate each component
                    → Determine overall health status
                    → Identify degraded services

3. Issue Detection → Detect failures or degradation
                  → Classify by severity
                  → Attempt automatic recovery

4. Recovery Actions → Restart failed services
                   → Clear temporary files
                   → Notify user if manual intervention needed

5. Reporting → Log health status
            → Create alert if critical
            → Update health dashboard
```

## Configuration

### Health Monitor Config (`gold/config/health_monitor_config.yaml`)

```yaml
monitoring:
  enabled: true
  interval_seconds: 60
  alert_on_failure: true

checks:
  mcp_servers:
    enabled: true
    timeout_seconds: 5
    servers:
      - name: "email-mcp"
        url: "http://localhost:3000"
        critical: true
      - name: "odoo-mcp"
        url: "http://localhost:3002"
        critical: true

  vault:
    enabled: true
    test_read: true
    test_write: true
    critical: true

  disk_space:
    enabled: true
    warning_threshold_gb: 5
    critical_threshold_gb: 1

  processes:
    enabled: true
    check_pm2: true
    critical_processes:
      - "gold-health-monitor"
      - "gold-watchdog"
      - "gold-ceo-briefing"

recovery:
  auto_restart: true
  max_restart_attempts: 3
  restart_cooldown_seconds: 60

alerts:
  critical_threshold: 2  # Alert if 2+ critical systems down
  notification_method: "file"  # file, email, desktop
  notification_path: "Needs_Action/"
```

## Usage

### Manual Health Check

```python
from gold.src.core.health_monitor import HealthMonitor

monitor = HealthMonitor(vault_path="/path/to/vault")

# Check all systems
health_status = monitor.check_all_systems()

print(f"Overall Status: {health_status['overall_status']}")
print(f"Healthy Systems: {health_status['healthy_count']}/{health_status['total_count']}")

# Check specific component
mcp_status = monitor.check_mcp_servers()
for server, status in mcp_status.items():
    print(f"{server}: {status['status']} ({status['latency']}ms)")
```

### Using Claude Code Skill

```bash
# Run health check
claude --skill monitor-system-health

# Check specific component
claude --skill monitor-system-health --component mcp-servers

# Generate health report
claude --skill monitor-system-health --report
```

### Continuous Monitoring (PM2)

```bash
# Start health monitor
pm2 start gold/ecosystem.config.js --only gold-health-monitor

# Check status
pm2 list | grep health-monitor

# View logs
pm2 logs gold-health-monitor
```

## Output Format

### Health Status Report

```json
{
  "timestamp": "2026-01-19T16:30:00Z",
  "overall_status": "healthy",
  "healthy_count": 4,
  "degraded_count": 0,
  "failed_count": 0,
  "total_count": 4,
  "components": {
    "mcp_servers": {
      "status": "healthy",
      "servers": {
        "email-mcp": {
          "status": "healthy",
          "url": "http://localhost:3000",
          "latency_ms": 45,
          "last_check": "2026-01-19T16:30:00Z"
        },
        "odoo-mcp": {
          "status": "healthy",
          "url": "http://localhost:3002",
          "latency_ms": 67,
          "last_check": "2026-01-19T16:30:00Z"
        }
      }
    },
    "vault": {
      "status": "healthy",
      "read_access": true,
      "write_access": true,
      "path": "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
    },
    "disk_space": {
      "status": "healthy",
      "available_gb": 45.2,
      "used_gb": 234.8,
      "total_gb": 280.0,
      "usage_percent": 84
    },
    "processes": {
      "status": "healthy",
      "running": 7,
      "stopped": 0,
      "errored": 0,
      "processes": [
        {"name": "gold-health-monitor", "status": "online", "uptime": "2d 5h"},
        {"name": "gold-watchdog", "status": "online", "uptime": "2d 5h"},
        {"name": "gold-ceo-briefing", "status": "online", "uptime": "2d 5h"}
      ]
    }
  }
}
```

### Critical Alert (Needs_Action/)

```markdown
---
type: system_health_alert
severity: critical
created_at: 2026-01-19T16:30:00Z
---

# 🚨 Critical System Health Alert

**Status**: Critical
**Time**: 2026-01-19 4:30 PM
**Failed Components**: 2

## Failed Systems

### Odoo MCP Server ❌
- **Status**: Unreachable
- **URL**: http://localhost:3002
- **Error**: Connection refused
- **Last Successful Check**: 2026-01-19 4:25 PM
- **Action**: Restart Odoo MCP server

### Disk Space ⚠️
- **Status**: Critical
- **Available**: 0.8 GB
- **Threshold**: 1.0 GB
- **Action**: Free up disk space immediately

## Recovery Actions Attempted

1. ✅ Attempted to restart Odoo MCP server (failed)
2. ⏳ Cleared temporary files (freed 0.2 GB)

## Manual Intervention Required

Please address the following:
1. Restart Odoo MCP server manually: `pm2 restart odoo-mcp`
2. Free up disk space (delete old logs, backups)
3. Verify system health after actions: `claude --skill monitor-system-health`
```

## Dependencies

```toml
[tool.poetry.dependencies]
psutil = "^5.9.0"  # System monitoring
requests = "^2.31.0"  # MCP health checks
pyyaml = "^6.0.1"
python-dotenv = "^1.0.0"
```

## Setup Instructions

```bash
# 1. Configure health monitoring
nano gold/config/health_monitor_config.yaml

# 2. Test health check
python gold/src/core/health_monitor.py

# 3. Start continuous monitoring
pm2 start gold/ecosystem.config.js --only gold-health-monitor

# 4. Verify monitoring
pm2 logs gold-health-monitor
```

## Success Criteria

- ✅ All system components monitored every 60 seconds
- ✅ MCP servers health checked with latency tracking
- ✅ Vault accessibility verified
- ✅ Disk space monitored with alerts
- ✅ PM2 processes tracked
- ✅ Automatic recovery attempted for failures
- ✅ Critical alerts created in Needs_Action/
- ✅ Health status logged to audit trail

## Related Skills

- **execute-actions**: Uses MCP servers monitored by this skill
- **generate-ceo-briefing**: Includes system health in briefing
- **manage-approvals**: May require approval for recovery actions

## Changelog

- **1.0.0** (2026-01-19): Initial implementation for Gold tier
