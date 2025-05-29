#!/usr/bin/env python3
"""Test processing one specific email."""

import os
from dotenv import load_dotenv
from imap_tools import MailBox, AND
from datetime import datetime

load_dotenv()

server = os.getenv('IMAP_SERVER')
port = int(os.getenv('IMAP_PORT', 993))
email = os.getenv('EMAIL_ADDRESS')
password = os.getenv('EMAIL_PASSWORD')

print(f"Connecting to {server}:{port} as {email}")

with MailBox(server, port).login(email, password) as mailbox:
    print("Connected successfully!")
    
    # Get one of the order emails
    for msg in mailbox.fetch(AND(uid="2764")):  # The last one we found
        print(f"\n=== Testing Email ===")
        print(f"From: {msg.from_}")
        print(f"To: {msg.to}")
        print(f"Subject: {msg.subject}")
        print(f"Date: {msg.date}")
        
        # Test subject matching
        subject_lower = msg.subject.lower()
        print(f"\nSubject lowercase: {subject_lower}")
        print(f"Contains 'new customer order': {'new customer order' in subject_lower}")
        
        # Test body content
        html_content = msg.html or ""
        text_content = msg.text or ""
        
        print(f"\nHTML content length: {len(html_content)}")
        print(f"Text content length: {len(text_content)}")
        
        # Check for order patterns
        patterns = [
            "You've received the following order from",
            "You've received the following order from",  
            "Youâ€™ve received the following order from",
            "received the following order"
        ]
        
        for pattern in patterns:
            in_html = pattern in html_content
            in_text = pattern in text_content
            in_html_lower = pattern.lower() in html_content.lower()
            print(f"\nPattern '{pattern}':")
            print(f"  In HTML: {in_html}")
            print(f"  In Text: {in_text}")
            print(f"  In HTML (case-insensitive): {in_html_lower}")
        
        # Show a snippet of the content
        if html_content:
            start = html_content.lower().find("received")
            if start != -1:
                print(f"\nHTML snippet around 'received': ...{html_content[max(0, start-50):start+200]}...")
        
        break