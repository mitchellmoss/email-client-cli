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
        
    def process_emails(self):
        """Main processing function to check and process new emails."""
        logger.info("Starting email processing cycle...")
        
        try:
            # Fetch new emails from Tile Pro Depot
            new_emails = self.email_fetcher.fetch_tile_pro_depot_emails()
            logger.info(f"Found {len(new_emails)} new emails from Tile Pro Depot")
            
            for email_data in new_emails:
                try:
                    # Parse email to check if it contains TileWare products
                    if self.parser.contains_tileware_product(email_data['html']):
                        logger.info(f"Processing order email: {email_data['subject']}")
                        
                        # Use Claude to extract order details
                        order_details = self.claude_processor.extract_order_details(
                            email_data['html']
                        )
                        
                        if order_details:
                            # Format the order for CS team
                            formatted_order = self.formatter.format_order(order_details)
                            
                            # Send to CS team
                            self.email_sender.send_order_to_cs(
                                recipient=self.cs_email,
                                order_text=formatted_order,
                                original_order_id=order_details.get('order_id', 'Unknown')
                            )
                            
                            logger.info(f"Successfully processed and sent order {order_details.get('order_id')}")
                        else:
                            logger.warning(f"Failed to extract order details from email: {email_data['subject']}")
                    else:
                        logger.debug(f"Email does not contain TileWare products: {email_data['subject']}")
                        
                except Exception as e:
                    logger.error(f"Error processing email {email_data.get('subject', 'Unknown')}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in email processing cycle: {str(e)}")
            
        logger.info("Email processing cycle completed")


def main():
    """Main entry point for the application."""
    logger.info("Starting Email Client CLI - Tile Pro Depot Order Processor")
    
    # Validate required environment variables
    required_vars = [
        'IMAP_SERVER', 'EMAIL_ADDRESS', 'EMAIL_PASSWORD',
        'ANTHROPIC_API_KEY', 'SMTP_SERVER', 'SMTP_USERNAME',
        'SMTP_PASSWORD', 'CS_EMAIL'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Initialize processor
    processor = EmailProcessor()
    
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