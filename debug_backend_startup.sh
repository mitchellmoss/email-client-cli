#!/bin/bash

# Debug script for backend startup issues

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Backend Startup Debug Script${NC}"
echo "=============================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check Python version
echo -e "\n${YELLOW}System Python Info:${NC}"
echo "Python3 version: $(python3 --version 2>&1 || echo 'Not found')"
echo "Python3 path: $(which python3 2>&1 || echo 'Not found')"

# Navigate to backend
cd admin_panel/backend

echo -e "\n${YELLOW}Backend Directory:${NC}"
pwd
ls -la

# Check virtual environment
echo -e "\n${YELLOW}Virtual Environment:${NC}"
if [ -d "venv" ]; then
    echo "✓ Virtual environment exists"
    source venv/bin/activate
    echo "Python in venv: $(which python)"
    echo "Python version in venv: $(python --version)"
else
    echo "✗ No virtual environment found"
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing wheel and setuptools..."
    pip install wheel setuptools --upgrade
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Test PYTHONPATH
echo -e "\n${YELLOW}PYTHONPATH Configuration:${NC}"
export PYTHONPATH="$(pwd):$(pwd)/../..:${PYTHONPATH}"
echo "PYTHONPATH=$PYTHONPATH"

# Test imports
echo -e "\n${YELLOW}Testing Imports:${NC}"

# Test 1: sys.path
echo "1. Testing sys.path..."
python -c "import sys; import json; print(json.dumps(sys.path, indent=2))"

# Test 2: Import config
echo -e "\n2. Testing config import..."
python -c "try:
    from config import settings
    print('✓ Config import successful')
    print(f'  Admin email: {settings.ADMIN_EMAIL}')
except Exception as e:
    print(f'✗ Config import failed: {e}')"

# Test 3: Import database
echo -e "\n3. Testing database import..."
python -c "try:
    from database import get_db
    print('✓ Database import successful')
except Exception as e:
    print(f'✗ Database import failed: {e}')"

# Test 4: Import API modules
echo -e "\n4. Testing API imports..."
python -c "try:
    from api import auth, orders
    print('✓ API imports successful')
except Exception as e:
    print(f'✗ API imports failed: {e}')"

# Test 5: Import src modules
echo -e "\n5. Testing src module imports..."
python -c "try:
    import sys
    sys.path.insert(0, '../../src')
    from email_fetcher import EmailFetcher
    print('✓ Src module import successful')
except Exception as e:
    print(f'✗ Src module import failed: {e}')"

# Check for port conflicts
echo -e "\n${YELLOW}Port 8000 Status:${NC}"
if lsof -i :8000 >/dev/null 2>&1; then
    echo "✗ Port 8000 is in use:"
    lsof -i :8000
elif netstat -tuln 2>/dev/null | grep -q ":8000 "; then
    echo "✗ Port 8000 is in use:"
    netstat -tuln | grep ":8000 "
else
    echo "✓ Port 8000 is available"
fi

# Try starting uvicorn
echo -e "\n${YELLOW}Attempting to start uvicorn:${NC}"
echo "Command: python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug"
echo "Press Ctrl+C to stop..."
echo ""

# Start with full debugging
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug