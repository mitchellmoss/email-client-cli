"""Email sender module for forwarding processed orders."""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, List, Dict
import time
import logging

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class EmailSender:
    """Send formatted orders via SMTP."""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
        """
        Initialize email sender.
        
        Args:
            smtp_server: SMTP server hostname
            smtp_port: SMTP server port
            username: Email username for authentication
            password: Email password or app password
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_address = username
        
    def send_order_to_cs(self, recipient: str, order_text: str, 
                        original_order_id: str = "Unknown") -> bool:
        """
        Send formatted order to CS team.
        
        Args:
            recipient: CS team email address
            order_text: Formatted order text
            original_order_id: Original order ID for subject line
            
        Returns:
            True if sent successfully, False otherwise
        """
        subject = f"TileWare Order #{original_order_id} - Action Required"
        
        # Create email message
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = self.from_address
        message['To'] = recipient
        message['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        
        # Add plain text part
        text_part = MIMEText(order_text, 'plain')
        message.attach(text_part)
        
        # Also create HTML version for better formatting
        html_content = self._create_html_version(order_text, original_order_id)
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)
        
        # Send with retry logic
        return self._send_with_retry(recipient, message)
    
    def _create_html_version(self, order_text: str, order_id: str) -> str:
        """Create HTML version of the order for better email formatting."""
        # Escape HTML and convert line breaks
        lines = order_text.split('\n')
        html_lines = []
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .order-container {{ 
                    background-color: #f8f9fa; 
                    padding: 20px; 
                    border-radius: 8px; 
                    margin: 20px 0;
                }}
                .order-header {{ 
                    background-color: #007bff; 
                    color: white; 
                    padding: 10px 20px; 
                    border-radius: 8px 8px 0 0; 
                    margin: -20px -20px 20px -20px;
                }}
                .product {{ 
                    background-color: white; 
                    padding: 10px; 
                    margin: 10px 0; 
                    border-left: 4px solid #007bff;
                }}
                .shipping {{ 
                    background-color: #e9ecef; 
                    padding: 15px; 
                    margin: 20px 0; 
                    border-radius: 4px;
                }}
                .shipping-method {{ 
                    font-weight: bold; 
                    color: #007bff; 
                    margin: 10px 0;
                }}
                .footer {{ 
                    margin-top: 30px; 
                    padding-top: 20px; 
                    border-top: 1px solid #dee2e6; 
                    font-size: 12px; 
                    color: #6c757d;
                }}
            </style>
        </head>
        <body>
            <div class="order-container">
                <div class="order-header">
                    <h2>TileWare Order #{order_id}</h2>
                </div>
                <div class="content">
        """
        
        in_shipping = False
        for line in lines:
            if line.startswith("Hi CS"):
                html += f"<p><strong>{line}</strong></p>"
            elif line.strip() == "SHIP TO:":
                html += '<div class="shipping"><h3>Shipping Information</h3>'
                in_shipping = True
            elif line.strip() == "::::":
                if in_shipping:
                    html += '</div>'
                break
            elif line.strip() and not line.startswith("Hi CS"):
                if in_shipping:
                    if line.isupper():  # Shipping method
                        html += f'<p class="shipping-method">{line}</p>'
                    else:
                        html += f'<p>{line}</p>'
                else:
                    # Product line
                    if ' x' in line and ('TileWare' in line or '#' in line):
                        html += f'<div class="product">{line}</div>'
                    else:
                        html += f'<p>{line}</p>'
        
        html += """
                </div>
                <div class="footer">
                    <p>This order was automatically processed from Tile Pro Depot.</p>
                    <p>Please process this TileWare order as soon as possible.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _send_with_retry(self, recipient: str, message: MIMEMultipart, 
                        max_retries: int = 3) -> bool:
        """
        Send email with retry logic.
        
        Args:
            recipient: Email recipient
            message: Email message to send
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if sent successfully, False otherwise
        """
        for attempt in range(max_retries):
            try:
                # Create SSL context
                context = ssl.create_default_context()
                
                # Connect to server based on port
                if self.smtp_port == 465:
                    # Use SMTP_SSL for port 465
                    with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                        server.login(self.username, self.password)
                        
                        # Send email
                        server.send_message(message)
                        
                        logger.info(f"Successfully sent order email to {recipient}")
                        return True
                else:
                    # Use STARTTLS for other ports (587, 25)
                    with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                        server.starttls(context=context)
                        server.login(self.username, self.password)
                        
                        # Send email
                        server.send_message(message)
                        
                        logger.info(f"Successfully sent order email to {recipient}")
                        return True
                    
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP authentication failed: {e}")
                return False  # Don't retry auth errors
                
            except smtplib.SMTPException as e:
                logger.error(f"SMTP error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Unexpected error sending email: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    
        logger.error(f"Failed to send email after {max_retries} attempts")
        return False
    
    def test_connection(self) -> bool:
        """
        Test SMTP connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            context = ssl.create_default_context()
            
            if self.smtp_port == 465:
                # Use SMTP_SSL for port 465
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                    server.login(self.username, self.password)
            else:
                # Use STARTTLS for other ports
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(self.username, self.password)
                
            logger.info("SMTP connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False
    
    def send_batch_orders(self, recipient: str, orders: List[Dict[str, str]]) -> int:
        """
        Send multiple orders in a batch.
        
        Args:
            recipient: CS team email address
            orders: List of order dictionaries with 'text' and 'id' keys
            
        Returns:
            Number of successfully sent orders
        """
        sent_count = 0
        
        for order in orders:
            if self.send_order_to_cs(recipient, order['text'], order.get('id', 'Unknown')):
                sent_count += 1
                # Small delay between emails to avoid rate limiting
                time.sleep(1)
                
        logger.info(f"Sent {sent_count} out of {len(orders)} orders")
        return sent_count