#!/usr/bin/env python3
"""Test script to verify PYTHONPATH is set correctly for imports."""

import sys
import os
from pathlib import Path

print("Testing PYTHONPATH configuration...")
print("=" * 60)

# Print current working directory
print(f"Current directory: {os.getcwd()}")
print()

# Print Python path
print("Python sys.path:")
for i, path in enumerate(sys.path):
    print(f"  {i}: {path}")
print()

# Print PYTHONPATH environment variable
pythonpath = os.environ.get('PYTHONPATH', 'NOT SET')
print(f"PYTHONPATH environment variable: {pythonpath}")
print()

# Test imports
print("Testing imports...")
try:
    from src.email_fetcher import EmailFetcher
    print("✓ Successfully imported EmailFetcher from src.email_fetcher")
except ImportError as e:
    print(f"✗ Failed to import EmailFetcher: {e}")

try:
    from src.order_tracker import OrderTracker
    print("✓ Successfully imported OrderTracker from src.order_tracker")
except ImportError as e:
    print(f"✗ Failed to import OrderTracker: {e}")

try:
    import database
    print("✓ Successfully imported database module")
except ImportError as e:
    print(f"✗ Failed to import database: {e}")

try:
    import auth
    print("✓ Successfully imported auth module")
except ImportError as e:
    print(f"✗ Failed to import auth: {e}")

print()
print("=" * 60)

# Check if we can find the src directory
root_dir = Path(__file__).parent.parent.parent
src_dir = root_dir / "src"
if src_dir.exists():
    print(f"✓ Found src directory at: {src_dir}")
else:
    print(f"✗ src directory not found at expected location: {src_dir}")