#!/usr/bin/env python3
"""Test improved price matching for Laticrete products."""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.price_list_reader import PriceListReader

# Load environment variables
load_dotenv()


def test_price_matching():
    """Test various product matching scenarios."""
    print("TESTING IMPROVED PRICE MATCHING")
    print("=" * 50)
    
    reader = PriceListReader()
    
    # Test cases from real orders
    test_cases = [
        # Case 1: Wrong SKU but correct product name
        {
            'name': 'Laticrete HYDRO BAN Preformed Niches (various sizes) - Square 12" x 12"',
            'sku': '#9315-0808-S',  # Wrong SKU
            'expected_sku': '9311-1212-S'
        },
        # Case 2: Product with size variations
        {
            'name': 'HYDRO BAN PREFORMED NICHE 16X16',
            'sku': None,
            'expected_contains': 'HYDRO BAN'
        },
        # Case 3: Product with brand prefix
        {
            'name': 'Laticrete 254 Platinum',
            'sku': None,
            'expected_contains': 'PLATINUM'
        },
        # Case 4: Complex product name
        {
            'name': 'LATICRETE STRATA MAT Uncoupling Membrane',
            'sku': None,
            'expected_contains': 'STRATA'
        },
        # Case 5: Product with measurements
        {
            'name': 'HYDRO BAN Sheet Membrane 5\' x 100\'',
            'sku': None,
            'expected_contains': 'HYDRO BAN'
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test['name']}")
        print(f"SKU: {test.get('sku', 'None')}")
        
        # Find product
        result = reader.find_product(test['name'], test.get('sku'))
        
        if result:
            print(f"✓ FOUND: {result['name']}")
            print(f"  SKU: {result['sku']}")
            print(f"  Price: {result.get('price', 'N/A')}")
            
            # Check expectations
            if 'expected_sku' in test and result['sku'] == test['expected_sku']:
                print(f"  ✓ Correct SKU matched!")
            elif 'expected_contains' in test and test['expected_contains'].upper() in result['name'].upper():
                print(f"  ✓ Contains expected text: {test['expected_contains']}")
        else:
            print("✗ NOT FOUND")
            
            # Try to get alternatives
            alternatives = reader.find_best_match(test['name'], test.get('sku'), return_alternatives=True)
            if alternatives and alternatives.get('alternatives'):
                print("  Suggested alternatives:")
                for alt in alternatives['alternatives'][:3]:
                    print(f"    - {alt['name']} (SKU: {alt['sku']}, Score: {alt.get('match_score', 'N/A')})")
    
    print("\n" + "=" * 50)
    print("ADDITIONAL MATCHING CAPABILITIES:")
    print("- Partial SKU matching (handles wrong prefixes/suffixes)")
    print("- Brand + Description combined search")
    print("- Keyword extraction and matching")
    print("- Fuzzy string matching for typos")
    print("- Returns best alternatives when no exact match found")


if __name__ == "__main__":
    test_price_matching()