#!/usr/bin/env python3
"""
Order management utility for the Email Client CLI.
Provides commands to view, search, and manage processed orders.
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from tabulate import tabulate
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.order_tracker import OrderTracker
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()
logger = setup_logger(__name__)


def format_datetime(dt_string):
    """Format datetime string for display."""
    if not dt_string:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return dt_string


def cmd_stats(args):
    """Display order processing statistics."""
    tracker = OrderTracker()
    stats = tracker.get_statistics(days=args.days)
    
    print(f"\n📊 Order Processing Statistics (Last {args.days} days)")
    print("=" * 50)
    print(f"Total Orders Sent: {stats.get('total_orders_sent', 0)}")
    print(f"Duplicate Attempts Blocked: {stats.get('duplicate_attempts_blocked', 0)}")
    
    # Show daily breakdown
    daily_counts = stats.get('daily_counts', [])
    if daily_counts:
        print("\n📅 Daily Breakdown:")
        for day_stat in daily_counts:
            print(f"  {day_stat['date']}: {day_stat['count']} orders")
    
    print()


def cmd_list(args):
    """List recent orders."""
    tracker = OrderTracker()
    orders = tracker.get_sent_orders(limit=args.limit)
    
    if not orders:
        print("No orders found.")
        return
    
    # Prepare table data
    table_data = []
    for order in orders:
        table_data.append([
            order['order_id'],
            order['customer_name'] or 'N/A',
            format_datetime(order['created_at']),
            order['sent_to'],
            order['order_total'] or 'N/A'
        ])
    
    headers = ['Order ID', 'Customer', 'Sent At', 'Sent To', 'Total']
    print(f"\n📦 Recent Orders (showing {len(orders)} of {args.limit} requested)")
    print(tabulate(table_data, headers=headers, tablefmt='grid'))
    print()


def cmd_view(args):
    """View details of a specific order."""
    tracker = OrderTracker()
    order = tracker.get_order_details(args.order_id)
    
    if not order:
        print(f"Order {args.order_id} not found.")
        return
    
    print(f"\n📋 Order Details: {args.order_id}")
    print("=" * 50)
    print(f"Customer: {order.get('customer_name', 'N/A')}")
    print(f"Email Subject: {order.get('email_subject', 'N/A')}")
    print(f"Sent At: {format_datetime(order.get('created_at'))}")
    print(f"Sent To: {order.get('sent_to', 'N/A')}")
    print(f"Order Total: {order.get('order_total', 'N/A')}")
    
    # Show products
    products = order.get('tileware_products', [])
    if products:
        print("\n📦 TileWare Products:")
        for i, product in enumerate(products, 1):
            print(f"  {i}. {product.get('name', 'Unknown Product')}")
            if product.get('sku'):
                print(f"     SKU: {product['sku']}")
            if product.get('quantity'):
                print(f"     Quantity: {product['quantity']}")
            if product.get('price'):
                print(f"     Price: {product['price']}")
    
    # Show processing history
    if args.history:
        history = tracker.get_order_history(args.order_id)
        if history:
            print("\n📜 Processing History:")
            for entry in history:
                print(f"  {format_datetime(entry['timestamp'])} - {entry['action']}: {entry['details']}")
    
    # Show formatted content
    if args.show_content and order.get('formatted_content'):
        print("\n📄 Formatted Content:")
        print("-" * 50)
        print(order['formatted_content'])
        print("-" * 50)
    
    print()


def cmd_check(args):
    """Check if an order has been sent."""
    tracker = OrderTracker()
    is_sent, order_details = tracker.has_order_been_sent(args.order_id)
    
    if is_sent:
        print(f"✅ Order {args.order_id} was sent on {format_datetime(order_details.get('created_at'))}")
        print(f"   Sent to: {order_details.get('sent_to')}")
        print(f"   Customer: {order_details.get('customer_name', 'N/A')}")
    else:
        print(f"❌ Order {args.order_id} has not been sent yet.")
    print()


def cmd_cleanup(args):
    """Clean up old records."""
    if not args.force:
        print(f"⚠️  This will delete all orders older than {args.days} days.")
        response = input("Are you sure? (y/N): ")
        if response.lower() != 'y':
            print("Cleanup cancelled.")
            return
    
    tracker = OrderTracker()
    deleted = tracker.cleanup_old_records(days=args.days)
    print(f"🧹 Cleaned up {deleted} old records.")
    print()


def main():
    """Main entry point for the order management utility."""
    parser = argparse.ArgumentParser(
        description='Manage processed orders for Email Client CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s stats                    # Show statistics for last 7 days
  %(prog)s stats --days 30         # Show statistics for last 30 days
  %(prog)s list                     # List recent orders
  %(prog)s list --limit 50         # List last 50 orders
  %(prog)s view 43060              # View details for order 43060
  %(prog)s view 43060 --history    # Include processing history
  %(prog)s check 43060             # Check if order was sent
  %(prog)s cleanup --days 90       # Remove orders older than 90 days
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show order processing statistics')
    stats_parser.add_argument('--days', type=int, default=7, help='Number of days to look back (default: 7)')
    stats_parser.set_defaults(func=cmd_stats)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List recent orders')
    list_parser.add_argument('--limit', type=int, default=20, help='Maximum number of orders to show (default: 20)')
    list_parser.set_defaults(func=cmd_list)
    
    # View command
    view_parser = subparsers.add_parser('view', help='View details of a specific order')
    view_parser.add_argument('order_id', help='Order ID to view')
    view_parser.add_argument('--history', action='store_true', help='Include processing history')
    view_parser.add_argument('--show-content', action='store_true', help='Show formatted content')
    view_parser.set_defaults(func=cmd_view)
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check if an order has been sent')
    check_parser.add_argument('order_id', help='Order ID to check')
    check_parser.set_defaults(func=cmd_check)
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old records')
    cleanup_parser.add_argument('--days', type=int, default=90, help='Remove records older than this many days (default: 90)')
    cleanup_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    cleanup_parser.set_defaults(func=cmd_cleanup)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()