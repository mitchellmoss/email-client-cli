#!/usr/bin/env python3
"""Search for the specific order email."""

import os
from dotenv import load_dotenv
from imap_tools import MailBox, AND, OR
from datetime import datetime, timedelta

load_dotenv()

server = os.getenv('IMAP_SERVER')
port = int(os.getenv('IMAP_PORT', 993))
email = os.getenv('EMAIL_ADDRESS')
password = os.getenv('EMAIL_PASSWORD')

print(f"Connecting to {server}:{port} as {email}")

with MailBox(server, port).login(email, password) as mailbox:
    print("Connected successfully!")
    
    # Search for emails with order number 43157
    print("\nSearching for order 43157...")
    
    count = 0
    # Search in subject
    for msg in mailbox.fetch(AND(subject="43157")):
        count += 1
        print(f"\n--- Found by subject ---")
        print(f"From: {msg.from_}")
        print(f"To: {msg.to}")
        print(f"Subject: {msg.subject}")
        print(f"Date: {msg.date}")
        print(f"Folder: {mailbox.folder.get()}")
    
    if count == 0:
        print("Not found by subject search")
    
    # Try searching by body content
    print("\nSearching in all folders...")
    folders_to_check = ['INBOX', 'INBOX.Sent', 'INBOX.spam', 'INBOX.Junk', 'INBOX.Trash']
    
    for folder_name in folders_to_check:
        try:
            mailbox.folder.set(folder_name)
            print(f"\nChecking {folder_name}...")
            
            # Get emails from today
            today = datetime.now().date()
            for msg in mailbox.fetch(AND(date_gte=today)):
                if "43157" in msg.subject or (msg.html and "43157" in msg.html) or (msg.text and "43157" in msg.text):
                    print(f"\n*** FOUND IN {folder_name} ***")
                    print(f"From: {msg.from_}")
                    print(f"To: {msg.to}")
                    print(f"Subject: {msg.subject}")
                    print(f"Date: {msg.date}")
                    print(f"UID: {msg.uid}")
                    
        except Exception as e:
            print(f"Could not access {folder_name}: {e}")