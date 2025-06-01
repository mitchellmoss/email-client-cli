#!/usr/bin/env python3
"""
Alternative backend startup script with better error handling
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    # Get the current directory
    backend_dir = Path(__file__).parent
    project_root = backend_dir.parent.parent
    
    # Check if virtual environment exists
    venv_path = backend_dir / "venv"
    if not venv_path.exists():
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
    
    # Determine the python executable in venv
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    
    # Install requirements
    print("Installing dependencies...")
    requirements_file = backend_dir / "requirements.txt"
    subprocess.run([str(pip_exe), "install", "-r", str(requirements_file)], check=True)
    
    # Install psutil
    subprocess.run([str(pip_exe), "install", "psutil"], check=True)
    
    # Set environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{backend_dir}:{project_root}:{env.get('PYTHONPATH', '')}"
    
    # Run the development server
    print("Starting FastAPI development server...")
    os.chdir(backend_dir)
    
    cmd = [
        str(python_exe),
        "-m", "uvicorn",
        "main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ]
    
    subprocess.run(cmd, env=env)

if __name__ == "__main__":
    main()