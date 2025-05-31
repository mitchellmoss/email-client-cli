@echo off
REM Email Client CLI - Complete System Startup Script for Windows
REM This script starts all components: main processor, admin backend, and admin frontend

setlocal enabledelayedexpansion

REM Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Colors (Windows 10+ only)
echo.
echo =====================================
echo Email Client CLI - Starting All Services
echo =====================================
echo.

REM Check prerequisites
echo Checking prerequisites...

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: npm is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found. Please copy .env.example and configure it.
    pause
    exit /b 1
)

echo All prerequisites met!
echo.

REM Create log directory
if not exist "logs" mkdir "logs"

REM Start main email processor
echo Starting email processor...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment for main app...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Start main.py in new window
start "Email Processor" /min cmd /c "python main.py > logs\email_processor.log 2>&1"
echo Email processor started

REM Start admin panel backend
echo Starting admin panel backend...
cd "%SCRIPT_DIR%\admin_panel\backend"

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment for backend...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Start FastAPI backend in new window
start "Admin Backend" /min cmd /c "uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ..\..\logs\admin_backend.log 2>&1"
echo Admin backend started

REM Wait a moment for backend to start
timeout /t 5 /nobreak >nul

REM Start admin panel frontend
echo Starting admin panel frontend...
cd "%SCRIPT_DIR%\admin_panel\frontend"

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

REM Start Vite dev server in new window
start "Admin Frontend" /min cmd /c "npm run dev -- --host 0.0.0.0 > ..\..\logs\admin_frontend.log 2>&1"
echo Admin frontend started

REM Wait for services to fully start
timeout /t 5 /nobreak >nul

REM Print success message
cls
echo.
echo ============================================================
echo Email Client CLI System is running!
echo ============================================================
echo.
echo Services:
echo    Email Processor: Running (checking every 5 minutes)
echo    Admin Backend:   http://localhost:8000 (API docs: http://localhost:8000/docs)
echo    Admin Frontend:  http://localhost:5173
echo.
echo Default Login:
echo    Email:    admin@example.com
echo    Password: changeme
echo.
echo Logs:
echo    Email Processor: %SCRIPT_DIR%logs\email_processor.log
echo    Admin Backend:   %SCRIPT_DIR%logs\admin_backend.log  
echo    Admin Frontend:  %SCRIPT_DIR%logs\admin_frontend.log
echo.
echo To stop all services, close this window and all service windows
echo.
pause