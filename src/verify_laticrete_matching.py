#!/usr/bin/env python3
"""Comprehensive verification of Laticrete product matching functionality."""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.price_list_reader import PriceListReader
from src.laticrete_processor import LatricreteProcessor
from src.claude_processor import ClaudeProcessor
from src.email_parser import TileProDepotParser

# Load environment variables
load_dotenv()


def test_matching_scenarios():
    """Test various real-world product matching scenarios."""
    print("\n=== TESTING PRODUCT MATCHING SCENARIOS ===")
    reader = PriceListReader()
    
    # Real-world product names that have caused issues
    problem_products = [
        # Products with size variations
        {
            'name': 'LATICRETE HYDRO BAN Preformed Niches (various sizes) - Square 12" x 12"',
            'sku': '#9315-0808-S',
            'notes': 'Wrong SKU provided, should match by name'
        },
        {
            'name': 'LATICRETE HYDRO BAN Preformed Niche 16" x 16" Square',
            'sku': None,
            'notes': 'Size variation'
        },
        {
            'name': 'LATICRETE HYDRO BAN Preformed Seat Triangle 16" x 16"',
            'sku': None,
            'notes': 'Seat vs Niche variation'
        },
        
        # Products with different naming conventions
        {
            'name': 'LATICRETE STRATA MAT Uncoupling Membrane',
            'sku': None,
            'notes': 'STRATA MAT vs STRATAHEAT MAT confusion'
        },
        {
            'name': 'LATICRETE STRATA MAT - 150 sq ft roll',
            'sku': None,
            'notes': 'With size specification'
        },
        
        # Products with brand variations
        {
            'name': 'Laticrete 254 Platinum Thinset Mortar - 50 lb',
            'sku': None,
            'notes': 'Different product description'
        },
        {
            'name': 'LATICRETE 254 PLATINUM PLUS GREY 25LB',
            'sku': None,
            'notes': 'Exact match expected'
        },
        
        # Complex product names
        {
            'name': 'LATICRETE HYDRO BAN Sheet Waterproofing Membrane 5\' x 100\'',
            'sku': None,
            'notes': 'With dimensions'
        },
        {
            'name': 'LATICRETE SpectraLOCK PRO Premium Grout',
            'sku': None,
            'notes': 'Premium product line'
        },
        {
            'name': 'LATICRETE Permacolor Select Grout - Various Colors',
            'sku': None,
            'notes': 'Color variations'
        }
    ]
    
    results = {
        'matched': 0,
        'unmatched': 0,
        'details': []
    }
    
    for product in problem_products:
        print(f"\n--- Testing: {product['name']}")
        print(f"    SKU: {product.get('sku', 'None')}")
        print(f"    Notes: {product['notes']}")
        
        # Try to find the product
        result = reader.find_product(product['name'], product.get('sku'))
        
        if result:
            results['matched'] += 1
            print(f"    ✓ MATCHED: {result['name']}")
            print(f"      SKU: {result['sku']}")
            print(f"      Price: {result.get('price', 'N/A')}")
            
            results['details'].append({
                'original': product['name'],
                'matched': True,
                'found_name': result['name'],
                'found_sku': result['sku'],
                'price': result.get('price', 'N/A')
            })
        else:
            results['unmatched'] += 1
            print(f"    ✗ NOT MATCHED")
            
            # Get alternatives
            alternatives = reader.find_best_match(
                product['name'], 
                product.get('sku'), 
                return_alternatives=True
            )
            
            if alternatives and alternatives.get('alternatives'):
                print("    Alternatives found:")
                for i, alt in enumerate(alternatives['alternatives'][:3], 1):
                    print(f"      {i}. {alt['name']} (SKU: {alt['sku']}, Score: {alt.get('match_score', 'N/A')})")
            
            results['details'].append({
                'original': product['name'],
                'matched': False,
                'alternatives': alternatives.get('alternatives', []) if alternatives else []
            })
    
    return results


def test_end_to_end_processing():
    """Test complete order processing flow."""
    print("\n=== TESTING END-TO-END PROCESSING ===")
    
    processor = LatricreteProcessor()
    
    # Sample order with products that have caused issues
    test_order = {
        'order_id': 'TEST-001',
        'customer_name': 'Test Customer',
        'shipping_address': {
            'street': '123 Test St',
            'city': 'Test City',
            'state': 'CA',
            'zip': '90210'
        },
        'laticrete_products': [
            {
                'name': 'LATICRETE HYDRO BAN Preformed Niches (various sizes) - Square 12" x 12"',
                'sku': '#9315-0808-S',  # Wrong SKU
                'quantity': 2,
                'price': '$99.64'
            },
            {
                'name': 'LATICRETE 254 Platinum Thinset - 50 lb',
                'sku': None,
                'quantity': 5,
                'price': '$40.00'
            },
            {
                'name': 'LATICRETE STRATA MAT Uncoupling Membrane',
                'sku': None,
                'quantity': 1,
                'price': '$180.00'
            }
        ]
    }
    
    # Process order to see enrichment
    enriched_order = processor._enrich_with_prices(test_order)
    
    print("\nEnrichment Results:")
    for i, product in enumerate(enriched_order['laticrete_products'], 1):
        print(f"\n{i}. {product['name']}")
        print(f"   Original SKU: {test_order['laticrete_products'][i-1].get('sku', 'None')}")
        print(f"   Matched SKU: {product.get('sku', 'None')}")
        print(f"   List Price: {product.get('list_price', 'N/A')}")
        print(f"   Needs Verification: {product.get('needs_verification', False)}")
        if product.get('verification_note'):
            print(f"   Note: {product['verification_note']}")
    
    return enriched_order


def test_price_list_coverage():
    """Analyze price list coverage and common product categories."""
    print("\n=== ANALYZING PRICE LIST COVERAGE ===")
    
    reader = PriceListReader()
    all_products = reader.get_all_products()
    
    # Analyze product categories
    categories = {}
    brands = {}
    product_types = []
    
    for product in all_products:
        # Extract category
        if 'category' in product:
            cat = product['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        # Extract brand
        if 'brand' in product:
            brand = product['brand']
            brands[brand] = brands.get(brand, 0) + 1
        
        # Analyze product types from names
        name = product.get('name', '').upper()
        if 'HYDRO BAN' in name:
            product_types.append('HYDRO BAN')
        elif '254 PLATINUM' in name:
            product_types.append('254 PLATINUM')
        elif 'STRATA' in name:
            product_types.append('STRATA')
        elif 'SPECTRALOCK' in name:
            product_types.append('SPECTRALOCK')
        elif 'PERMACOLOR' in name:
            product_types.append('PERMACOLOR')
    
    print(f"\nTotal products in price list: {len(all_products)}")
    print(f"\nCategories found: {len(categories)}")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  - {cat}: {count} products")
    
    print(f"\nBrands found: {len(brands)}")
    for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  - {brand}: {count} products")
    
    # Count common product types
    type_counts = {}
    for ptype in product_types:
        type_counts[ptype] = type_counts.get(ptype, 0) + 1
    
    print("\nCommon product types:")
    for ptype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {ptype}: {count} products")


def generate_matching_report():
    """Generate a comprehensive report on matching capabilities."""
    print("\n" + "=" * 70)
    print("LATICRETE PRODUCT MATCHING VERIFICATION REPORT")
    print("=" * 70)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    matching_results = test_matching_scenarios()
    enriched_order = test_end_to_end_processing()
    test_price_list_coverage()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    total_tested = matching_results['matched'] + matching_results['unmatched']
    success_rate = (matching_results['matched'] / total_tested * 100) if total_tested > 0 else 0
    
    print(f"\nProduct Matching Performance:")
    print(f"  - Total products tested: {total_tested}")
    print(f"  - Successfully matched: {matching_results['matched']}")
    print(f"  - Failed to match: {matching_results['unmatched']}")
    print(f"  - Success rate: {success_rate:.1f}%")
    
    print(f"\nMatching Strategies Used:")
    print("  1. Exact SKU matching")
    print("  2. Partial SKU matching (handles wrong prefixes)")
    print("  3. Exact name matching")
    print("  4. Keyword-based matching")
    print("  5. Fuzzy string matching")
    print("  6. Brand + Description combined search")
    
    print(f"\nRecommendations:")
    if matching_results['unmatched'] > 0:
        print("  - Review unmatched products and add manual mappings")
        print("  - Consider updating price list with common product variations")
        print("  - Use admin panel to create product mappings for failed matches")
    
    print("\n" + "=" * 70)
    
    # Save detailed results
    report_file = f"laticrete_matching_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tested': total_tested,
                'matched': matching_results['matched'],
                'unmatched': matching_results['unmatched'],
                'success_rate': success_rate
            },
            'detailed_results': matching_results['details']
        }, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")


if __name__ == "__main__":
    generate_matching_report()