#!/usr/bin/env python3
"""Test Laticrete order resending functionality."""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.order_tracker import OrderTracker
from src.laticrete_processor import LatricreteProcessor
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv(override=True)

def test_laticrete_resend():
    """Test resending a Laticrete order."""
    print("\n=== Testing Laticrete Order Resend ===")
    
    # Get order from database
    tracker = OrderTracker()
    order = tracker.get_order_details('LAT-PDF-PRICE-TEST-001')
    
    if not order:
        print("✗ Order not found in database")
        return False
    
    print(f"✓ Found order: {order['order_id']}")
    print(f"  Customer: {order['customer_name']}")
    print(f"  Sent to: {order['sent_to']}")
    
    # Check order_data
    order_data = order.get('order_data')
    if not order_data:
        print("✗ No order_data found")
        return False
    
    print(f"✓ Order data found with {len(order_data.get('laticrete_products', []))} products")
    
    # Test Laticrete processor directly
    processor = LatricreteProcessor()
    
    print("\nAttempting to process order...")
    try:
        success = processor.process_order(order_data)
        
        if success:
            print("✓ Order processed successfully!")
            return True
        else:
            print("✗ Order processing failed")
            return False
            
    except Exception as e:
        print(f"✗ Error processing order: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test."""
    print("=" * 60)
    print("Laticrete Order Resend Test")
    print("=" * 60)
    
    success = test_laticrete_resend()
    
    print("\n" + "=" * 60)
    print(f"Test Result: {'✓ Success' if success else '✗ Failed'}")
    print("=" * 60)

if __name__ == "__main__":
    main()