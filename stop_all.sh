#!/bin/bash

# Email Client CLI - Stop All Services Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

echo ""
print_status "Stopping Email Client CLI services..."
echo ""

# Kill processes by name
services_stopped=0

# Stop main email processor
if pkill -f "python main.py"; then
    print_success "Email processor stopped"
    ((services_stopped++))
else
    print_error "Email processor was not running"
fi

# Stop admin backend (uvicorn)
if pkill -f "uvicorn main:app"; then
    print_success "Admin backend stopped"
    ((services_stopped++))
else
    print_error "Admin backend was not running"
fi

# Stop admin frontend (vite/npm)
if pkill -f "vite.*admin_panel/frontend"; then
    print_success "Admin frontend stopped"
    ((services_stopped++))
else
    print_error "Admin frontend was not running"
fi

# Also try to kill any npm dev processes in the frontend directory
pkill -f "npm.*dev.*admin_panel/frontend" 2>/dev/null

echo ""
if [ $services_stopped -gt 0 ]; then
    print_success "Stopped $services_stopped service(s)"
else
    print_status "No services were running"
fi
echo ""