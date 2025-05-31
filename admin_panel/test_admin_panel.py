#!/usr/bin/env python3
"""
Test script to verify admin panel setup and functionality.
Run this after starting both backend and frontend servers.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"
DEFAULT_EMAIL = "admin@example.com"
DEFAULT_PASSWORD = "changeme"

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*50}")
    print(f"{title:^50}")
    print(f"{'='*50}")

def test_health():
    """Test health check endpoint."""
    print_section("Testing Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✓ Health check passed")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Health check failed with status {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Failed to connect to backend: {e}")
        return False

def test_login():
    """Test login and get authentication token."""
    print_section("Testing Authentication")
    try:
        # Test login
        login_data = {
            "username": DEFAULT_EMAIL,
            "password": DEFAULT_PASSWORD
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            data=login_data
        )
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            print("✓ Login successful")
            print(f"  Token type: {token_data.get('token_type')}")
            print(f"  Token: {token[:20]}...")
            
            # Test getting current user
            headers = {"Authorization": f"Bearer {token}"}
            user_response = requests.get(
                f"{BASE_URL}{API_PREFIX}/auth/me",
                headers=headers
            )
            
            if user_response.status_code == 200:
                user_data = user_response.json()
                print("✓ User info retrieved")
                print(f"  Email: {user_data.get('email')}")
                print(f"  Is Superuser: {user_data.get('is_superuser')}")
            
            return token
        else:
            print(f"✗ Login failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Authentication test failed: {e}")
        return None

def test_orders(token):
    """Test order endpoints."""
    print_section("Testing Order Management")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Get order stats
        stats_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/orders/stats",
            headers=headers
        )
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print("✓ Order statistics retrieved")
            print(f"  Total orders (7d): {stats.get('total_orders_sent', 0)}")
            print(f"  Duplicates blocked: {stats.get('duplicate_attempts_blocked', 0)}")
            
            if stats.get('daily_counts'):
                print("  Daily counts:")
                for day in stats['daily_counts'][-3:]:  # Last 3 days
                    print(f"    {day['date']}: {day['count']} orders")
        
        # Get order list
        orders_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/orders?limit=5",
            headers=headers
        )
        
        if orders_response.status_code == 200:
            orders = orders_response.json()
            print(f"\n✓ Order list retrieved ({len(orders)} orders)")
            for order in orders[:3]:  # Show first 3
                print(f"  - Order #{order.get('order_id')}: {order.get('customer_name')} "
                      f"({order.get('status')}) - {order.get('sent_at')}")
        
    except Exception as e:
        print(f"✗ Order test failed: {e}")

def test_system_status(token):
    """Test system status endpoint."""
    print_section("Testing System Status")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/system/status",
            headers=headers
        )
        
        if response.status_code == 200:
            status = response.json()
            print("✓ System status retrieved")
            print(f"  Running: {status.get('is_running', False)}")
            print(f"  PID: {status.get('pid', 'N/A')}")
            print(f"  Last check: {status.get('last_check', 'Never')}")
            print(f"  Uptime: {status.get('uptime', 'N/A')}")
            
            if status.get('last_logs'):
                print("\n  Recent logs:")
                for log in status['last_logs'][-3:]:
                    print(f"    {log.strip()}")
        else:
            print(f"✗ System status failed with status {response.status_code}")
    except Exception as e:
        print(f"✗ System status test failed: {e}")

def test_email_config(token):
    """Test email configuration endpoint."""
    print_section("Testing Email Configuration")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/email-config",
            headers=headers
        )
        
        if response.status_code == 200:
            config = response.json()
            print("✓ Email configuration retrieved")
            print(f"  IMAP Server: {config.get('imap_server', 'Not set')}")
            print(f"  SMTP Server: {config.get('smtp_server', 'Not set')}")
            print(f"  Check interval: {config.get('check_interval_minutes', 5)} minutes")
            print(f"  CS Email: {config.get('cs_email', 'Not set')}")
            print(f"  Laticrete CS Email: {config.get('laticrete_cs_email', 'Not set')}")
        else:
            print(f"✗ Email config failed with status {response.status_code}")
    except Exception as e:
        print(f"✗ Email config test failed: {e}")

def test_product_mappings(token):
    """Test product mapping endpoints."""
    print_section("Testing Product Mappings")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/products/mappings",
            headers=headers
        )
        
        if response.status_code == 200:
            mappings = response.json()
            print(f"✓ Product mappings retrieved ({len(mappings)} mappings)")
            for mapping in mappings[:3]:  # Show first 3
                print(f"  - {mapping.get('product_name')} → "
                      f"{mapping.get('matched_sku')} (${mapping.get('matched_price', 0):.2f})")
        else:
            print(f"✗ Product mappings failed with status {response.status_code}")
    except Exception as e:
        print(f"✗ Product mappings test failed: {e}")

def main():
    """Run all tests."""
    print(f"\nEmail Client CLI Admin Panel Test")
    print(f"Testing backend at: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test health check
    if not test_health():
        print("\n❌ Backend is not running. Please start it with:")
        print("   cd admin_panel/backend")
        print("   ./run_dev.sh")
        return
    
    # Test authentication
    token = test_login()
    if not token:
        print("\n❌ Authentication failed. Cannot proceed with other tests.")
        return
    
    # Test other endpoints
    test_orders(token)
    test_system_status(token)
    test_email_config(token)
    test_product_mappings(token)
    
    print_section("Test Summary")
    print("✓ All basic tests completed!")
    print("\nNext steps:")
    print("1. Start the frontend: cd admin_panel/frontend && npm run dev")
    print("2. Open http://localhost:5173 in your browser")
    print("3. Login with admin@example.com / changeme")
    print("4. Change the default password in Settings")

if __name__ == "__main__":
    main()