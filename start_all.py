#!/usr/bin/env python3
"""
Email Client CLI - Cross-platform startup script
Starts all components: main processor, admin backend, and admin frontend
"""

import os
import sys
import subprocess
import time
import signal
import atexit
import platform
import shutil
import requests
from pathlib import Path
from datetime import datetime

# ANSI color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

# Store process handles
processes = []

def print_status(message):
    """Print status message with timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{BLUE}[{timestamp}]{NC} {message}")

def print_success(message):
    """Print success message."""
    print(f"{GREEN}✓{NC} {message}")

def print_error(message):
    """Print error message."""
    print(f"{RED}✗{NC} {message}")

def print_warning(message):
    """Print warning message."""
    print(f"{YELLOW}!{NC} {message}")

def cleanup():
    """Kill all child processes on exit."""
    print_status("Shutting down all services...")
    
    for process in processes:
        if process.poll() is None:  # Process is still running
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    
    print_success("All services stopped")

def check_command(command):
    """Check if a command exists."""
    return shutil.which(command) is not None

def wait_for_service(url, name, max_attempts=30):
    """Wait for a service to be ready."""
    print_status(f"Waiting for {name} to be ready...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=1)
            if response.status_code in [200, 404]:
                print_success(f"{name} is ready")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(".", end="", flush=True)
        time.sleep(1)
    
    print()
    print_error(f"{name} failed to start")
    return False

def setup_venv(path, requirements_file):
    """Set up virtual environment if it doesn't exist."""
    venv_path = path / "venv"
    
    if not venv_path.exists():
        print_warning("Virtual environment not found. Creating...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        
        # Install requirements
        if platform.system() == "Windows":
            pip_path = venv_path / "Scripts" / "pip.exe"
        else:
            pip_path = venv_path / "bin" / "pip"
        
        subprocess.run([str(pip_path), "install", "-q", "-r", str(requirements_file)], check=True)
        print_success("Virtual environment created")
    
    return venv_path

def get_python_executable(venv_path):
    """Get the python executable path for the virtual environment."""
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def main():
    """Main function to start all services."""
    # Register cleanup
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
    
    # Get script directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    print()
    print("=" * 60)
    print("Email Client CLI - Starting All Services")
    print("=" * 60)
    print()
    
    # Check prerequisites
    print_status("Checking prerequisites...")
    
    if not check_command("python3") and not check_command("python"):
        print_error("Python 3 is not installed")
        sys.exit(1)
    
    if not check_command("node"):
        print_error("Node.js is not installed")
        sys.exit(1)
    
    if not check_command("npm"):
        print_error("npm is not installed")
        sys.exit(1)
    
    # Check .env file
    if not (script_dir / ".env").exists():
        print_error(".env file not found. Please copy .env.example and configure it.")
        sys.exit(1)
    
    print_success("All prerequisites met")
    
    # Create log directory
    log_dir = script_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Start main email processor
    print_status("Starting email processor...")
    
    main_venv = setup_venv(script_dir, script_dir / "requirements.txt")
    main_python = get_python_executable(main_venv)
    
    with open(log_dir / "email_processor.log", "w") as log_file:
        process = subprocess.Popen(
            [str(main_python), "main.py"],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            cwd=script_dir
        )
        processes.append(process)
    
    print_success(f"Email processor started (PID: {process.pid})")
    
    # Start admin panel backend
    print_status("Starting admin panel backend...")
    
    backend_dir = script_dir / "admin_panel" / "backend"
    backend_venv = setup_venv(backend_dir, backend_dir / "requirements.txt")
    backend_python = get_python_executable(backend_venv)
    
    with open(log_dir / "admin_backend.log", "w") as log_file:
        process = subprocess.Popen(
            [str(backend_python), "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            cwd=backend_dir
        )
        processes.append(process)
    
    print_success(f"Admin backend starting (PID: {process.pid})")
    
    # Wait for backend
    if not wait_for_service("http://localhost:8000/health", "Admin Backend"):
        cleanup()
        sys.exit(1)
    
    # Start admin panel frontend
    print_status("Starting admin panel frontend...")
    
    frontend_dir = script_dir / "admin_panel" / "frontend"
    
    # Check node_modules
    if not (frontend_dir / "node_modules").exists():
        print_warning("Node modules not found. Installing dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
    
    with open(log_dir / "admin_frontend.log", "w") as log_file:
        process = subprocess.Popen(
            ["npm", "run", "dev", "--", "--host", "0.0.0.0"],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            cwd=frontend_dir
        )
        processes.append(process)
    
    print_success(f"Admin frontend starting (PID: {process.pid})")
    
    # Wait for frontend
    if not wait_for_service("http://localhost:5173", "Admin Frontend"):
        cleanup()
        sys.exit(1)
    
    # Print success message
    print()
    print(f"{GREEN}{'=' * 60}{NC}")
    print(f"{GREEN}Email Client CLI System is running!{NC}")
    print(f"{GREEN}{'=' * 60}{NC}")
    print()
    print("🚀 Services:")
    print("   📧 Email Processor: Running (checking every 5 minutes)")
    print("   🔧 Admin Backend:   http://localhost:8000 (API docs: http://localhost:8000/docs)")
    print("   🌐 Admin Frontend:  http://localhost:5173")
    print()
    print("📋 Default Login:")
    print("   Email:    admin@example.com")
    print("   Password: changeme")
    print()
    print("📁 Logs:")
    print(f"   Email Processor: {log_dir}/email_processor.log")
    print(f"   Admin Backend:   {log_dir}/admin_backend.log")
    print(f"   Admin Frontend:  {log_dir}/admin_frontend.log")
    print()
    print("Press Ctrl+C to stop all services")
    print()
    
    # Keep running
    try:
        while True:
            # Check if any process has died
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    print_error(f"Process {i} has stopped unexpectedly")
                    cleanup()
                    sys.exit(1)
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print_status("Received interrupt signal")

if __name__ == "__main__":
    main()