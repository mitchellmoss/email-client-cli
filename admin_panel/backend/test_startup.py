#!/usr/bin/env python3
"""
Comprehensive startup tests for the admin panel backend.
Run this to diagnose startup issues.
"""

import time
import sys
import os
import traceback
from pathlib import Path
import subprocess
import psutil
import tempfile
import sqlite3
from contextlib import contextmanager

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

class StartupTester:
    def __init__(self):
        self.results = []
        self.test_db_path = None
        
    def log(self, test_name: str, success: bool, message: str = "", duration: float = 0):
        """Log test result."""
        status = "✓ PASS" if success else "✗ FAIL"
        duration_str = f" ({duration:.3f}s)" if duration > 0 else ""
        self.results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'duration': duration
        })
        print(f"{status} {test_name}{duration_str}")
        if message:
            print(f"    {message}")
    
    def test_basic_imports(self):
        """Test individual module imports to isolate problems."""
        modules_to_test = [
            "fastapi",
            "sqlalchemy", 
            "pydantic",
            "uvicorn",
            "psutil",
            "python_jose",
            "passlib"
        ]
        
        for module in modules_to_test:
            start = time.time()
            try:
                __import__(module)
                self.log(f"Import {module}", True, duration=time.time() - start)
            except Exception as e:
                self.log(f"Import {module}", False, str(e), time.time() - start)
    
    def test_config_loading(self):
        """Test configuration loading."""
        start = time.time()
        try:
            from config import settings
            self.log("Config loading", True, f"Database URL: {settings.database_url}", time.time() - start)
        except Exception as e:
            self.log("Config loading", False, str(e), time.time() - start)
    
    def test_database_connection(self):
        """Test database connection and operations."""
        start = time.time()
        try:
            # Test with a temporary database to avoid interfering with real one
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                self.test_db_path = f.name
            
            # Test raw SQLite connection
            conn = sqlite3.connect(self.test_db_path)
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
            conn.close()
            
            # Test SQLAlchemy connection
            from sqlalchemy import create_engine
            test_engine = create_engine(f"sqlite:///{self.test_db_path}")
            with test_engine.connect() as conn:
                result = conn.execute("SELECT 1").fetchone()
                assert result[0] == 1
            
            self.log("Database connection", True, duration=time.time() - start)
        except Exception as e:
            self.log("Database connection", False, str(e), time.time() - start)
    
    def test_database_reflection(self):
        """Test the metadata reflection that might be causing slowdowns."""
        start = time.time()
        try:
            from sqlalchemy import create_engine, MetaData
            
            # Use the main database file
            from config import settings
            engine = create_engine(settings.database_url)
            
            metadata = MetaData()
            metadata.reflect(bind=engine)
            
            table_count = len(metadata.tables)
            self.log("Database reflection", True, f"Found {table_count} tables", time.time() - start)
            
            if time.time() - start > 5:
                self.log("Database reflection slow", False, f"Reflection took {time.time() - start:.1f}s - this is likely the issue!")
                
        except Exception as e:
            self.log("Database reflection", False, str(e), time.time() - start)
    
    def test_model_imports(self):
        """Test model imports."""
        models_to_test = [
            "models.user",
            "models.product", 
        ]
        
        for model in models_to_test:
            start = time.time()
            try:
                __import__(model)
                self.log(f"Import {model}", True, duration=time.time() - start)
            except Exception as e:
                self.log(f"Import {model}", False, str(e), time.time() - start)
    
    def test_api_imports(self):
        """Test API router imports."""
        apis_to_test = [
            "api.auth",
            "api.orders",
            "api.products", 
            "api.email_config",
            "api.analytics",
            "api.system"
        ]
        
        for api in apis_to_test:
            start = time.time()
            try:
                __import__(api)
                self.log(f"Import {api}", True, duration=time.time() - start)
            except Exception as e:
                self.log(f"Import {api}", False, str(e), time.time() - start)
    
    def test_fastapi_app_creation(self):
        """Test FastAPI app creation without lifespan."""
        start = time.time()
        try:
            from fastapi import FastAPI
            from config import settings
            
            # Create minimal app without lifespan
            app = FastAPI(title=settings.api_title)
            self.log("FastAPI app creation", True, duration=time.time() - start)
        except Exception as e:
            self.log("FastAPI app creation", False, str(e), time.time() - start)
    
    def test_full_app_import(self):
        """Test importing the full main app."""
        start = time.time()
        try:
            # This will trigger all the startup code
            import main
            self.log("Full app import", True, duration=time.time() - start)
            
            if time.time() - start > 10:
                self.log("Full app import slow", False, f"Import took {time.time() - start:.1f}s - startup issue confirmed!")
                
        except Exception as e:
            self.log("Full app import", False, str(e), time.time() - start)
    
    def test_psutil_operations(self):
        """Test psutil operations that might be slow."""
        start = time.time()
        try:
            import psutil
            
            # Test process iteration (used in system.py)
            process_count = 0
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                process_count += 1
                if process_count > 100:  # Limit iteration
                    break
            
            self.log("psutil process iteration", True, f"Checked {process_count} processes", time.time() - start)
            
            if time.time() - start > 3:
                self.log("psutil slow", False, f"Process iteration took {time.time() - start:.1f}s")
                
        except Exception as e:
            self.log("psutil operations", False, str(e), time.time() - start)
    
    def test_directory_access(self):
        """Test file system access that might be slow."""
        start = time.time()
        try:
            from config import settings
            
            # Test project root access
            project_root = settings.project_root
            if project_root.exists():
                file_count = len(list(project_root.rglob("*")))
                self.log("Directory access", True, f"Found {file_count} files/dirs", time.time() - start)
            else:
                self.log("Directory access", False, f"Project root not found: {project_root}")
                
        except Exception as e:
            self.log("Directory access", False, str(e), time.time() - start)
    
    def test_subprocess_operations(self):
        """Test subprocess operations that might hang."""
        start = time.time()
        try:
            # Test a simple subprocess call
            result = subprocess.run(
                ["python", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            self.log("Subprocess operations", True, f"Exit code: {result.returncode}", time.time() - start)
        except Exception as e:
            self.log("Subprocess operations", False, str(e), time.time() - start)
    
    def cleanup(self):
        """Clean up test resources."""
        if self.test_db_path and os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
    
    def run_all_tests(self):
        """Run all startup tests."""
        print("🧪 Running backend startup diagnostic tests...\n")
        
        try:
            self.test_basic_imports()
            print()
            self.test_config_loading()
            print()
            self.test_database_connection()
            self.test_database_reflection()
            print()
            self.test_model_imports()
            print()
            self.test_api_imports()
            print()
            self.test_fastapi_app_creation()
            print()
            self.test_psutil_operations()
            print()
            self.test_directory_access()
            print()
            self.test_subprocess_operations()
            print()
            self.test_full_app_import()
            
        finally:
            self.cleanup()
        
        # Summary
        print("\n" + "="*60)
        print("DIAGNOSTIC SUMMARY")
        print("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        # Check for slow operations
        slow_tests = [r for r in self.results if r['duration'] > 2]
        if slow_tests:
            print("\n🐌 SLOW OPERATIONS (>2s):")
            for result in slow_tests:
                print(f"  - {result['test']}: {result['duration']:.1f}s")
        
        print("\n💡 RECOMMENDATIONS:")
        if any("reflection" in r['test'] and r['duration'] > 3 for r in self.results):
            print("  - Database reflection is slow - consider lazy loading")
        if any("psutil" in r['test'] and r['duration'] > 2 for r in self.results):
            print("  - psutil operations are slow - consider caching")
        if any("import" in r['test'] and not r['success'] for r in self.results):
            print("  - Missing dependencies - check requirements.txt")


if __name__ == "__main__":
    tester = StartupTester()
    tester.run_all_tests()