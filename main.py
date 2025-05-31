#!/usr/bin/env python3
"""
Email Client CLI - Tile Pro Depot Order Processor
Main entry point for the email processing application.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

from src.email_fetcher import EmailFetcher
from src.email_parser import TileProDepotParser
from src.order_formatter import OrderFormatter
from src.email_sender import EmailSender
from src.claude_processor import ClaudeProcessor
from src.order_tracker import OrderTracker
from src.laticrete_processor import LatricreteProcessor
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logger(__name__)


class EmailProcessor:
    """Main application class for processing Tile Pro Depot emails."""
    
    def __init__(self):
        """Initialize the email processor with required components."""
        self.email_fetcher = EmailFetcher(
            server=os.getenv('IMAP_SERVER'),
            port=int(os.getenv('IMAP_PORT', 993)),
            email=os.getenv('EMAIL_ADDRESS'),
            password=os.getenv('EMAIL_PASSWORD')
        )
        
        self.parser = TileProDepotParser()
        self.claude_processor = ClaudeProcessor(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.formatter = OrderFormatter()
        self.email_sender = EmailSender(
            smtp_server=os.getenv('SMTP_SERVER'),
            smtp_port=int(os.getenv('SMTP_PORT', 587)),
            username=os.getenv('SMTP_USERNAME'),
            password=os.getenv('SMTP_PASSWORD')
        )
        
        self.cs_email = os.getenv('CS_EMAIL')
        self.laticrete_cs_email = os.getenv('LATICRETE_CS_EMAIL')
        
        # Initialize order tracker
        self.order_tracker = OrderTracker(
            db_path=os.getenv('ORDER_TRACKING_DB', 'order_tracking.db')
        )
        
        # Initialize Laticrete processor
        self.laticrete_processor = LatricreteProcessor()
        
    def process_emails(self):
        """Main processing function to check and process new emails."""
        logger.info("Starting email processing cycle...")
        
        try:
            # Fetch new emails from Tile Pro Depot
            new_emails = self.email_fetcher.fetch_tile_pro_depot_emails()
            logger.info(f"Found {len(new_emails)} new emails from Tile Pro Depot")
            
            for email_data in new_emails:
                try:
                    # Check what type of products this email contains
                    product_type = self.parser.get_product_type(email_data['html'])
                    
                    if product_type == 'none':
                        logger.debug(f"Email does not contain TileWare or Laticrete products: {email_data['subject']}")
                        continue
                    
                    logger.info(f"Processing order email ({product_type} products): {email_data['subject']}")
                    
                    # Handle mixed product types
                    if product_type == 'both':
                        logger.info("Order contains both TileWare and Laticrete products, processing separately")
                        # Process TileWare products
                        self._process_tileware_order(email_data)
                        # Process Laticrete products  
                        self._process_laticrete_order(email_data)
                    elif product_type == 'tileware':
                        self._process_tileware_order(email_data)
                    elif product_type == 'laticrete':
                        self._process_laticrete_order(email_data)
                        
                except Exception as e:
                    logger.error(f"Error processing email {email_data.get('subject', 'Unknown')}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in email processing cycle: {str(e)}")
            
        logger.info("Email processing cycle completed")
    
    def _process_tileware_order(self, email_data):
        """Process TileWare products from the email."""
        try:
            # Use Claude to extract TileWare order details
            order_details = self.claude_processor.extract_order_details(
                email_data['html'], product_type="tileware"
            )
            
            if order_details and self.claude_processor.validate_extraction(order_details, "tileware"):
                order_id = order_details.get('order_id', 'Unknown')
                
                # Check if order has already been sent
                is_sent, existing_order = self.order_tracker.has_order_been_sent(f"TW-{order_id}")
                if is_sent:
                    logger.info(f"TileWare order {order_id} has already been sent on {existing_order.get('created_at')}, skipping...")
                    return
                
                # Format the order for CS team
                formatted_order = self.formatter.format_order(order_details)
                
                # Send to CS team
                success = self.email_sender.send_order_to_cs(
                    recipient=self.cs_email,
                    order_text=formatted_order,
                    original_order_id=order_id
                )
                
                if success:
                    # Track the sent order
                    if self.order_tracker.mark_order_as_sent(
                        order_id=f"TW-{order_id}",
                        email_data=email_data,
                        order_details=order_details,
                        formatted_content=formatted_order,
                        recipient=self.cs_email
                    ):
                        logger.info(f"Successfully processed and sent TileWare order {order_id}")
                    else:
                        logger.warning(f"TileWare order {order_id} sent but failed to track in database")
                else:
                    logger.error(f"Failed to send TileWare order {order_id} to CS")
            else:
                logger.warning(f"Failed to extract TileWare order details from email: {email_data['subject']}")
                
        except Exception as e:
            logger.error(f"Error processing TileWare order: {str(e)}")
    
    def _process_laticrete_order(self, email_data):
        """Process Laticrete products from the email."""
        try:
            if not self.laticrete_cs_email:
                logger.warning("LATICRETE_CS_EMAIL not configured, skipping Laticrete order processing")
                return
                
            # Use Claude to extract Laticrete order details
            order_details = self.claude_processor.extract_order_details(
                email_data['html'], product_type="laticrete"
            )
            
            if order_details and self.claude_processor.validate_extraction(order_details, "laticrete"):
                order_id = order_details.get('order_id', 'Unknown')
                
                # Check if order has already been sent
                is_sent, existing_order = self.order_tracker.has_order_been_sent(f"LAT-{order_id}")
                if is_sent:
                    logger.info(f"Laticrete order {order_id} has already been sent on {existing_order.get('created_at')}, skipping...")
                    return
                
                # Process with Laticrete processor (enriches prices, fills PDF, sends email)
                success = self.laticrete_processor.process_order(order_details)
                
                if success:
                    # Track the sent order
                    if self.order_tracker.mark_order_as_sent(
                        order_id=f"LAT-{order_id}",
                        email_data=email_data,
                        order_details=order_details,
                        formatted_content="Laticrete order with PDF attachment",
                        recipient=self.laticrete_cs_email
                    ):
                        logger.info(f"Successfully processed and sent Laticrete order {order_id}")
                    else:
                        logger.warning(f"Laticrete order {order_id} sent but failed to track in database")
                else:
                    logger.error(f"Failed to process Laticrete order {order_id}")
            else:
                logger.warning(f"Failed to extract Laticrete order details from email: {email_data['subject']}")
                
        except Exception as e:
            logger.error(f"Error processing Laticrete order: {str(e)}")


def main():
    """Main entry point for the application."""
    logger.info("Starting Email Client CLI - Tile Pro Depot Order Processor")
    
    # Display order tracking statistics
    try:
        tracker = OrderTracker()
        stats = tracker.get_statistics(days=7)
        logger.info(f"Last 7 days: {stats.get('total_orders_sent', 0)} orders sent, "
                   f"{stats.get('duplicate_attempts_blocked', 0)} duplicates blocked")
    except Exception as e:
        logger.warning(f"Could not retrieve order statistics: {e}")
    
    # Validate required environment variables
    required_vars = [
        'IMAP_SERVER', 'EMAIL_ADDRESS', 'EMAIL_PASSWORD',
        'ANTHROPIC_API_KEY', 'SMTP_SERVER', 'SMTP_USERNAME',
        'SMTP_PASSWORD', 'CS_EMAIL'
    ]
    
    # Optional but recommended for Laticrete processing
    if not os.getenv('LATICRETE_CS_EMAIL'):
        logger.warning("LATICRETE_CS_EMAIL not set - Laticrete orders will not be processed")
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Initialize processor
    processor = EmailProcessor()
    
    # Display order tracking statistics on startup
    stats = processor.order_tracker.get_statistics()
    logger.info(f"Order Tracking Statistics:")
    logger.info(f"  Total orders processed: {stats.get('total_orders', 0)}")
    logger.info(f"  Orders today: {stats.get('orders_today', 0)}")
    logger.info(f"  Orders this week: {stats.get('orders_this_week', 0)}")
    if stats.get('most_recent_order'):
        logger.info(f"  Most recent order: {stats['most_recent_order']['order_id']} at {stats['most_recent_order']['sent_timestamp']}")
    
    # Check if running in single-run mode or scheduled mode
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        logger.info("Running in single execution mode")
        processor.process_emails()
    else:
        # Set up scheduler
        scheduler = BlockingScheduler()
        interval_minutes = int(os.getenv('CHECK_INTERVAL_MINUTES', 5))
        
        logger.info(f"Setting up scheduler to run every {interval_minutes} minutes")
        
        # Run immediately on startup
        processor.process_emails()
        
        # Schedule periodic runs
        scheduler.add_job(
            processor.process_emails,
            'interval',
            minutes=interval_minutes,
            id='email_processor',
            name='Process Tile Pro Depot Emails',
            next_run_time=datetime.now()
        )
        
        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Shutting down scheduler...")
            scheduler.shutdown()
            logger.info("Application stopped")


if __name__ == "__main__":
    main()