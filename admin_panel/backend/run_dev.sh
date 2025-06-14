#!/bin/bash

# Development server startup script

echo "Starting Email Order Admin Panel Backend..."

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
export PYTHONPATH="${PYTHONPATH}:$(pwd):$(pwd)/../.."

# Run the development server
echo "Starting FastAPI development server..."
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000