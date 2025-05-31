#!/usr/bin/env python3
"""
Quick connection and health tests for the backend.
"""

import requests
import time
import subprocess
import signal
import os
import sys
from pathlib import Path

def test_health_endpoint():
    """Test if the backend health endpoint responds."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✓ Backend health endpoint responding")
            return True
        else:
            print(f"✗ Backend health endpoint returned {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Backend not responding (connection refused)")
        return False
    except requests.exceptions.Timeout:
        print("✗ Backend health check timed out")
        return False
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_root_endpoint():
    """Test root endpoint."""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Root endpoint responding: {data.get('message', 'No message')}")
            return True
        else:
            print(f"✗ Root endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}")
        return False

def start_backend_with_timeout():
    """Start backend and wait for it to respond or timeout."""
    print("🚀 Starting backend with timeout monitoring...")
    
    backend_dir = Path(__file__).parent
    
    # Start uvicorn process
    process = subprocess.Popen(
        ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid if hasattr(os, 'setsid') else None
    )
    
    print(f"Backend process started (PID: {process.pid})")
    
    # Wait for startup with timeout
    timeout = 30  # 30 seconds
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if process.poll() is not None:
            # Process has terminated
            stdout, stderr = process.communicate()
            print(f"❌ Backend process terminated early")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return False
        
        if test_health_endpoint():
            print(f"✅ Backend started successfully in {time.time() - start_time:.1f} seconds")
            
            # Test a few endpoints
            test_root_endpoint()
            
            # Cleanup
            try:
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                process.wait(timeout=5)
                print("✓ Backend stopped cleanly")
            except:
                print("⚠ Backend force killed")
            
            return True
        
        time.sleep(1)
        print(f"⏳ Waiting for backend... ({int(time.time() - start_time)}s)")
    
    # Timeout reached
    print(f"❌ Backend startup timed out after {timeout} seconds")
    
    # Get process output
    try:
        stdout, stderr = process.communicate(timeout=1)
        print(f"STDOUT: {stdout.decode()}")
        print(f"STDERR: {stderr.decode()}")
    except:
        print("Could not retrieve process output")
    
    # Kill process
    try:
        if hasattr(os, 'killpg'):
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=5)
    except:
        try:
            process.kill()
        except:
            pass
    
    return False

if __name__ == "__main__":
    print("🧪 Quick backend startup test\n")
    
    # Check if backend is already running
    if test_health_endpoint():
        print("✅ Backend is already running and healthy!")
        test_root_endpoint()
    else:
        # Start backend and test
        success = start_backend_with_timeout()
        if not success:
            print("\n💡 Backend startup failed or timed out.")
            print("Run 'python test_startup.py' for detailed diagnostics.")
            sys.exit(1)
        else:
            print("\n✅ Backend startup test passed!")