#!/bin/bash
"""
Silver Tier Startup Script

This script starts all Silver tier components in the correct order:
1. Gmail Watcher
2. WhatsApp Watcher
3. Approval Checker
4. Scheduler (optional)

Prerequisites:
- Gmail API credentials configured
- WhatsApp Web session active
- Python virtual environment activated
- All dependencies installed
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
LOGS_PATH="$VAULT_PATH/Logs"
PID_PATH="$SILVER_PATH/.pids"

# Create necessary directories
mkdir -p "$LOGS_PATH"
mkdir -p "$PID_PATH"

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

# Check if service is already running
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

# Start a service
start_service() {
    local service_name=$1
    local service_command=$2
    local log_file="$LOGS_PATH/${service_name}.log"
    local pid_file="$PID_PATH/${service_name}.pid"

    if is_running "$service_name"; then
        print_warning "$service_name is already running (PID: $(cat $pid_file))"
        return 0
    fi

    print_info "Starting $service_name..."

    # Start service in background
    nohup $service_command > "$log_file" 2>&1 &
    local pid=$!

    # Save PID
    echo $pid > "$pid_file"

    # Wait a moment and check if it's still running
    sleep 2
    if ps -p $pid > /dev/null 2>&1; then
        print_success "$service_name started (PID: $pid)"
        return 0
    else
        print_error "$service_name failed to start"
        rm -f "$pid_file"
        return 1
    fi
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    local all_ok=true

    # Check Python
    if command -v python3 &> /dev/null; then
        print_success "Python 3 installed"
    else
        print_error "Python 3 not found"
        all_ok=false
    fi

    # Check virtual environment
    if [ -n "$VIRTUAL_ENV" ]; then
        print_success "Virtual environment activated: $VIRTUAL_ENV"
    else
        print_warning "Virtual environment not activated"
        print_info "Activate with: source venv/bin/activate"
    fi

    # Check Gmail credentials
    if [ -f "$VAULT_PATH/silver/config/.env" ]; then
        if grep -q "GMAIL_CLIENT_ID" "$VAULT_PATH/silver/config/.env"; then
            print_success "Gmail credentials configured"
        else
            print_warning "Gmail credentials not configured"
            print_info "Run: python silver/scripts/setup_gmail.py"
        fi
    else
        print_warning ".env file not found"
        print_info "Run: python silver/scripts/setup_gmail.py"
    fi

    # Check WhatsApp session
    if [ -d "$SILVER_PATH/config/whatsapp_session" ]; then
        print_success "WhatsApp session exists"
    else
        print_warning "WhatsApp session not configured"
        print_info "Run: python silver/scripts/setup_whatsapp.py"
    fi

    # Check LinkedIn session
    if [ -d "$SILVER_PATH/config/linkedin_session" ]; then
        print_success "LinkedIn session exists"
    else
        print_warning "LinkedIn session not configured"
        print_info "Run: python silver/scripts/setup_linkedin.py"
    fi

    # Check required Python packages
    if python3 -c "import google.auth" 2>/dev/null; then
        print_success "Google API libraries installed"
    else
        print_warning "Google API libraries not installed"
        print_info "Run: pip install -r silver/requirements.txt"
    fi

    if python3 -c "import playwright" 2>/dev/null; then
        print_success "Playwright installed"
    else
        print_warning "Playwright not installed"
        print_info "Run: pip install playwright && playwright install chromium"
    fi

    echo ""

    if [ "$all_ok" = false ]; then
        print_error "Some prerequisites are missing"
        return 1
    fi

    return 0
}

# Start all services
start_all_services() {
    print_header "Starting Silver Tier Services"

    local failed=false

    # Start Gmail Watcher
    if ! start_service "gmail_watcher" "python3 -m silver.src.watchers.gmail_watcher"; then
        failed=true
    fi

    # Start WhatsApp Watcher
    if ! start_service "whatsapp_watcher" "python3 -m silver.src.watchers.whatsapp_watcher"; then
        failed=true
    fi

    # Start Approval Checker
    if ! start_service "approval_checker" "python3 -m silver.src.approval.approval_checker"; then
        failed=true
    fi

    # Start LinkedIn Scheduler
    if ! start_service "linkedin_scheduler" "python3 $SILVER_PATH/scripts/linkedin_scheduler.py"; then
        print_warning "LinkedIn scheduler failed to start (may need session setup)"
    fi

    # Start Scheduler (optional)
    read -p "Start general Scheduler? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if ! start_service "scheduler" "python3 -m silver.src.scheduling.scheduler"; then
            failed=true
        fi
    else
        print_info "General scheduler not started (can be started manually later)"
    fi

    echo ""

    if [ "$failed" = true ]; then
        print_error "Some services failed to start"
        return 1
    fi

    print_success "All services started successfully"
    return 0
}

# Show service status
show_status() {
    print_header "Service Status"

    local services=("gmail_watcher" "whatsapp_watcher" "approval_checker" "linkedin_scheduler" "scheduler")

    for service in "${services[@]}"; do
        if is_running "$service"; then
            local pid=$(cat "$PID_PATH/${service}.pid")
            print_success "$service: Running (PID: $pid)"
        else
            print_warning "$service: Not running"
        fi
    done

    echo ""
}

# Show log locations
show_logs() {
    print_header "Log Files"

    echo "Logs are located in: $LOGS_PATH"
    echo ""
    echo "View logs with:"
    echo "  tail -f $LOGS_PATH/gmail_watcher.log"
    echo "  tail -f $LOGS_PATH/whatsapp_watcher.log"
    echo "  tail -f $LOGS_PATH/approval_checker.log"
    echo "  tail -f $LOGS_PATH/linkedin_scheduler.log"
    echo "  tail -f $LOGS_PATH/scheduler.log"
    echo ""
}

# Main
main() {
    print_header "Silver Tier Startup"
    echo ""

    # Check prerequisites
    if ! check_prerequisites; then
        print_error "Prerequisites check failed"
        print_info "Fix the issues above and try again"
        exit 1
    fi

    # Start services
    if ! start_all_services; then
        print_error "Failed to start all services"
        show_status
        exit 1
    fi

    # Show status
    show_status

    # Show log locations
    show_logs

    print_success "Silver Tier startup complete!"
    print_info "Monitor logs to verify services are working correctly"
    print_info "Stop services with: ./silver/scripts/shutdown.sh"
}

# Run main
main
