#!/usr/bin/env python3
"""Test script for order update functionality."""

import requests
import json
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

# Test credentials
TEST_EMAIL = "admin@example.com"
TEST_PASSWORD = "changeme"

def login():
    """Login and get access token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_update_order(token, order_id):
    """Test updating an order."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Update simple fields
    print("\n=== Test 1: Update simple fields ===")
    update_data = {
        "email_subject": "Updated Order Subject",
        "customer_name": "Updated Customer Name",
        "order_total": "$999.99"
    }
    
    response = requests.patch(
        f"{BASE_URL}/orders/{order_id}",
        headers=headers,
        json=update_data
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Success! Updated order:")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.text}")
    
    # Test 2: Update with products
    print("\n=== Test 2: Update tileware_products ===")
    update_data = {
        "tileware_products": [
            {
                "name": "Updated Product 1",
                "sku": "UPD-001",
                "quantity": 5,
                "price": "$50.00"
            },
            {
                "name": "Updated Product 2",
                "sku": "UPD-002",
                "quantity": 3,
                "price": "$75.00"
            }
        ]
    }
    
    response = requests.patch(
        f"{BASE_URL}/orders/{order_id}",
        headers=headers,
        json=update_data
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Success! Products updated")
    else:
        print(f"Error: {response.text}")
    
    # Test 3: Test duplicate order_id validation
    print("\n=== Test 3: Test duplicate order_id validation ===")
    update_data = {
        "order_id": "43058"  # Try to change to an existing order ID
    }
    
    response = requests.patch(
        f"{BASE_URL}/orders/{order_id}",
        headers=headers,
        json=update_data
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 400:
        print("Good! Duplicate validation working")
        print(f"Error message: {response.json()['detail']}")
    else:
        print("Warning: Duplicate validation may not be working correctly")
    
    # Test 4: Check audit log
    print("\n=== Test 4: Check audit log ===")
    response = requests.get(
        f"{BASE_URL}/orders/{order_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        order = response.json()
        print(f"Order history entries: {len(order.get('history', []))}")
        for entry in order.get('history', [])[-3:]:  # Show last 3 entries
            print(f"- {entry['timestamp']}: {entry['action']} - {entry.get('details', '')[:100]}...")

def main():
    """Main test function."""
    print("Testing Order Update Functionality")
    print("==================================")
    
    # Login
    token = login()
    if not token:
        print("Failed to login")
        return
    
    print("Login successful!")
    
    # Get a test order ID (use the first order in the list)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/orders?limit=1", headers=headers)
    
    if response.status_code == 200 and response.json():
        order_id = response.json()[0]["order_id"]
        print(f"Using order ID: {order_id}")
        
        # Run tests
        test_update_order(token, order_id)
    else:
        print("No orders found to test with")

if __name__ == "__main__":
    main()