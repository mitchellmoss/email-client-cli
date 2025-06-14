#!/usr/bin/env python3
"""Test TileWare order matching with new WooCommerce template."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.email_parser import TileProDepotParser
from src.claude_processor import ClaudeProcessor
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Sample email HTML based on the screenshot
test_email_html = """
<!DOCTYPE html>
<html>
<head>
    <title>New customer order</title>
</head>
<body>
    <div style="font-family: Arial, sans-serif;">
        <h1>New customer order</h1>
        <p>Woo! You've received a new order from Dan Rogers:</p>
        
        <h2>Order summary</h2>
        <p>Order #43333 (June 13, 2025)</p>
        
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 10px;">
                    <img src="product-image.jpg" style="width: 60px; height: 60px;">
                </td>
                <td style="padding: 10px;">
                    TileWare Promessa™ Series Tee Hook - Traditional - Brushed Nickel (#T101-212-BN)
                </td>
                <td style="padding: 10px; text-align: center;">
                    ×1
                </td>
                <td style="padding: 10px; text-align: right;">
                    $46.42
                </td>
            </tr>
        </table>
        
        <div style="margin-top: 20px;">
            <p>Subtotal: $46.42</p>
            <p>Shipping: UPS® Ground $13.47</p>
            <p><strong>Total: $59.89</strong></p>
            <p>Payment method: Credit / Debit Card</p>
        </div>
        
        <div style="margin-top: 30px;">
            <div style="float: left; width: 45%;">
                <h3>Billing address</h3>
                <p>
                    Dan Rogers<br>
                    131 Flanders Rd<br>
                    Westborough, MA 01581<br>
                    17742330210<br>
                    dan@installplusinc.com
                </p>
            </div>
            <div style="float: right; width: 45%;">
                <h3>Shipping address</h3>
                <p>
                    Dan Rogers<br>
                    131 Flanders Rd<br>
                    Westborough, MA 01581
                </p>
            </div>
            <div style="clear: both;"></div>
        </div>
        
        <p style="margin-top: 30px;">Congratulations on the sale!</p>
    </div>
</body>
</html>
"""

def test_tileware_detection():
    """Test TileWare product detection."""
    print("Testing TileWare Order Matching")
    print("=" * 50)
    
    # Initialize parser
    parser = TileProDepotParser()
    
    # Test 1: Product type detection
    print("\n1. Testing product type detection...")
    product_type = parser.get_product_type(test_email_html)
    print(f"   Product type detected: {product_type}")
    print(f"   ✓ PASS" if product_type == 'tileware' else f"   ✗ FAIL - Expected 'tileware', got '{product_type}'")
    
    # Test 2: TileWare product detection
    print("\n2. Testing TileWare product detection...")
    contains_tileware = parser.contains_tileware_product(test_email_html)
    print(f"   Contains TileWare: {contains_tileware}")
    print(f"   ✓ PASS" if contains_tileware else "   ✗ FAIL")
    
    # Test 3: Basic order info extraction
    print("\n3. Testing basic order info extraction...")
    order_info = parser.extract_basic_order_info(test_email_html)
    
    print(f"   Customer name: {order_info.get('customer_name')}")
    print(f"   Order ID: {order_info.get('order_id')}")
    print(f"   Shipping method: {order_info.get('shipping_method')}")
    print(f"   Total: {order_info.get('total')}")
    print(f"   Products found: {len(order_info.get('products', []))}")
    
    if order_info.get('products'):
        for i, product in enumerate(order_info['products']):
            print(f"   Product {i+1}: {product.get('name')}")
            print(f"             Type: {product.get('type')}")
    
    # Test 4: Order validation
    print("\n4. Testing order validation...")
    is_valid = parser.validate_order_data(order_info)
    print(f"   Order valid: {is_valid}")
    print(f"   ✓ PASS" if is_valid else "   ✗ FAIL")
    
    # Test 5: Claude processor (if API key is available)
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        print("\n5. Testing Claude processor...")
        try:
            processor = ClaudeProcessor(api_key)
            
            # Process as TileWare order
            order_data = processor.extract_order_details(test_email_html, product_type='tileware')
            
            if order_data:
                print(f"   ✓ Claude processing successful")
                print(f"   Order ID: {order_data.get('order_id')}")
                print(f"   Customer: {order_data.get('customer_name')}")
                
                if order_data.get('tileware_products'):
                    print(f"   TileWare products: {len(order_data['tileware_products'])}")
                    for product in order_data['tileware_products']:
                        print(f"     - {product.get('name')} (SKU: {product.get('sku')})")
                        print(f"       Quantity: {product.get('quantity')}, Price: {product.get('price')}")
            else:
                print(f"   ✗ Claude processing failed")
        except Exception as e:
            print(f"   ✗ Error with Claude processor: {e}")
    else:
        print("\n5. Skipping Claude processor test (no API key)")
    
    print("\n" + "=" * 50)
    print("Test complete!")

if __name__ == "__main__":
    test_tileware_detection()