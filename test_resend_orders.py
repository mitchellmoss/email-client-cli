#!/usr/bin/env python3
"""Test script for debugging order resend functionality."""

import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.order_tracker import OrderTracker
from src.email_sender import EmailSender
from admin_panel.backend.services.order_service import OrderService
from admin_panel.backend.database import SessionLocal

def test_order_lookup():
    """Test order lookup with various ID formats."""
    print("\n=== Testing Order Lookup ===")
    
    tracker = OrderTracker("order_tracking.db")
    
    # Test IDs
    test_ids = [
        "43207",           # Plain ID
        "TW-43207",        # With TW prefix
        "LAT-43156",       # With LAT prefix
        "43156",           # Another plain ID
    ]
    
    for order_id in test_ids:
        print(f"\nLooking up order: {order_id}")
        
        # Try direct lookup
        order = tracker.get_order_details(order_id)
        if order:
            print(f"  ✓ Found order {order_id}")
            print(f"    Customer: {order.get('customer_name')}")
            print(f"    Sent to: {order.get('sent_to')}")
            print(f"    Sent at: {order.get('sent_at')}")
        else:
            print(f"  ✗ Order {order_id} not found")
            
            # Try without prefix
            if '-' in order_id:
                clean_id = order_id.split('-')[1]
                print(f"  Trying without prefix: {clean_id}")
                order = tracker.get_order_details(clean_id)
                if order:
                    print(f"    ✓ Found order {clean_id}")
                    print(f"    Customer: {order.get('customer_name')}")
                else:
                    print(f"    ✗ Order {clean_id} not found")

def test_email_sender():
    """Test email sender methods."""
    print("\n=== Testing Email Sender ===")
    
    try:
        sender = EmailSender()
        print("✓ EmailSender initialized successfully")
        
        # Check if send_order_to_cs method exists
        if hasattr(sender, 'send_order_to_cs'):
            print("✓ send_order_to_cs method exists")
        else:
            print("✗ send_order_to_cs method not found")
            
        # Check if send_order_email method exists
        if hasattr(sender, 'send_order_email'):
            print("✓ send_order_email method exists")
        else:
            print("✗ send_order_email method not found")
            
        # List all send methods
        print("\nAvailable send methods:")
        for attr in dir(sender):
            if 'send' in attr and not attr.startswith('_'):
                print(f"  - {attr}")
                
    except Exception as e:
        print(f"✗ Error initializing EmailSender: {e}")

def test_order_service_resend():
    """Test the order service resend functionality."""
    print("\n=== Testing Order Service Resend ===")
    
    db = SessionLocal()
    try:
        service = OrderService(db)
        
        # Test with various order IDs
        test_cases = [
            ("43207", "Plain order ID"),
            ("TW-43207", "Order ID with TW prefix"),
        ]
        
        for order_id, description in test_cases:
            print(f"\nTesting: {description} - {order_id}")
            
            try:
                # First check if order exists
                order = service.get_order_detail(order_id)
                if not order:
                    # Try without prefix
                    if '-' in order_id:
                        clean_id = order_id.split('-')[1]
                        order = service.get_order_detail(clean_id)
                        
                if order:
                    print(f"  ✓ Order found")
                    print(f"    Customer: {order.get('customer_name')}")
                    print(f"    Format content length: {len(order.get('formatted_content', ''))}")
                    
                    # Try to resend
                    print(f"  Attempting resend...")
                    success = service.resend_order(order_id)
                    if success:
                        print(f"  ✓ Resend successful")
                    else:
                        print(f"  ✗ Resend failed")
                else:
                    print(f"  ✗ Order not found")
                    
            except Exception as e:
                print(f"  ✗ Error: {e}")
                import traceback
                traceback.print_exc()
                
    finally:
        db.close()

def test_formatted_content_structure():
    """Check the structure of formatted_content in orders."""
    print("\n=== Testing Formatted Content Structure ===")
    
    tracker = OrderTracker("order_tracking.db")
    
    # Get a few recent orders
    orders = tracker.get_sent_orders(limit=5)
    
    for order in orders:
        print(f"\nOrder {order.get('order_id')}:")
        formatted_content = order.get('formatted_content', '')
        
        if formatted_content:
            print(f"  Content length: {len(formatted_content)}")
            print(f"  Content preview: {formatted_content[:100]}...")
            
            # Check if it's HTML or plain text
            if '<html>' in formatted_content.lower() or '<div>' in formatted_content.lower():
                print(f"  Format: HTML")
            else:
                print(f"  Format: Plain text")
        else:
            print(f"  ✗ No formatted content")

def main():
    """Run all tests."""
    print("=" * 50)
    print("Order Resend Debugging Test")
    print("=" * 50)
    
    # Run tests
    test_order_lookup()
    test_email_sender()
    test_formatted_content_structure()
    test_order_service_resend()
    
    print("\n" + "=" * 50)
    print("Test completed")
    print("=" * 50)

if __name__ == "__main__":
    main()