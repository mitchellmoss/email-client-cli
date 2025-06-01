"""System control endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import subprocess
import psutil
import os
from datetime import datetime
from pathlib import Path

from auth import get_current_active_user
from models.user import User
from config import settings

router = APIRouter()

# Global state for tracking system status
system_state = {
    "is_running": False,
    "last_check": None,
    "process_pid": None
}


@router.get("/status")
async def get_system_status(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get current system status."""
    # Check if main.py process is running
    is_running = False
    process_info = None
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline and 'main.py' in ' '.join(cmdline):
                # Check if process is running in our project directory
                try:
                    process = psutil.Process(proc.info['pid'])
                    if 'email-client-cli' in process.cwd():
                        is_running = True
                        process_info = {
                            "pid": proc.info['pid'],
                            "cpu_percent": proc.cpu_percent(),
                            "memory_mb": proc.memory_info().rss / 1024 / 1024
                        }
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Read last lines from log file
    log_file = settings.project_root / "email_processor.log"
    last_logs = []
    if log_file.exists():
        with open(log_file, 'r') as f:
            last_logs = f.readlines()[-10:]  # Last 10 lines
    
    return {
        "is_running": is_running,
        "process_info": process_info,
        "last_check": datetime.now().isoformat(),
        "last_logs": last_logs,
        "config_path": str(settings.email_processor_config),
        "log_path": str(log_file)
    }


@router.post("/start")
async def start_system(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """Start the email processing system."""
    # Check if already running
    status = await get_system_status(current_user)
    if status["is_running"]:
        raise HTTPException(status_code=400, detail="System is already running")
    
    try:
        # Start the main.py process
        main_py_path = settings.project_root / "main.py"
        process = subprocess.Popen(
            ["python", str(main_py_path)],
            cwd=str(settings.project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        return {
            "message": "System started successfully",
            "pid": str(process.pid)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start system: {str(e)}")


@router.post("/stop")
async def stop_system(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """Stop the email processing system."""
    status = await get_system_status(current_user)
    if not status["is_running"]:
        raise HTTPException(status_code=400, detail="System is not running")
    
    try:
        # Find and terminate the process
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'main.py' in ' '.join(cmdline):
                    # Check if process is running in our project directory
                    try:
                        process = psutil.Process(proc.info['pid'])
                        if 'email-client-cli' in process.cwd():
                            proc.terminate()
                            proc.wait(timeout=5)  # Wait up to 5 seconds
                            return {"message": "System stopped successfully"}
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        raise HTTPException(status_code=404, detail="Process not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop system: {str(e)}")


@router.post("/restart")
async def restart_system(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """Restart the email processing system."""
    # Stop if running
    status = await get_system_status(current_user)
    if status["is_running"]:
        await stop_system(current_user)
    
    # Wait a moment
    import time
    time.sleep(2)
    
    # Start again
    return await start_system(current_user)


@router.get("/logs")
async def get_system_logs(
    lines: int = 100,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get system logs."""
    log_file = settings.project_root / "email_processor.log"
    
    if not log_file.exists():
        return {"logs": [], "total_lines": 0}
    
    try:
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            total_lines = len(all_lines)
            logs = all_lines[-lines:] if lines < total_lines else all_lines
        
        return {
            "logs": logs,
            "total_lines": total_lines,
            "requested_lines": lines
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {str(e)}")


@router.delete("/logs")
async def clear_logs(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """Clear system logs."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    log_file = settings.project_root / "email_processor.log"
    
    try:
        if log_file.exists():
            # Create backup
            backup_file = log_file.with_suffix('.log.bak')
            log_file.rename(backup_file)
            
            # Create empty log file
            log_file.touch()
            
        return {"message": "Logs cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear logs: {str(e)}")