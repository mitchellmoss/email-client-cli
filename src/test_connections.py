#!/usr/bin/env python3
"""Test connections for email client CLI."""

import os
import sys
from dotenv import load_dotenv
from anthropic import Anthropic

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.email_fetcher import EmailFetcher
from src.email_sender import EmailSender
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()
logger = setup_logger(__name__)


def test_imap_connection():
    """Test IMAP connection."""
    print("\n🔍 Testing IMAP Connection...")
    
    try:
        fetcher = EmailFetcher(
            server=os.getenv('IMAP_SERVER'),
            port=int(os.getenv('IMAP_PORT', 993)),
            email=os.getenv('EMAIL_ADDRESS'),
            password=os.getenv('EMAIL_PASSWORD')
        )
        
        if fetcher.test_connection():
            print("✅ IMAP connection successful!")
            
            # Try to fetch recent emails
            emails = fetcher.fetch_tile_pro_depot_emails(since_days=7)
            print(f"📧 Found {len(emails)} Tile Pro Depot emails in the last 7 days")
            
            return True
        else:
            print("❌ IMAP connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ IMAP test error: {e}")
        return False


def test_smtp_connection():
    """Test SMTP connection."""
    print("\n📤 Testing SMTP Connection...")
    
    try:
        sender = EmailSender(
            smtp_server=os.getenv('SMTP_SERVER'),
            smtp_port=int(os.getenv('SMTP_PORT', 587)),
            username=os.getenv('SMTP_USERNAME'),
            password=os.getenv('SMTP_PASSWORD')
        )
        
        if sender.test_connection():
            print("✅ SMTP connection successful!")
            return True
        else:
            print("❌ SMTP connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ SMTP test error: {e}")
        return False


def test_claude_api():
    """Test Claude API connection."""
    print("\n🤖 Testing Claude API Connection...")
    
    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        # Send a simple test message
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": "Say 'API connection successful' and nothing else."
                }
            ]
        )
        
        result = response.content[0].text
        if "API connection successful" in result:
            print("✅ Claude API connection successful!")
            return True
        else:
            print("❌ Claude API returned unexpected response")
            return False
            
    except Exception as e:
        print(f"❌ Claude API test error: {e}")
        return False


def check_environment_variables():
    """Check if all required environment variables are set."""
    print("\n🔧 Checking Environment Variables...")
    
    required_vars = [
        'IMAP_SERVER', 'IMAP_PORT', 'EMAIL_ADDRESS', 'EMAIL_PASSWORD',
        'ANTHROPIC_API_KEY', 'SMTP_SERVER', 'SMTP_PORT', 
        'SMTP_USERNAME', 'SMTP_PASSWORD', 'CS_EMAIL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            print(f"❌ Missing: {var}")
        else:
            # Show masked value
            value = os.getenv(var)
            if 'PASSWORD' in var or 'API_KEY' in var:
                masked = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '*' * len(value)
                print(f"✅ {var}: {masked}")
            else:
                print(f"✅ {var}: {value}")
    
    if missing_vars:
        print(f"\n❌ Missing {len(missing_vars)} required environment variables")
        return False
    else:
        print("\n✅ All required environment variables are set!")
        return True


def main():
    """Run all connection tests."""
    print("=" * 50)
    print("Email Client CLI - Connection Test")
    print("=" * 50)
    
    # Check environment variables
    env_ok = check_environment_variables()
    
    if not env_ok:
        print("\n⚠️  Please set all required environment variables in .env file")
        sys.exit(1)
    
    # Run connection tests
    results = {
        'IMAP': test_imap_connection(),
        'SMTP': test_smtp_connection(),
        'Claude API': test_claude_api()
    }
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("=" * 50)
    
    all_passed = True
    for service, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{service}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! The email client is ready to use.")
        print("\nRun the application with:")
        print("  python main.py        # Run with scheduler")
        print("  python main.py --once # Run once")
    else:
        print("\n⚠️  Some tests failed. Please check your configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()