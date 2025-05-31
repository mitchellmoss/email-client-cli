#!/usr/bin/env python3
"""Test if email signature is loading from environment."""

import os
from dotenv import load_dotenv

# Reload environment variables
load_dotenv(override=True)

# Check if signature is loaded
signature = os.getenv('EMAIL_SIGNATURE_TEXT', 'NOT FOUND')

print("Email Signature Test")
print("=" * 50)
print(f"Signature loaded: {'Yes' if signature != 'NOT FOUND' else 'No'}")
print(f"Signature length: {len(signature)} characters")
print(f"First 200 chars: {signature[:200]}...")
print("=" * 50)