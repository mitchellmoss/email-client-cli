#!/usr/bin/env python3
"""Simple test to see what emails are in the inbox."""

import os
from dotenv import load_dotenv
from imap_tools import MailBox
from datetime import datetime, timedelta

load_dotenv()

server = os.getenv('IMAP_SERVER')
port = int(os.getenv('IMAP_PORT', 993))
email = os.getenv('EMAIL_ADDRESS')
password = os.getenv('EMAIL_PASSWORD')

print(f"Connecting to {server}:{port} as {email}")

with MailBox(server, port).login(email, password) as mailbox:
    print("Connected successfully!")
    
    # Get emails from last 2 days
    since_date = datetime.now() - timedelta(days=2)
    
    print(f"\nSearching for emails since {since_date.date()}...")
    
    count = 0
    from imap_tools import AND
    for msg in mailbox.fetch(AND(date_gte=since_date.date())):
        count += 1
        print(f"\n--- Email #{count} ---")
        print(f"From: {msg.from_}")
        print(f"To: {msg.to}")
        print(f"Subject: {msg.subject}")
        print(f"Date: {msg.date}")
        
        # Check if it's a Tile Pro Depot order
        if "tileprodepot" in str(msg.from_).lower() or (msg.to and any("tileprodepot" in str(t).lower() for t in msg.to)):
            print("✓ This is a Tile Pro Depot related email!")
            
            # Check subject
            if "customer order" in msg.subject.lower():
                print("✓ Subject contains 'customer order'")
            
            # Check body for order pattern
            if msg.html:
                if "received the following order" in msg.html.lower():
                    print("✓ Body contains order pattern")
                else:
                    print("✗ Body doesn't contain 'received the following order'")
                    # Show first 500 chars to debug
                    print(f"Body preview: {msg.html[:500]}...")
        
        if count >= 10:
            print("\n... (showing first 10 emails only)")
            break
    
    print(f"\nTotal emails found: {count}")