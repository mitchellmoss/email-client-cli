#!/usr/bin/env python3
"""
Test script for order tracking functionality.
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.order_tracker import OrderTracker
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def test_order_tracking():
    """Test various order tracking functionalities."""
    print("=== Testing Order Tracking System ===\n")
    
    # Initialize tracker with test database
    tracker = OrderTracker(db_path="test_order_tracking.db")
    
    # Test 1: Check if a non-existent order has been sent
    print("Test 1: Checking non-existent order...")
    order_id = "TEST-12345"
    if not tracker.has_order_been_sent(order_id):
        print("✓ Correctly identified that order TEST-12345 has not been sent\n")
    else:
        print("✗ Error: Order should not exist\n")
    
    # Test 2: Mark an order as sent
    print("Test 2: Marking order as sent...")
    test_order = {
        'order_id': 'TEST-12345',
        'email_subject': 'New customer order #TEST-12345',
        'email_date': datetime.now().isoformat(),
        'customer_name': 'Test Customer',
        'total': '$299.99',
        'recipient_email': 'cs@example.com',
        'tileware_products': [
            {
                'name': 'TileWare Test Product',
                'sku': 'TEST-SKU-001',
                'quantity': 2,
                'price': '$149.99'
            }
        ],
        'shipping_address': {
            'name': 'Test Customer',
            'street': '123 Test Street',
            'city': 'Test City',
            'state': 'TS',
            'zip': '12345'
        }
    }
    
    if tracker.mark_order_as_sent(test_order):
        print("✓ Successfully marked order as sent\n")
    else:
        print("✗ Failed to mark order as sent\n")
    
    # Test 3: Check if the order is now marked as sent
    print("Test 3: Verifying order is marked as sent...")
    if tracker.has_order_been_sent(order_id):
        print("✓ Order correctly identified as already sent\n")
    else:
        print("✗ Error: Order should be marked as sent\n")
    
    # Test 4: Try to mark the same order again (should fail)
    print("Test 4: Testing duplicate prevention...")
    if not tracker.mark_order_as_sent(test_order):
        print("✓ Correctly prevented duplicate order entry\n")
    else:
        print("✗ Error: Should not allow duplicate order\n")
    
    # Test 5: Retrieve order details
    print("Test 5: Retrieving order details...")
    order_details = tracker.get_order_details(order_id)
    if order_details:
        print("✓ Successfully retrieved order details")
        print(f"  Customer: {order_details.get('customer_name')}")
        print(f"  Total: {order_details.get('total_amount')}")
        print(f"  Sent to: {order_details.get('recipient_email')}\n")
    else:
        print("✗ Failed to retrieve order details\n")
    
    # Test 6: Get statistics
    print("Test 6: Getting statistics...")
    stats = tracker.get_statistics()
    print(f"✓ Statistics retrieved:")
    print(f"  Total orders: {stats.get('total_orders', 0)}")
    print(f"  Orders today: {stats.get('orders_today', 0)}")
    print(f"  Orders this week: {stats.get('orders_this_week', 0)}\n")
    
    # Test 7: Add another order for listing test
    print("Test 7: Adding another test order...")
    test_order2 = {
        'order_id': 'TEST-67890',
        'email_subject': 'New customer order #TEST-67890',
        'email_date': datetime.now().isoformat(),
        'customer_name': 'Another Test Customer',
        'total': '$199.99',
        'recipient_email': 'cs@example.com',
        'tileware_products': [
            {
                'name': 'TileWare Another Product',
                'sku': 'TEST-SKU-002',
                'quantity': 1,
                'price': '$199.99'
            }
        ],
        'shipping_address': {
            'name': 'Another Test Customer',
            'street': '456 Test Avenue',
            'city': 'Test Town',
            'state': 'TS',
            'zip': '67890'
        }
    }
    
    if tracker.mark_order_as_sent(test_order2):
        print("✓ Successfully added second test order\n")
    
    # Test 8: List orders
    print("Test 8: Listing recent orders...")
    orders = tracker.get_sent_orders(limit=10)
    print(f"✓ Found {len(orders)} orders:")
    for order in orders:
        print(f"  - Order {order.get('order_id')}: {order.get('customer_name')} - {order.get('total_amount')}")
    
    # Cleanup test database
    print("\nCleaning up test database...")
    try:
        os.remove("test_order_tracking.db")
        print("✓ Test database removed")
    except:
        print("✗ Could not remove test database")
    
    print("\n=== All tests completed ===")


if __name__ == "__main__":
    test_order_tracking()