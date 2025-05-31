#!/usr/bin/env python3
"""Test admin panel resend functionality."""

import sys
import os
from pathlib import Path

# Add paths like admin panel does
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / 'admin_panel' / 'backend'))

from admin_panel.backend.services.order_service import OrderService
from admin_panel.backend.database import get_db_session
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

def test_admin_resend():
    """Test resending through admin panel service."""
    print("\n=== Testing Admin Panel Resend ===")
    
    # Get database session
    with get_db_session() as db:
        # Create order service
        service = OrderService(db)
        
        # Try to resend the order
        order_id = 'LAT-PDF-PRICE-TEST-001'
        print(f"Attempting to resend order {order_id}...")
        
        try:
            success = service.resend_order(order_id)
            
            if success:
                print("✓ Order resent successfully!")
                return True
            else:
                print("✗ Failed to resend order")
                return False
                
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Run the test."""
    print("=" * 60)
    print("Admin Panel Resend Test")
    print("=" * 60)
    
    success = test_admin_resend()
    
    print("\n" + "=" * 60)
    print(f"Test Result: {'✓ Success' if success else '✗ Failed'}")
    print("=" * 60)

if __name__ == "__main__":
    main()