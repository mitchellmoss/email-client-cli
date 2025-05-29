#!/usr/bin/env python3
"""Debug script to search for emails and understand folder structure."""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from imap_tools import MailBox, AND, OR
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger(__name__)

def debug_email_search():
    """Debug email search to find why emails aren't being detected."""
    
    server = os.getenv('IMAP_SERVER')
    port = int(os.getenv('IMAP_PORT', 993))
    email = os.getenv('EMAIL_ADDRESS')
    password = os.getenv('EMAIL_PASSWORD')
    
    logger.info(f"Connecting to {server}:{port} as {email}")
    
    try:
        with MailBox(server, port).login(email, password) as mailbox:
            logger.info("Connected successfully!")
            
            # List all folders
            logger.info("\n=== Available folders ===")
            for folder in mailbox.folder.list():
                logger.info(f"  - {folder.name}")
            
            # Check INBOX
            logger.info("\n=== Checking INBOX ===")
            mailbox.folder.set('INBOX')
            
            # Count total emails
            total_count = len(list(mailbox.fetch()))
            logger.info(f"Total emails in INBOX: {total_count}")
            
            # Search for emails from noreply@tileprodepot.com
            logger.info("\n=== Searching for emails from noreply@tileprodepot.com ===")
            count = 0
            for msg in mailbox.fetch(from_="noreply@tileprodepot.com"):
                count += 1
                logger.info(f"\nEmail #{count}:")
                logger.info(f"  From: {msg.from_}")
                logger.info(f"  To: {msg.to}")
                logger.info(f"  Subject: {msg.subject}")
                logger.info(f"  Date: {msg.date}")
                logger.info(f"  UID: {msg.uid}")
                
                # Check if subject contains order info
                if "customer order" in msg.subject.lower():
                    logger.info("  ✓ Contains 'customer order' in subject")
                
                # Check body content
                if msg.html and "You've received the following order from" in msg.html:
                    logger.info("  ✓ Contains order pattern in HTML body")
                elif msg.text and "You've received the following order from" in msg.text:
                    logger.info("  ✓ Contains order pattern in text body")
            
            if count == 0:
                logger.info("No emails found from noreply@tileprodepot.com")
                
                # Try broader search
                logger.info("\n=== Broader search for 'tileprodepot' ===")
                count = 0
                for msg in mailbox.fetch():
                    if 'tileprodepot' in str(msg.from_).lower():
                        count += 1
                        logger.info(f"\nEmail #{count}:")
                        logger.info(f"  From: {msg.from_}")
                        logger.info(f"  Subject: {msg.subject}")
                        logger.info(f"  Date: {msg.date}")
                        
                if count == 0:
                    logger.info("No emails found containing 'tileprodepot'")
            
            # Try other common folders
            other_folders = ['All Mail', 'Sent', '[Gmail]/All Mail', '[Gmail]/Sent Mail']
            for folder_name in other_folders:
                try:
                    logger.info(f"\n=== Checking {folder_name} ===")
                    mailbox.folder.set(folder_name)
                    
                    count = 0
                    for msg in mailbox.fetch(from_="noreply@tileprodepot.com"):
                        count += 1
                        if count <= 3:  # Show first 3
                            logger.info(f"\nEmail #{count}:")
                            logger.info(f"  From: {msg.from_}")
                            logger.info(f"  To: {msg.to}")
                            logger.info(f"  Subject: {msg.subject}")
                            logger.info(f"  Date: {msg.date}")
                    
                    if count > 0:
                        logger.info(f"Total found in {folder_name}: {count}")
                    else:
                        logger.info(f"No emails found in {folder_name}")
                        
                except Exception as e:
                    logger.debug(f"Folder {folder_name} not accessible: {e}")
                    
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(f"Make sure you're checking the correct email account.")
        logger.error(f"The email was sent TO: customerservice@tileprodepot.com")
        logger.error(f"You're currently checking: {email}")

if __name__ == "__main__":
    debug_email_search()