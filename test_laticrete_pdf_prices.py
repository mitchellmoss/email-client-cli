#!/usr/bin/env python3
"""Test that Laticrete PDFs include product prices."""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.laticrete_processor import LatricreteProcessor
from src.order_tracker import OrderTracker
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

def test_laticrete_pdf_with_prices():
    """Test creating a Laticrete order PDF with prices."""
    print("\n=== Testing Laticrete PDF with Prices ===")
    
    processor = LatricreteProcessor()
    tracker = OrderTracker()
    
    # Create test order
    test_order = {
        "order_id": "PDF-PRICE-TEST-001",
        "customer_name": "PDF Price Test Customer",
        "phone": "617-555-1234",
        "email": "pdftest@example.com",
        "laticrete_products": [
            {
                "name": "LATICRETE 254 PLATINUM PLUS GREY 25LB",
                "sku": None,
                "quantity": 5,
                "price": None  # Will be enriched
            },
            {
                "name": "LATICRETE HYDRO BAN PREFORMED NICHE 12X12IN SQUARE",
                "sku": None,
                "quantity": 2,
                "price": None  # Will be enriched
            },
            {
                "name": "LATICRETE PERMACOLOR SELECT GROUT - SILVER",
                "sku": None,
                "quantity": 10,
                "price": None  # Will be enriched
            }
        ],
        "shipping_address": {
            "name": "PDF Price Test Customer",
            "company": "Test Construction Co.",
            "street": "123 Test Street",
            "city": "Boston",
            "state": "MA",
            "zip": "02101"
        },
        "shipping_method": "UPS GROUND",
        "po_number": "PDF-TEST-2024",
        "notes": "Testing PDF generation with prices"
    }
    
    print("Processing order with price enrichment...")
    
    # Process the order
    success = processor.process_order(test_order)
    
    if success:
        print("✓ Order processed and sent successfully!")
        
        # Track in database
        recipient = os.getenv('LATICRETE_CS_EMAIL', 'mitch.mossy@gmail.com')
        tracker.mark_order_as_sent(
            order_id=f"LAT-{test_order['order_id']}",
            email_data={
                'subject': f"Test Laticrete PDF Prices {test_order['order_id']}",
                'uid': f"test-pdf-prices-{datetime.now().timestamp()}"
            },
            order_details=test_order,
            formatted_content="Laticrete order with PDF attachment (price test)",
            recipient=recipient
        )
        
        print("\nExpected results in PDF:")
        print("- 254 PLATINUM PLUS GREY 25LB: Should show price ~$40.48")
        print("- HYDRO BAN PREFORMED NICHE: Should show price ~$49.82")
        print("- PERMACOLOR SELECT GROUT: Should show price ~$11.57")
        print("\nCheck your email for the PDF with prices!")
        
        return True
    else:
        print("✗ Failed to process order")
        return False

def main():
    """Run the PDF price test."""
    print("=" * 60)
    print("Laticrete PDF Price Test")
    print("=" * 60)
    
    success = test_laticrete_pdf_with_prices()
    
    print("\n" + "=" * 60)
    print(f"Test Result: {'✓ Success' if success else '✗ Failed'}")
    print("=" * 60)

if __name__ == "__main__":
    main()