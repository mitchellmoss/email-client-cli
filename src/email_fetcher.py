"""IMAP email fetcher for retrieving Tile Pro Depot emails."""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from imap_tools import MailBox, AND, OR
from email.header import decode_header
import logging

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class EmailFetcher:
    """Fetches emails from IMAP server with filtering for Tile Pro Depot orders."""
    
    def __init__(self, server: str, port: int, email: str, password: str):
        """
        Initialize the email fetcher.
        
        Args:
            server: IMAP server hostname
            port: IMAP server port
            email: Email address for authentication
            password: Password or app password for authentication
        """
        self.server = server
        self.port = port
        self.email = email
        self.password = password
        self._last_check = None
        
    def _decode_header_value(self, value: str) -> str:
        """Decode email header values properly."""
        if not value:
            return ""
            
        decoded_parts = []
        for part, encoding in decode_header(value):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(encoding or 'utf-8'))
                except:
                    decoded_parts.append(part.decode('utf-8', errors='ignore'))
            else:
                decoded_parts.append(str(part))
        return ' '.join(decoded_parts)
        
    def fetch_tile_pro_depot_emails(self, since_days: int = 1) -> List[Dict]:
        """
        Fetch emails from Tile Pro Depot.
        
        Args:
            since_days: Number of days to look back for emails
            
        Returns:
            List of email dictionaries with parsed content
        """
        emails = []
        
        try:
            # Connect to mailbox
            with MailBox(self.server, self.port).login(self.email, self.password) as mailbox:
                logger.info(f"Connected to {self.server} as {self.email} (read-only mode)")
                
                # Calculate date range
                since_date = datetime.now() - timedelta(days=since_days)
                
                # Search criteria for Tile Pro Depot emails
                # Use OR to catch both direct emails and forwarded emails
                criteria = AND(
                    OR(
                        from_="noreply@tileprodepot.com",
                        to="customerservice@tileprodepot.com"
                    ),
                    date_gte=since_date.date()
                )
                
                # Fetch matching emails without marking as read
                for msg in mailbox.fetch(criteria, mark_seen=False):
                    try:
                        # Check if subject contains "New customer order"
                        subject = self._decode_header_value(msg.subject)
                        logger.debug(f"Checking email - From: {msg.from_}, To: {msg.to}, Subject: {subject}")
                        
                        if "new customer order" not in subject.lower():
                            logger.debug(f"Skipping email - subject doesn't contain 'new customer order': {subject}")
                            continue
                            
                        # Extract order number from subject if present
                        order_match = re.search(r'\((\d+)\)', subject)
                        order_id = order_match.group(1) if order_match else None
                        
                        # Get email content
                        html_content = msg.html or ""
                        text_content = msg.text or ""
                        
                        # Check if email contains the expected pattern
                        # Use case-insensitive search for better matching
                        html_lower = html_content.lower()
                        text_lower = text_content.lower()
                        
                        if "received the following order" in html_lower or \
                           "received the following order" in text_lower:
                            
                            email_data = {
                                'uid': msg.uid,
                                'subject': subject,
                                'from': msg.from_,
                                'date': msg.date,
                                'order_id': order_id,
                                'html': html_content,
                                'text': text_content,
                                'has_attachments': len(msg.attachments) > 0
                            }
                            
                            emails.append(email_data)
                            logger.info(f"Found Tile Pro Depot order email: {subject}")
                        
                    except Exception as e:
                        logger.error(f"Error processing email: {e}")
                        continue
                
                logger.info(f"Fetched {len(emails)} Tile Pro Depot order emails")
                
        except Exception as e:
            logger.error(f"Error connecting to mailbox: {e}")
            raise
            
        return emails
    
    def fetch_unread_tile_pro_depot_emails(self) -> List[Dict]:
        """
        Fetch only unread emails from Tile Pro Depot.
        
        Returns:
            List of unread email dictionaries
        """
        emails = []
        
        try:
            with MailBox(self.server, self.port).login(self.email, self.password) as mailbox:
                logger.info(f"Connected to {self.server} for unread emails")
                
                # Search for unread emails from Tile Pro Depot
                # Use OR to catch both direct emails and forwarded emails
                criteria = AND(
                    OR(
                        from_="noreply@tileprodepot.com",
                        to="customerservice@tileprodepot.com"
                    ),
                    seen=False
                )
                
                for msg in mailbox.fetch(criteria, mark_seen=False):
                    try:
                        subject = self._decode_header_value(msg.subject)
                        if "new customer order" not in subject.lower():
                            continue
                            
                        order_match = re.search(r'\((\d+)\)', subject)
                        order_id = order_match.group(1) if order_match else None
                        
                        html_content = msg.html or ""
                        text_content = msg.text or ""
                        
                        # Check if email contains the expected pattern
                        # Use case-insensitive search for better matching
                        html_lower = html_content.lower()
                        text_lower = text_content.lower()
                        
                        if "received the following order" in html_lower or \
                           "received the following order" in text_lower:
                            
                            email_data = {
                                'uid': msg.uid,
                                'subject': subject,
                                'from': msg.from_,
                                'date': msg.date,
                                'order_id': order_id,
                                'html': html_content,
                                'text': text_content,
                                'has_attachments': len(msg.attachments) > 0
                            }
                            
                            emails.append(email_data)
                            logger.info(f"Found unread order email: {subject}")
                            
                            # Mark as seen after successful processing
                            mailbox.flag(msg.uid, ['\\Seen'], True)
                        
                    except Exception as e:
                        logger.error(f"Error processing unread email: {e}")
                        continue
                
                logger.info(f"Fetched {len(emails)} unread Tile Pro Depot emails")
                
        except Exception as e:
            logger.error(f"Error fetching unread emails: {e}")
            raise
            
        return emails
    
    def test_connection(self) -> bool:
        """
        Test the IMAP connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with MailBox(self.server, self.port).login(self.email, self.password) as mailbox:
                # Try to select INBOX
                mailbox.folder.set('INBOX')
                logger.info("IMAP connection test successful")
                return True
        except Exception as e:
            logger.error(f"IMAP connection test failed: {e}")
            return False