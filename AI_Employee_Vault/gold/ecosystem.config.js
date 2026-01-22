// PM2 Ecosystem Configuration for Gold Tier
// Manages all Gold Tier processes with auto-restart and monitoring

module.exports = {
  apps: [
    // Health Monitor - Continuous health checking
    {
      name: 'gold-health-monitor',
      script: 'python3',
      args: 'gold/src/core/health_monitor.py --continuous --interval 60',
      cwd: '/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault',
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONPATH: '/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault',
        LOG_LEVEL: 'INFO'
      },
      error_file: './Logs/pm2/gold-health-monitor-error.log',
      out_file: './Logs/pm2/gold-health-monitor-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    },

    // Watchdog - Process monitoring and auto-restart
    {
      name: 'gold-watchdog',
      script: 'python3',
      args: 'gold/src/core/watchdog.py --interval 30',
      cwd: '/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault',
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONPATH: '/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault',
        LOG_LEVEL: 'INFO'
      },
      error_file: './Logs/pm2/gold-watchdog-error.log',
      out_file: './Logs/pm2/gold-watchdog-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    },

    // Facebook Watcher (Phase 2)
    {
      name: 'gold-facebook-watcher',
      script: 'python3',
      args: 'gold/src/watchers/facebook_watcher.py --continuous',
      cwd: '/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault',
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONPATH: '/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault',
        LOG_LEVEL: 'INFO'
      },
      error_file: './Logs/pm2/gold-facebook-watcher-error.log',
      out_file: './Logs/pm2/gold-facebook-watcher-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    },

    // Instagram Watcher (Phase 2)
    {
      name: 'gold-instagram-watcher',
      script: 'python3',
      args: 'gold/src/watchers/instagram_watcher.py --continuous',
      cwd: '/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault',
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONPATH: '/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault',
        LOG_LEVEL: 'INFO'
      },
      error_file: './Logs/pm2/gold-instagram-watcher-error.log',
      out_file: './Logs/pm2/gold-instagram-watcher-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    },

    // Twitter Watcher (Phase 2)
    {
      name: 'gold-twitter-watcher',
      script: 'python3',
      args: 'gold/src/watchers/twitter_watcher.py --continuous',
      cwd: '/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault',
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONPATH: '/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault',
        LOG_LEVEL: 'INFO'
      },
      error_file: './Logs/pm2/gold-twitter-watcher-error.log',
      out_file: './Logs/pm2/gold-twitter-watcher-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    },

    // CEO Briefing Scheduler (Phase 3)
    // Runs every Sunday at 7:00 AM
    {
      name: 'gold-ceo-briefing',
      script: 'python3',
      args: 'gold/src/intelligence/ceo_briefing.py --schedule',
      cwd: '/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault',
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      cron_restart: '0 7 * * 0',  // Every Sunday at 7:00 AM
      env: {
        PYTHONPATH: '/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault',
        LOG_LEVEL: 'INFO',
        USE_MOCK_XERO: 'true'  // Change to 'false' in Phase 4
      },
      error_file: './Logs/pm2/gold-ceo-briefing-error.log',
      out_file: './Logs/pm2/gold-ceo-briefing-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    },

    // System Monitor - Monitors all Gold Tier processes
    // Checks every 15 minutes for issues
    {
      name: 'gold-system-monitor',
      script: 'python3',
      args: 'gold/src/monitoring/system_monitor.py --continuous --interval 15',
      cwd: '/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault',
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONPATH: '/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault',
        LOG_LEVEL: 'INFO'
      },
      error_file: './Logs/pm2/gold-system-monitor-error.log',
      out_file: './Logs/pm2/gold-system-monitor-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    }
  ]
};
