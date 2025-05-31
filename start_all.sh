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

# Start main.py in background
python main.py > "$LOG_DIR/email_processor.log" 2>&1 &
MAIN_PID=$!
print_success "Email processor started (PID: $MAIN_PID)"

# Start admin panel backend
print_status "Starting admin panel backend..."

cd "$SCRIPT_DIR/admin_panel/backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found for backend. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q -r requirements.txt
else
    source venv/bin/activate
fi

# Start FastAPI backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload > "$LOG_DIR/admin_backend.log" 2>&1 &
BACKEND_PID=$!
print_success "Admin backend starting (PID: $BACKEND_PID)"

# Wait for backend to be ready
wait_for_service "http://localhost:8000/health" "Admin Backend"

# Start admin panel frontend
print_status "Starting admin panel frontend..."

cd "$SCRIPT_DIR/admin_panel/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_warning "Node modules not found. Installing dependencies..."
    npm install --silent
fi

# Start Vite dev server
npm run dev -- --host 0.0.0.0 > "$LOG_DIR/admin_frontend.log" 2>&1 &
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
echo "   🔧 Admin Backend:   http://localhost:8000 (API docs: http://localhost:8000/docs)"
echo "   🌐 Admin Frontend:  http://localhost:5173"
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