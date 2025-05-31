#!/usr/bin/env python3
"""Test script for Laticrete order processing functionality."""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.price_list_reader import PriceListReader
from src.pdf_filler import PDFOrderFormFiller
from src.laticrete_processor import LatricreteProcessor
from src.claude_processor import ClaudeProcessor
from src.email_parser import TileProDepotParser

# Load environment variables
load_dotenv()


def test_price_list_reader():
    """Test the price list reader functionality."""
    print("\n=== Testing Price List Reader ===")
    reader = PriceListReader()
    
    # Test searching for common Laticrete products
    test_products = [
        ("Hydro Ban", None),
        ("254 Platinum", None),
        ("STRATA MAT", None),
        ("Permacolor", None),
        ("SpectraLOCK", None)
    ]
    
    for name, sku in test_products:
        print(f"\nSearching for: {name}")
        result = reader.find_product(name, sku)
        if result:
            print(f"  Found: {result.get('name', 'N/A')} (SKU: {result.get('sku', 'N/A')})")
            print(f"  Price: {result.get('price', 'N/A')}")
        else:
            print("  Not found in price list")


def test_pdf_filler():
    """Test the PDF form filler functionality."""
    print("\n=== Testing PDF Filler ===")
    filler = PDFOrderFormFiller()
    
    # Test order data
    test_order = {
        'order_id': 'TEST-LAT-001',
        'customer_name': 'Test Customer - Laticrete',
        'shipping_address': {
            'name': 'Test Customer',
            'street': '456 Laticrete Lane',
            'city': 'Test City',
            'state': 'TX',
            'zip': '78901'
        },
        'laticrete_products': [
            {
                'name': 'LATICRETE HYDRO BAN Sheet Membrane',
                'sku': 'HB-SHEET-5',
                'quantity': 3,
                'price': '$125.00'
            },
            {
                'name': 'LATICRETE 254 Platinum Adhesive',
                'sku': '254-50',
                'quantity': 10,
                'price': '$45.00'
            },
            {
                'name': 'LATICRETE STRATA MAT Uncoupling Membrane',
                'sku': 'SM-150',
                'quantity': 2,
                'price': '$180.00'
            }
        ]
    }
    
    output_path = "test_laticrete_order_form.pdf"
    if filler.fill_order_form(test_order, output_path):
        print(f"✓ Test order form created: {output_path}")
    else:
        print("✗ Failed to create test order form")


def test_email_detection():
    """Test detection of Laticrete products in sample email."""
    print("\n=== Testing Laticrete Product Detection ===")
    
    parser = TileProDepotParser()
    
    # Sample HTML with Laticrete products
    sample_html = """
    <html>
    <body>
        <h2>Order #12345</h2>
        <p>You've received the following order from John Doe:</p>
        <table>
            <tr>
                <th>Product</th>
                <th>Quantity</th>
                <th>Price</th>
            </tr>
            <tr>
                <td>LATICRETE 254 Platinum Thin-Set Adhesive - 50 lb bag</td>
                <td>5</td>
                <td>$225.00</td>
            </tr>
            <tr>
                <td>LATICRETE HYDRO BAN Waterproofing Membrane</td>
                <td>2</td>
                <td>$250.00</td>
            </tr>
            <tr>
                <td>Some Other Product (not Laticrete)</td>
                <td>1</td>
                <td>$50.00</td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Test product type detection
    product_type = parser.get_product_type(sample_html)
    print(f"Detected product type: {product_type}")
    
    # Test individual detection methods
    has_tileware = parser.contains_tileware_product(sample_html)
    has_laticrete = parser.contains_laticrete_product(sample_html)
    
    print(f"Contains TileWare: {has_tileware}")
    print(f"Contains Laticrete: {has_laticrete}")


def test_claude_extraction():
    """Test Claude API extraction for Laticrete products."""
    print("\n=== Testing Claude Extraction for Laticrete ===")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("✗ ANTHROPIC_API_KEY not set, skipping Claude test")
        return
    
    processor = ClaudeProcessor(api_key)
    
    # Sample email HTML
    sample_html = """
    <html>
    <body>
        <h1>New customer order</h1>
        <p>You've received the following order from Jane Smith:</p>
        <p>[Order #54321] (November 30, 2024)</p>
        
        <h3>Order Details</h3>
        <table>
            <tr>
                <th>Product</th>
                <th>Quantity</th>
                <th>Price</th>
            </tr>
            <tr>
                <td>LATICRETE 254 Platinum Multipurpose Thinset - Gray 50lb (#254-50G)</td>
                <td>10</td>
                <td>$450.00</td>
            </tr>
            <tr>
                <td>LATICRETE HYDRO BAN Sheet Membrane 5' x 100' (#HB-5X100)</td>
                <td>1</td>
                <td>$425.00</td>
            </tr>
        </table>
        
        <h3>Shipping Address</h3>
        <p>
        Jane Smith<br>
        789 Construction Blvd<br>
        Builder City, CA 90210<br>
        </p>
        
        <p>Shipping Method: UPS GROUND</p>
        <p>Order Total: $875.00</p>
    </body>
    </html>
    """
    
    # Extract order details
    order_details = processor.extract_order_details(sample_html, product_type="laticrete")
    
    if order_details:
        print("✓ Successfully extracted order details:")
        print(f"  Order ID: {order_details.get('order_id')}")
        print(f"  Customer: {order_details.get('customer_name')}")
        print(f"  Products: {len(order_details.get('laticrete_products', []))}")
        for product in order_details.get('laticrete_products', []):
            print(f"    - {product.get('name')} x{product.get('quantity')}")
    else:
        print("✗ Failed to extract order details")


def main():
    """Run all tests."""
    print("LATICRETE ORDER PROCESSING TEST SUITE")
    print("=" * 50)
    
    # Run tests
    test_price_list_reader()
    test_pdf_filler()
    test_email_detection()
    test_claude_extraction()
    
    print("\n" + "=" * 50)
    print("TEST SUITE COMPLETED")


if __name__ == "__main__":
    main()