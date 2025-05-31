#!/usr/bin/env python3
"""Simple script to test the API endpoints."""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def test_api():
    """Test basic API functionality."""
    
    print("Testing Email Order Admin Panel API")
    print("=" * 50)
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    # Test login
    print("\n2. Testing login...")
    login_data = {
        "username": "admin@example.com",
        "password": "changeme"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            data=login_data
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data["access_token"]
            print(f"   Token received: {token[:20]}...")
            
            # Set up headers for authenticated requests
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test authenticated endpoints
            print("\n3. Testing authenticated endpoints...")
            
            # Get current user
            print("\n   a. Current user:")
            response = requests.get(f"{BASE_URL}{API_PREFIX}/auth/me", headers=headers)
            print(f"      Status: {response.status_code}")
            print(f"      User: {response.json()}")
            
            # Get orders
            print("\n   b. Orders:")
            response = requests.get(f"{BASE_URL}{API_PREFIX}/orders", headers=headers)
            print(f"      Status: {response.status_code}")
            orders = response.json()
            print(f"      Found {len(orders)} orders")
            if orders:
                print(f"      Latest order: {orders[0].get('order_id', 'N/A')}")
            
            # Get order stats
            print("\n   c. Order statistics:")
            response = requests.get(f"{BASE_URL}{API_PREFIX}/orders/stats", headers=headers)
            print(f"      Status: {response.status_code}")
            stats = response.json()
            print(f"      Total orders (7d): {stats.get('total_orders_sent', 0)}")
            print(f"      Duplicates blocked: {stats.get('duplicate_attempts_blocked', 0)}")
            
            # Get system status
            print("\n   d. System status:")
            response = requests.get(f"{BASE_URL}{API_PREFIX}/system/status", headers=headers)
            print(f"      Status: {response.status_code}")
            status = response.json()
            print(f"      Email processor running: {status.get('is_running', False)}")
            
            # Get email config (without passwords)
            print("\n   e. Email configuration:")
            response = requests.get(f"{BASE_URL}{API_PREFIX}/email-config", headers=headers)
            print(f"      Status: {response.status_code}")
            config = response.json()
            print(f"      IMAP server: {config.get('imap', {}).get('server', 'Not configured')}")
            print(f"      CS Email: {config.get('recipients', {}).get('cs_email', 'Not configured')}")
            
        else:
            print(f"   Login failed: {response.json()}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 50)
    print("API test completed!")


if __name__ == "__main__":
    print("Make sure the API server is running on http://localhost:8000")
    print("Run ./run_dev.sh in the backend directory first\n")
    
    input("Press Enter to start testing...")
    test_api()