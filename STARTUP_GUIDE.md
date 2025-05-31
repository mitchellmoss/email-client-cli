# Email Client CLI - Startup Guide

This guide explains how to start and stop all components of the Email Client CLI system with a single command.

## 🚀 Quick Start

### Option 1: Shell Script (Mac/Linux)
```bash
./start_all.sh
```

### Option 2: Python Script (Cross-platform)
```bash
python start_all.py
```

### Option 3: Batch Script (Windows)
```cmd
start_all.bat
```

## 📋 What Gets Started

The startup scripts launch three components:

1. **Email Processor** (`main.py`)
   - Monitors emails from Tile Pro Depot
   - Processes orders every 5 minutes
   - Runs in the background

2. **Admin Backend** (FastAPI)
   - REST API server on http://localhost:8000
   - Handles authentication and data management
   - API documentation at http://localhost:8000/docs

3. **Admin Frontend** (React)
   - Web interface on http://localhost:5173
   - Default login: `admin@example.com` / `changeme`
   - Real-time monitoring dashboard

## 🛑 Stopping All Services

### Mac/Linux
```bash
./stop_all.sh
# or press Ctrl+C in the terminal running start_all.sh
```

### All Platforms
```bash
# Press Ctrl+C in the terminal running the start script
```

### Windows
Close all command windows or press Ctrl+C in each window

## 📁 Log Files

All services write logs to the `logs/` directory:
- `logs/email_processor.log` - Main email processing
- `logs/admin_backend.log` - API server logs
- `logs/admin_frontend.log` - Frontend dev server logs

## 🔧 Prerequisites

Before running the startup scripts, ensure you have:

1. **Python 3.8+** installed
2. **Node.js 14+** and **npm** installed
3. **`.env` file** configured (copy from `.env.example`)
4. **Virtual environments** will be created automatically

## 🐛 Troubleshooting

### "Permission denied" error
```bash
chmod +x start_all.sh stop_all.sh start_all.py
```

### Port already in use
```bash
# Check what's using the ports
lsof -i :8000  # Backend port
lsof -i :5173  # Frontend port

# Kill the processes
kill -9 <PID>
```

### Services not starting
1. Check the log files in `logs/` directory
2. Ensure all prerequisites are installed
3. Verify `.env` file is properly configured
4. Try starting services individually:
   ```bash
   # Email processor
   python main.py
   
   # Admin backend
   cd admin_panel/backend
   ./run_dev.sh
   
   # Admin frontend
   cd admin_panel/frontend
   npm run dev
   ```

### Virtual environment issues
```bash
# Remove and recreate virtual environments
rm -rf venv admin_panel/backend/venv
# Then run the start script again
```

## 🎯 Features of the Startup Scripts

- **Automatic dependency installation**: Creates virtual environments and installs packages
- **Health checks**: Waits for services to be ready before proceeding
- **Colored output**: Clear status messages
- **Log management**: All output redirected to log files
- **Graceful shutdown**: Stops all services when interrupted
- **Cross-platform**: Works on Mac, Linux, and Windows

## 💡 Tips

1. **First run**: The first run may take longer as it installs dependencies
2. **Background mode**: Services run in the background, check logs for output
3. **Development**: The scripts use development servers with hot-reload enabled
4. **Production**: For production, use proper process managers (systemd, PM2, etc.)

## 📊 Monitoring

Once started, you can:
1. Open http://localhost:5173 for the admin panel
2. View real-time logs: `tail -f logs/*.log`
3. Check API docs: http://localhost:8000/docs
4. Monitor system status in the admin dashboard

## 🔒 Security Note

The default login credentials are for development only. In production:
1. Change the default password immediately
2. Use strong passwords
3. Enable HTTPS
4. Restrict access to trusted networks