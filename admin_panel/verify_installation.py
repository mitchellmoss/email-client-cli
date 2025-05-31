#!/usr/bin/env python3
"""
Verify admin panel installation and dependencies.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version."""
    print("🐍 Python Version Check")
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 8:
        print(f"  ✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"  ❌ Python {python_version.major}.{python_version.minor}.{python_version.micro} (3.8+ required)")
        return False
    return True

def check_backend_dependencies():
    """Check backend dependencies."""
    print("\n📦 Backend Dependencies Check")
    backend_dir = Path(__file__).parent / "backend"
    
    if not (backend_dir / "requirements.txt").exists():
        print("  ❌ requirements.txt not found")
        return False
    
    # Check if venv exists
    venv_path = backend_dir / "venv"
    if venv_path.exists():
        print(f"  ✅ Virtual environment found at {venv_path}")
    else:
        print("  ⚠️  No virtual environment found (recommended)")
    
    # Check key packages
    try:
        import fastapi
        print("  ✅ FastAPI installed")
    except ImportError:
        print("  ❌ FastAPI not installed")
        return False
    
    try:
        import uvicorn
        print("  ✅ Uvicorn installed")
    except ImportError:
        print("  ❌ Uvicorn not installed")
        return False
    
    try:
        import jwt
        print("  ✅ PyJWT installed")
    except ImportError:
        print("  ❌ PyJWT not installed")
        return False
    
    return True

def check_frontend_dependencies():
    """Check frontend dependencies."""
    print("\n📦 Frontend Dependencies Check")
    frontend_dir = Path(__file__).parent / "frontend"
    
    if not (frontend_dir / "package.json").exists():
        print("  ❌ package.json not found")
        return False
    
    # Check if node_modules exists
    if (frontend_dir / "node_modules").exists():
        print("  ✅ node_modules found")
    else:
        print("  ❌ node_modules not found (run 'npm install')")
        return False
    
    # Check Node.js and npm
    try:
        node_version = subprocess.check_output(["node", "--version"], stderr=subprocess.DEVNULL).decode().strip()
        print(f"  ✅ Node.js {node_version}")
    except:
        print("  ❌ Node.js not found")
        return False
    
    try:
        npm_version = subprocess.check_output(["npm", "--version"], stderr=subprocess.DEVNULL).decode().strip()
        print(f"  ✅ npm {npm_version}")
    except:
        print("  ❌ npm not found")
        return False
    
    return True

def check_database():
    """Check database access."""
    print("\n🗄️  Database Check")
    db_path = Path(__file__).parent.parent / "order_tracking.db"
    
    if db_path.exists():
        print(f"  ✅ Database found at {db_path}")
        
        # Check if we can read it
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sent_orders")
            count = cursor.fetchone()[0]
            conn.close()
            print(f"  ✅ Database accessible ({count} orders)")
        except Exception as e:
            print(f"  ❌ Database error: {e}")
            return False
    else:
        print(f"  ❌ Database not found at {db_path}")
        return False
    
    return True

def check_environment():
    """Check environment variables."""
    print("\n🔧 Environment Variables Check")
    
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        print(f"  ✅ .env file found")
        
        # Check required vars
        from dotenv import load_dotenv
        load_dotenv(env_file)
        
        required_vars = [
            "IMAP_SERVER",
            "EMAIL_ADDRESS", 
            "EMAIL_PASSWORD",
            "ANTHROPIC_API_KEY",
            "SMTP_SERVER",
            "SMTP_USERNAME",
            "SMTP_PASSWORD",
            "CS_EMAIL"
        ]
        
        missing = []
        for var in required_vars:
            if os.getenv(var):
                print(f"  ✅ {var} is set")
            else:
                print(f"  ❌ {var} is not set")
                missing.append(var)
        
        if missing:
            return False
    else:
        print("  ❌ .env file not found")
        return False
    
    return True

def check_file_structure():
    """Check required files exist."""
    print("\n📂 File Structure Check")
    
    base_dir = Path(__file__).parent
    required_files = [
        "backend/main.py",
        "backend/models/__init__.py",
        "backend/database.py",
        "backend/auth.py",
        "backend/run_dev.sh",
        "frontend/src/App.tsx",
        "frontend/src/main.tsx",
        "frontend/index.html",
        "frontend/vite.config.ts"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def print_setup_instructions():
    """Print setup instructions."""
    print("\n📋 Setup Instructions")
    print("1. Backend setup:")
    print("   cd admin_panel/backend")
    print("   python -m venv venv")
    print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
    print("   pip install -r requirements.txt")
    print("   ./run_dev.sh")
    print()
    print("2. Frontend setup (new terminal):")
    print("   cd admin_panel/frontend")
    print("   npm install")
    print("   npm run dev")
    print()
    print("3. Access admin panel:")
    print("   http://localhost:5173")
    print("   Login: admin@example.com / changeme")

def main():
    """Run all checks."""
    print("🔍 Admin Panel Installation Verification")
    print("=" * 50)
    
    checks = [
        check_python_version(),
        check_file_structure(),
        check_backend_dependencies(),
        check_frontend_dependencies(),
        check_database(),
        check_environment()
    ]
    
    if all(checks):
        print("\n✅ All checks passed! Admin panel is ready to use.")
        print("\nTo start the admin panel:")
        print("1. Backend: cd admin_panel/backend && ./run_dev.sh")
        print("2. Frontend: cd admin_panel/frontend && npm run dev")
        print("3. Open: http://localhost:5173")
    else:
        print("\n❌ Some checks failed. Please follow the setup instructions above.")
        print_setup_instructions()

if __name__ == "__main__":
    main()