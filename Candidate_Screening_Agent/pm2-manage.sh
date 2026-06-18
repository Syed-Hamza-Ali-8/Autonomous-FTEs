#!/bin/bash

# PM2 Management Script for Candidate Screening Agent

case "$1" in
  start)
    echo "Starting Candidate Screening Agent with PM2..."
    cd /mnt/d/hamza/autonomous-ftes/Candidate_Screening_Agent
    pm2 start ecosystem.config.js
    pm2 save
    echo "✓ Services started"
    pm2 status
    ;;

  stop)
    echo "Stopping Candidate Screening Agent..."
    pm2 stop ecosystem.config.js
    echo "✓ Services stopped"
    ;;

  restart)
    echo "Restarting Candidate Screening Agent..."
    pm2 restart ecosystem.config.js
    echo "✓ Services restarted"
    pm2 status
    ;;

  status)
    pm2 status
    ;;

  logs)
    if [ -z "$2" ]; then
      pm2 logs
    else
      pm2 logs "$2"
    fi
    ;;

  delete)
    echo "Deleting PM2 processes..."
    pm2 delete ecosystem.config.js
    echo "✓ Processes deleted"
    ;;

  *)
    echo "Usage: $0 {start|stop|restart|status|logs|delete}"
    echo ""
    echo "Commands:"
    echo "  start    - Start both backend and frontend with PM2"
    echo "  stop     - Stop all services"
    echo "  restart  - Restart all services"
    echo "  status   - Show PM2 process status"
    echo "  logs     - Show logs (optionally specify service name)"
    echo "  delete   - Delete PM2 processes"
    exit 1
    ;;
esac
