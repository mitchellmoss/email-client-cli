#!/bin/bash

# Development server startup script with improved error handling

echo "Starting Email Order Admin Panel Backend..."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Add psutil for system monitoring
pip install psutil

# Export PYTHONPATH to include parent directories
export PYTHONPATH="${SCRIPT_DIR}:${SCRIPT_DIR}/../..:${PYTHONPATH}"

echo "PYTHONPATH set to: $PYTHONPATH"
echo "Current directory: $(pwd)"

# Run the development server using python -m to ensure proper module resolution
echo "Starting FastAPI development server..."
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000