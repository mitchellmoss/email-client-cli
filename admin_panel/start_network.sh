#!/bin/bash

# Start script for admin panel accessible over local network

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the local IP address
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    LOCAL_IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1)
else
    # Linux
    LOCAL_IP=$(hostname -I | awk '{print $1}')
fi

if [ -z "$LOCAL_IP" ]; then
    echo -e "${RED}Could not determine local IP address${NC}"
    exit 1
fi

echo -e "${GREEN}Your local IP address is: ${LOCAL_IP}${NC}"

# Create .env.local for frontend with correct API URL
echo "VITE_API_URL=http://${LOCAL_IP}:8000" > admin_panel/frontend/.env.local
echo -e "${GREEN}Created frontend .env.local with API URL: http://${LOCAL_IP}:8000${NC}"

# Export CORS_ORIGINS to allow the frontend to connect
export CORS_ORIGINS="http://${LOCAL_IP}:5173,http://localhost:5173"

# Function to stop all services on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping all services...${NC}"
    
    # Kill backend
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    
    # Kill frontend
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    
    # Kill any remaining processes on the ports
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    lsof -ti:5173 | xargs kill -9 2>/dev/null
    
    echo -e "${GREEN}All services stopped${NC}"
    exit 0
}

# Set trap to cleanup on exit
trap cleanup EXIT INT TERM

# Start backend (bound to all interfaces)
echo -e "${YELLOW}Starting backend API server on 0.0.0.0:8000...${NC}"
cd admin_panel/backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt -q

# Start backend with host binding to all interfaces
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
echo -e "${YELLOW}Waiting for backend to start...${NC}"
sleep 5

# Start frontend
echo -e "${YELLOW}Starting frontend on 0.0.0.0:5173...${NC}"
cd ../../admin_panel/frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
fi

# Start frontend with host binding to all interfaces
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 5

echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}Admin panel is running!${NC}"
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}Access from this machine: http://localhost:5173${NC}"
echo -e "${GREEN}Access from network: http://${LOCAL_IP}:5173${NC}"
echo -e "${GREEN}API docs: http://${LOCAL_IP}:8000/docs${NC}"
echo -e "${GREEN}==========================================${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Wait for user to stop
wait