#!/bin/bash
"""
Silver Tier Shutdown Script

This script gracefully stops all Silver tier components:
1. Scheduler
2. Approval Checker
3. WhatsApp Watcher
4. Gmail Watcher

Ensures clean shutdown with proper signal handling.
"""

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VAULT_PATH="${VAULT_PATH:-/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault}"
SILVER_PATH="$VAULT_PATH/silver"
PID_PATH="$SILVER_PATH/.pids"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if service is running
is_running() {
    local service_name=$1
    local pid_file="$PID_PATH/${service_name}.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Running
        else
            rm -f "$pid_file"  # Stale PID file
            return 1  # Not running
        fi
    fi
    return 1  # Not running
}

# Stop a service
stop_service() {
    local service_name=$1
    local pid_file="$PID_PATH/${service_name}.pid"

    if ! is_running "$service_name"; then
        print_warning "$service_name is not running"
        return 0
    fi

    local pid=$(cat "$pid_file")
    print_info "Stopping $service_name (PID: $pid)..."

    # Send SIGTERM for graceful shutdown
    kill -TERM $pid 2>/dev/null || true

    # Wait up to 10 seconds for graceful shutdown
    local count=0
    while [ $count -lt 10 ]; do
        if ! ps -p $pid > /dev/null 2>&1; then
            rm -f "$pid_file"
            print_success "$service_name stopped gracefully"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done

    # Force kill if still running
    print_warning "$service_name did not stop gracefully, forcing..."
    kill -KILL $pid 2>/dev/null || true
    rm -f "$pid_file"

    # Verify it's stopped
    if ! ps -p $pid > /dev/null 2>&1; then
        print_success "$service_name stopped (forced)"
        return 0
    else
        print_error "Failed to stop $service_name"
        return 1
    fi
}

# Show service status
show_status() {
    print_header "Service Status"

    local services=("gmail_watcher" "whatsapp_watcher" "approval_checker" "linkedin_scheduler" "scheduler")
    local any_running=false

    for service in "${services[@]}"; do
        if is_running "$service"; then
            local pid=$(cat "$PID_PATH/${service}.pid")
            print_warning "$service: Still running (PID: $pid)"
            any_running=true
        else
            print_success "$service: Stopped"
        fi
    done

    echo ""

    if [ "$any_running" = true ]; then
        return 1
    fi
    return 0
}

# Stop all services
stop_all_services() {
    print_header "Stopping Silver Tier Services"

    local failed=false

    # Stop in reverse order (opposite of startup)
    # Stop Scheduler first
    if ! stop_service "scheduler"; then
        failed=true
    fi

    # Stop LinkedIn Scheduler
    if ! stop_service "linkedin_scheduler"; then
        failed=true
    fi

    # Stop Approval Checker
    if ! stop_service "approval_checker"; then
        failed=true
    fi

    # Stop WhatsApp Watcher
    if ! stop_service "whatsapp_watcher"; then
        failed=true
    fi

    # Stop Gmail Watcher
    if ! stop_service "gmail_watcher"; then
        failed=true
    fi

    echo ""

    if [ "$failed" = true ]; then
        print_error "Some services failed to stop cleanly"
        return 1
    fi

    print_success "All services stopped successfully"
    return 0
}

# Clean up PID files
cleanup_pids() {
    print_info "Cleaning up PID files..."

    if [ -d "$PID_PATH" ]; then
        rm -f "$PID_PATH"/*.pid
        print_success "PID files cleaned up"
    fi
}

# Force stop all (emergency)
force_stop_all() {
    print_header "Force Stopping All Services"
    print_warning "This will forcefully kill all Silver tier processes"

    # Kill by process name
    pkill -9 -f "gmail_watcher" 2>/dev/null || true
    pkill -9 -f "whatsapp_watcher" 2>/dev/null || true
    pkill -9 -f "approval_checker" 2>/dev/null || true
    pkill -9 -f "scheduler" 2>/dev/null || true

    # Clean up PID files
    cleanup_pids

    print_success "All processes forcefully stopped"
}

# Main
main() {
    print_header "Silver Tier Shutdown"
    echo ""

    # Check if PID directory exists
    if [ ! -d "$PID_PATH" ]; then
        print_warning "PID directory not found, no services to stop"
        exit 0
    fi

    # Check for force flag
    if [ "$1" = "--force" ] || [ "$1" = "-f" ]; then
        force_stop_all
        exit 0
    fi

    # Stop services gracefully
    if ! stop_all_services; then
        print_error "Failed to stop all services gracefully"
        echo ""
        read -p "Force stop remaining services? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            force_stop_all
        else
            print_info "Some services may still be running"
            show_status
            exit 1
        fi
    fi

    # Show final status
    show_status

    # Clean up PID files
    cleanup_pids

    print_success "Silver Tier shutdown complete!"
}

# Handle Ctrl+C
trap 'echo ""; print_warning "Shutdown interrupted"; exit 130' INT

# Run main
main "$@"
