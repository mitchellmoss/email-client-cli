#!/usr/bin/env python3
"""Test script to send sample TileWare and Laticrete orders with updated signatures."""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.email_sender import EmailSender
from src.order_formatter import OrderFormatter
from src.laticrete_processor import LatricreteProcessor
from src.order_tracker import OrderTracker
from dotenv import load_dotenv

# Load environment variables (force reload)
load_dotenv(override=True)

def send_test_tileware_order():
    """Send a test TileWare order."""
    print("\n=== Sending Test TileWare Order ===")
    
    # Initialize components with custom signature
    email_signature = os.getenv('EMAIL_SIGNATURE_TEXT')
    print(f"Using custom signature: {'Yes' if email_signature else 'No'}")
    
    sender = EmailSender(
        smtp_server=os.getenv('SMTP_SERVER'),
        smtp_port=int(os.getenv('SMTP_PORT', 587)),
        username=os.getenv('SMTP_USERNAME'),
        password=os.getenv('SMTP_PASSWORD'),
        signature_html=email_signature
    )
    
    formatter = OrderFormatter()
    tracker = OrderTracker()
    
    # Create test order data
    test_order = {
        "order_id": "TEST-TW-001",
        "customer_name": "Test Customer",
        "tileware_products": [
            {
                "name": "TileWare Promessa™ Series Towel Bar",
                "sku": "T102-124-BN",
                "quantity": 2,
                "price": "$89.99"
            },
            {
                "name": "TileWare Bella Vetro™ Glass Tile Hook",
                "sku": "BV-201-PC",
                "quantity": 4,
                "price": "$34.99"
            }
        ],
        "shipping_address": {
            "name": "Test Customer",
            "street": "123 Test Street",
            "city": "Boston",
            "state": "MA",
            "zip": "02101"
        },
        "shipping_method": "UPS GROUND",
        "total": "$319.92"
    }
    
    # Format the order
    formatted_order = formatter.format_order(test_order)
    print(f"Formatted order preview:\n{formatted_order[:200]}...")
    
    # Send the email
    recipient = os.getenv('CS_EMAIL', 'mitch.mossy@gmail.com')
    print(f"Sending to: {recipient}")
    
    success = sender.send_order_to_cs(
        recipient=recipient,
        order_text=formatted_order,
        original_order_id=test_order['order_id']
    )
    
    if success:
        print("✓ Test TileWare order sent successfully!")
        
        # Track in database
        tracker.mark_order_as_sent(
            order_id=test_order['order_id'],
            email_data={
                'subject': f"Test TileWare Order {test_order['order_id']}",
                'uid': f"test-{datetime.now().timestamp()}"
            },
            order_details=test_order,
            formatted_content=formatted_order,
            recipient=recipient
        )
    else:
        print("✗ Failed to send test TileWare order")
    
    return success

def send_test_laticrete_order():
    """Send a test Laticrete order with PDF."""
    print("\n=== Sending Test Laticrete Order ===")
    
    # Initialize processor
    processor = LatricreteProcessor()
    tracker = OrderTracker()
    
    # Create test order data
    test_order = {
        "order_id": "TEST-LAT-001",
        "customer_name": "Test Laticrete Customer",
        "phone": "617-555-1234",
        "email": "test@example.com",
        "laticrete_products": [
            {
                "name": "LATICRETE HYDRO BAN Sheet Waterproofing Membrane 5' x 100'",
                "sku": None,
                "quantity": 2,
                "price": None  # Will be enriched from price list
            },
            {
                "name": "LATICRETE 254 PLATINUM PLUS GREY 25LB",
                "sku": None,
                "quantity": 5,
                "price": None  # Will be enriched from price list
            }
        ],
        "shipping_address": {
            "name": "Test Laticrete Customer",
            "company": "Test Construction Co.",
            "street": "456 Builder Lane",
            "city": "Worcester",
            "state": "MA",
            "zip": "01609"
        },
        "shipping_method": "LTL FREIGHT",
        "po_number": "TEST-PO-2024",
        "notes": "Test order - please confirm signature is updated"
    }
    
    print(f"Processing Laticrete order {test_order['order_id']}...")
    
    # Process the order (enriches prices, fills PDF, sends email)
    success = processor.process_order(test_order)
    
    if success:
        print("✓ Test Laticrete order sent successfully!")
        
        # Track in database
        recipient = os.getenv('LATICRETE_CS_EMAIL', 'mitch.mossy@gmail.com')
        tracker.mark_order_as_sent(
            order_id=test_order['order_id'],
            email_data={
                'subject': f"Test Laticrete Order {test_order['order_id']}",
                'uid': f"test-lat-{datetime.now().timestamp()}"
            },
            order_details=test_order,
            formatted_content="Laticrete order with PDF attachment",
            recipient=recipient
        )
    else:
        print("✗ Failed to send test Laticrete order")
    
    return success

def main():
    """Run the email signature tests."""
    print("=" * 50)
    print("Email Signature Test")
    print("=" * 50)
    print("\nThis will send test orders to verify the updated email signature.")
    print("Make sure you've updated the signature in the admin UI first!")
    
    # Check environment
    cs_email = os.getenv('CS_EMAIL', 'Not set')
    lat_email = os.getenv('LATICRETE_CS_EMAIL', 'Not set')
    
    print(f"\nTileWare orders will be sent to: {cs_email}")
    print(f"Laticrete orders will be sent to: {lat_email}")
    
    # Auto-proceed for non-interactive mode
    print("\nProceeding with test emails...")
    
    # Send test orders
    tileware_success = send_test_tileware_order()
    laticrete_success = send_test_laticrete_order()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"TileWare order: {'✓ Sent' if tileware_success else '✗ Failed'}")
    print(f"Laticrete order: {'✓ Sent' if laticrete_success else '✗ Failed'}")
    print("=" * 50)
    
    if tileware_success and laticrete_success:
        print("\nBoth test emails sent successfully!")
        print("Check your inbox to verify the signature has been updated.")
    else:
        print("\nSome tests failed. Check the logs for details.")

if __name__ == "__main__":
    main()