#!/usr/bin/env python3
"""Test script to verify billing address fallback functionality."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.order_formatter import OrderFormatter
from src.pdf_filler import PDFOrderFormFiller
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def test_tileware_order_formatting():
    """Test TileWare order formatting with various address scenarios."""
    formatter = OrderFormatter()
    
    # Test 1: Order with shipping address
    order1 = {
        'order_id': '12345',
        'customer_name': 'John Doe',
        'tileware_products': [
            {'name': 'TileWare Product A', 'sku': 'TW-001', 'quantity': 2}
        ],
        'shipping_address': {
            'name': 'John Doe',
            'street': '123 Ship Street',
            'city': 'Ship City',
            'state': 'SC',
            'zip': '12345'
        },
        'billing_address': {
            'name': 'John Doe',
            'street': '456 Bill Avenue',
            'city': 'Bill City',
            'state': 'BC',
            'zip': '67890'
        },
        'shipping_method': 'UPS Ground'
    }
    
    print("Test 1 - Order with shipping address:")
    print(formatter.format_order(order1))
    print("\n" + "="*50 + "\n")
    
    # Test 2: Order with only billing address
    order2 = {
        'order_id': '12346',
        'customer_name': 'Jane Smith',
        'tileware_products': [
            {'name': 'TileWare Product B', 'sku': 'TW-002', 'quantity': 3}
        ],
        'shipping_address': None,  # No shipping address
        'billing_address': {
            'name': 'Jane Smith',
            'street': '789 Bill Street',
            'city': 'Billing Town',
            'state': 'BT',
            'zip': '11111'
        },
        'shipping_method': 'FedEx'
    }
    
    print("Test 2 - Order with only billing address:")
    print(formatter.format_order(order2))
    print("\n" + "="*50 + "\n")
    
    # Test 3: Order with empty shipping address
    order3 = {
        'order_id': '12347',
        'customer_name': 'Bob Johnson',
        'tileware_products': [
            {'name': 'TileWare Product C', 'sku': 'TW-003', 'quantity': 1}
        ],
        'shipping_address': {},  # Empty shipping address
        'billing_address': {
            'name': 'Bob Johnson',
            'street': '321 Billing Road',
            'city': 'Bill Village',
            'state': 'BV',
            'zip': '22222'
        },
        'shipping_method': 'USPS'
    }
    
    print("Test 3 - Order with empty shipping address:")
    print(formatter.format_order(order3))
    print("\n" + "="*50 + "\n")
    
    # Test 4: Order with neither address
    order4 = {
        'order_id': '12348',
        'customer_name': 'Alice Brown',
        'tileware_products': [
            {'name': 'TileWare Product D', 'sku': 'TW-004', 'quantity': 5}
        ],
        'shipping_address': None,
        'billing_address': None,
        'shipping_method': 'Pickup'
    }
    
    print("Test 4 - Order with no addresses (should use customer name only):")
    print(formatter.format_order(order4))
    print("\n" + "="*50 + "\n")

def test_laticrete_pdf_generation():
    """Test Laticrete PDF generation with billing address fallback."""
    pdf_filler = PDFOrderFormFiller()
    
    # Test order with only billing address
    test_order = {
        'order_id': 'LAT-TEST-001',
        'customer_name': 'Test Customer',
        'phone': '555-123-4567',
        'shipping_address': None,  # No shipping address
        'billing_address': {
            'street': '999 Billing Boulevard',
            'city': 'Billing City',
            'state': 'CA',
            'zip': '90210'
        },
        'shipping_method': 'UPS Ground',
        'laticrete_products': [
            {
                'name': 'HYDRO BAN Sheet Membrane',
                'sku': 'HB-SHEET-5',
                'quantity': 2,
                'list_price': '$125.00'
            }
        ]
    }
    
    output_path = "test_billing_fallback_order.pdf"
    print(f"Generating test PDF with billing address fallback...")
    
    if pdf_filler.fill_order_form(test_order, output_path):
        print(f"✓ Test PDF created successfully: {output_path}")
        print(f"  Please check the PDF to verify billing address was used for shipping")
    else:
        print("✗ Failed to create test PDF")

def main():
    """Run all tests."""
    print("Testing Billing Address Fallback Functionality\n")
    
    print("=" * 60)
    print("TESTING TILEWARE ORDER FORMATTING")
    print("=" * 60 + "\n")
    test_tileware_order_formatting()
    
    print("\n" + "=" * 60)
    print("TESTING LATICRETE PDF GENERATION")
    print("=" * 60 + "\n")
    test_laticrete_pdf_generation()
    
    print("\n✓ All tests completed. Please review the output above.")

if __name__ == "__main__":
    main()