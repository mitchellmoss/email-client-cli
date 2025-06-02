#!/bin/bash

# Email Client CLI - Complete System Startup Script
# This script starts all components: main processor, admin backend, and admin frontend

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Function to get machine IP address
get_ip() {
    # Try different methods to get IP
    if command -v ip >/dev/null 2>&1; then
        # Linux with ip command
        ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1' | head -1
    elif command -v ifconfig >/dev/null 2>&1; then
        # macOS/BSD or older Linux
        ifconfig | grep -E "inet\s" | grep -v '127.0.0.1' | awk '{print $2}' | sed 's/addr://' | head -1
    elif command -v hostname >/dev/null 2>&1; then
        # Fallback using hostname
        hostname -I 2>/dev/null | awk '{print $1}' || hostname -i 2>/dev/null | grep -v '127.0.0.1'
    else
        echo "localhost"
    fi
}

# Detect if we should use network mode
MACHINE_IP=$(get_ip)
USE_NETWORK_MODE=false

# Check if --network flag is passed or if accessed from non-localhost
if [[ "$1" == "--network" ]] || [[ -n "$SSH_CLIENT" ]] || [[ -n "$SSH_TTY" ]]; then
    USE_NETWORK_MODE=true
    print_status "Network mode enabled - services will be accessible from other machines"
    print_status "Detected IP address: $MACHINE_IP"
fi

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to kill all child processes on exit
cleanup() {
    print_status "Shutting down all services..."
    
    # Kill all child processes
    pkill -P $$ || true
    
    # Kill specific processes by name as backup
    pkill -f "python main.py" || true
    pkill -f "uvicorn" || true
    pkill -f "vite" || true
    
    print_success "All services stopped"
    exit 0
}

# Trap signals to ensure cleanup
trap cleanup EXIT INT TERM

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists python3; then
    print_error "Python 3 is not installed"
    exit 1
fi

if ! command_exists node; then
    print_error "Node.js is not installed"
    exit 1
fi

if ! command_exists npm; then
    print_error "npm is not installed"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found. Please copy .env.example and configure it."
    exit 1
fi

print_success "All prerequisites met"

# Create log directory
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# Function to wait for a service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|404"; then
            print_success "$name is ready"
            return 0
        fi
        
        printf "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    print_error "$name failed to start"
    return 1
}

# Start main email processor
print_status "Starting email processor..."

# Check if virtual environment exists for main
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found for main app. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q -r requirements.txt
else
    source venv/bin/activate
fi

# Start main.py in background using venv python
./venv/bin/python main.py > "$LOG_DIR/email_processor.log" 2>&1 &
MAIN_PID=$!
print_success "Email processor started (PID: $MAIN_PID)"

# Start admin panel backend
print_status "Starting admin panel backend..."

cd "$SCRIPT_DIR/admin_panel/backend"

# Debug: Show current directory
print_status "Backend directory: $(pwd)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found for backend. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    print_status "Installing backend requirements..."
    pip install wheel setuptools --upgrade
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        print_error "Failed to install backend requirements"
        exit 1
    fi
else
    source venv/bin/activate
fi

# Debug: Show Python version and location
print_status "Python version: $(./venv/bin/python --version)"
print_status "Python path: $(which python)"

# Set PYTHONPATH to include parent directories for imports
export PYTHONPATH="$(pwd):$(pwd)/../..:${PYTHONPATH}"
print_status "PYTHONPATH set to: $PYTHONPATH"

# Set CORS origins for network access
if [ "$USE_NETWORK_MODE" = true ]; then
    export CORS_ORIGINS="http://${MACHINE_IP}:5173,http://localhost:5173,http://127.0.0.1:5173"
    export FRONTEND_URL="http://${MACHINE_IP}:5173"
    print_status "CORS configured for network access: $CORS_ORIGINS"
fi

# Debug: Test imports before starting
print_status "Testing Python imports..."
./venv/bin/python -c "import sys; print('sys.path:', sys.path)" > "$LOG_DIR/backend_import_test.log" 2>&1
./venv/bin/python -c "from config import settings; print('Config import successful')" >> "$LOG_DIR/backend_import_test.log" 2>&1
if [ $? -ne 0 ]; then
    print_error "Python import test failed. Check $LOG_DIR/backend_import_test.log"
    cat "$LOG_DIR/backend_import_test.log"
fi

# Check if port 8000 is already in use
if lsof -i :8000 >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":8000 "; then
    print_warning "Port 8000 is already in use. Attempting to kill existing process..."
    pkill -f "uvicorn.*8000" || true
    sleep 2
fi

# Start FastAPI backend using venv python with more verbose logging
print_status "Starting uvicorn server..."
./venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug > "$LOG_DIR/admin_backend.log" 2>&1 &
BACKEND_PID=$!

# Check if process started
sleep 2
if ! ps -p $BACKEND_PID > /dev/null; then
    print_error "Backend process failed to start. Last 20 lines of log:"
    tail -n 20 "$LOG_DIR/admin_backend.log"
    exit 1
fi

print_success "Admin backend starting (PID: $BACKEND_PID)"

# Show initial backend logs
print_status "Initial backend logs:"
sleep 1
tail -n 10 "$LOG_DIR/admin_backend.log"

# Wait for backend to be ready with more detailed logging
wait_for_service "http://localhost:8000/health" "Admin Backend"
if [ $? -ne 0 ]; then
    print_error "Backend failed to become ready. Last 50 lines of log:"
    tail -n 50 "$LOG_DIR/admin_backend.log"
    exit 1
fi

# Start admin panel frontend
print_status "Starting admin panel frontend..."

cd "$SCRIPT_DIR/admin_panel/frontend"

# Debug: Show current directory
print_status "Frontend directory: $(pwd)"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_warning "Node modules not found. Installing dependencies..."
    npm install --silent
fi

# Check if src/lib/utils.ts exists
if [ ! -f "src/lib/utils.ts" ]; then
    print_error "Missing src/lib/utils.ts file!"
    print_status "Creating missing utils file..."
    mkdir -p src/lib
    cat > src/lib/utils.ts << 'EOF'
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
EOF
fi

# Configure frontend for network access
if [ "$USE_NETWORK_MODE" = true ]; then
    print_status "Configuring frontend for network access..."
    cat > .env.local << EOF
VITE_API_URL=http://${MACHINE_IP}:8000
EOF
    print_status "Frontend API URL set to: http://${MACHINE_IP}:8000"
fi

# Clear any potentially conflicting NODE_PATH
unset NODE_PATH

# Start Vite dev server with explicit working directory
(cd "$SCRIPT_DIR/admin_panel/frontend" && npm run dev -- --host 0.0.0.0) > "$LOG_DIR/admin_frontend.log" 2>&1 &
FRONTEND_PID=$!
print_success "Admin frontend starting (PID: $FRONTEND_PID)"

# Wait for frontend to be ready
wait_for_service "http://localhost:5173" "Admin Frontend"

# Print success message
echo ""
print_success "All services started successfully!"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Email Client CLI System is running!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "🚀 Services:"
echo "   📧 Email Processor: Running (checking every 5 minutes)"
if [ "$USE_NETWORK_MODE" = true ]; then
    echo "   🔧 Admin Backend:   http://${MACHINE_IP}:8000 (API docs: http://${MACHINE_IP}:8000/docs)"
    echo "   🌐 Admin Frontend:  http://${MACHINE_IP}:5173"
    echo ""
    echo "   📱 Local Access:    http://localhost:5173"
    echo "   🌐 Network Access:  http://${MACHINE_IP}:5173"
else
    echo "   🔧 Admin Backend:   http://localhost:8000 (API docs: http://localhost:8000/docs)"
    echo "   🌐 Admin Frontend:  http://localhost:5173"
    echo ""
    echo "   💡 Tip: Use './start_all.sh --network' to enable access from other devices"
fi
echo ""
echo "📋 Default Login:"
echo "   Email:    admin@example.com"
echo "   Password: changeme"
echo ""
echo "📁 Logs:"
echo "   Email Processor: $LOG_DIR/email_processor.log"
echo "   Admin Backend:   $LOG_DIR/admin_backend.log"
echo "   Admin Frontend:  $LOG_DIR/admin_frontend.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Keep script running and show combined logs
tail -f "$LOG_DIR"/*.log