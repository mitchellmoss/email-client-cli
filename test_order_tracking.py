#!/usr/bin/env python3
"""
Test script for order tracking functionality.
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from src.order_tracker import OrderTracker

# Load environment variables
load_dotenv()


def test_order_tracking():
    """Test basic order tracking functionality."""
    print("🧪 Testing Order Tracking System\n")
    
    # Initialize tracker
    tracker = OrderTracker(db_path="test_order_tracking.db")
    print("✅ Database initialized")
    
    # Test data
    test_order_id = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    test_email_data = {
        'uid': 'test-email-123',
        'subject': f'[Tile Pro Depot] New customer order ({test_order_id})',
        'date': datetime.now().isoformat()
    }
    test_order_details = {
        'order_id': test_order_id,
        'customer_name': 'Test Customer',
        'tileware_products': [
            {
                'name': 'TileWare Test Product',
                'sku': 'TEST-123',
                'quantity': 2,
                'price': '$50.00'
            }
        ],
        'total': '$100.00'
    }
    
    # Test 1: Check order not sent yet
    print(f"\n📋 Test 1: Checking if order {test_order_id} has been sent...")
    is_sent, _ = tracker.has_order_been_sent(test_order_id)
    assert not is_sent, "Order should not be marked as sent yet"
    print("✅ Correctly identified as not sent")
    
    # Test 2: Mark order as sent
    print(f"\n📋 Test 2: Marking order {test_order_id} as sent...")
    success = tracker.mark_order_as_sent(
        order_id=test_order_id,
        email_data=test_email_data,
        order_details=test_order_details,
        formatted_content="Test formatted content",
        recipient="test@example.com"
    )
    assert success, "Failed to mark order as sent"
    print("✅ Order marked as sent")
    
    # Test 3: Check duplicate detection
    print(f"\n📋 Test 3: Testing duplicate detection...")
    is_sent, order_info = tracker.has_order_been_sent(test_order_id)
    assert is_sent, "Order should be marked as sent"
    assert order_info['order_id'] == test_order_id, "Wrong order returned"
    print("✅ Duplicate correctly detected")
    print(f"   Order was sent at: {order_info['sent_at']}")
    
    # Test 4: Get statistics
    print("\n📋 Test 4: Getting statistics...")
    stats = tracker.get_statistics(days=1)
    assert stats['total_orders_sent'] >= 1, "Should have at least 1 order"
    print(f"✅ Statistics retrieved: {stats['total_orders_sent']} orders in last day")
    
    # Test 5: Get order details
    print(f"\n📋 Test 5: Retrieving order details...")
    order = tracker.get_order_details(test_order_id)
    assert order is not None, "Order details not found"
    assert order['customer_name'] == 'Test Customer', "Wrong customer name"
    assert len(order['tileware_products']) == 1, "Wrong number of products"
    print("✅ Order details retrieved correctly")
    
    # Test 6: Get order history
    print(f"\n📋 Test 6: Getting order history...")
    history = tracker.get_order_history(test_order_id)
    assert len(history) >= 2, "Should have at least 2 history entries"
    print(f"✅ Found {len(history)} history entries")
    
    print("\n🎉 All tests passed!\n")
    
    # Clean up test database
    os.remove("test_order_tracking.db")
    print("🧹 Test database cleaned up")


if __name__ == "__main__":
    try:
        test_order_tracking()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)