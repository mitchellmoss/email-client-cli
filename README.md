# Email Client CLI - Tile Pro Depot Order Processor

An intelligent email processing agent that monitors emails from Tile Pro Depot and automatically extracts and forwards TileWare product orders to customer service.

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd email-client-cli
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your credentials

# Test connections
python src/test_connections.py

# Run
python main.py
```

## Features

- 🔍 **Automatic Email Monitoring**: Periodically checks for new emails from Tile Pro Depot
- 🤖 **Intelligent Parsing**: Uses Claude AI to extract order details from complex HTML emails
- 📦 **TileWare Product Detection**: Specifically identifies and processes orders containing TileWare products
- 📧 **Automated Forwarding**: Sends formatted orders to customer service team
- 🔄 **Duplicate Prevention**: Tracks sent orders to prevent duplicate processing
- 📊 **Comprehensive Logging**: Detailed logging for monitoring and troubleshooting
- 🗄️ **Order History**: SQLite database for tracking all processed orders

## Prerequisites

- Python 3.8 or higher
- Email account with IMAP access enabled
- Anthropic API key for Claude
- SMTP access for sending emails

## 📋 Step-by-Step Setup

### 1. Installation

Clone the repository and install dependencies:

```bash
# Clone repository
git clone <repository-url>
cd email-client-cli

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Get Required Credentials

#### A. Gmail App Password (for IMAP/SMTP)

1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Navigate to **Security** → **2-Step Verification** (must be enabled)
3. Scroll down to **App passwords**
4. Select app: **Mail**
5. Select device: **Other** (enter "Email Client CLI")
6. Click **Generate**
7. Copy the 16-character password (spaces don't matter)

#### B. Claude API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to **API Keys**
4. Click **Create Key**
5. Name it "Email Client CLI"
6. Copy the key (starts with `sk-ant-api03-`)

### 3. Configuration

Copy the environment template and configure:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Email Account Settings (IMAP)
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx  # Your 16-char app password

# Claude API Configuration
ANTHROPIC_API_KEY=sk-ant-api03-...  # Your Claude API key

# SMTP Settings (for sending emails)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com  # Same as EMAIL_ADDRESS
SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # Same as EMAIL_PASSWORD

# Recipients
CS_EMAIL=customerservice@company.com  # Where to send orders

# Processing Schedule
CHECK_INTERVAL_MINUTES=5  # How often to check for new emails

# Logging
LOG_LEVEL=INFO
LOG_FILE=email_processor.log

# Order Tracking Database
ORDER_TRACKING_DB=order_tracking.db  # Optional: customize database location
```

### 4. Verify Setup

Run the connection test to ensure everything is configured correctly:

```bash
python src/test_connections.py
```

You should see:
```
✅ All required environment variables are set!
✅ IMAP connection successful!
✅ SMTP connection successful!
✅ Claude API connection successful!
```

## Usage

### Run continuously (with scheduler):
```bash
python main.py
```

### Run once (process current emails):
```bash
python main.py --once
```

### Manage order tracking:
```bash
# View order statistics
python src/manage_orders.py stats

# List recent orders
python src/manage_orders.py list

# View specific order details
python src/manage_orders.py view ORDER_ID

# Check if an order has been sent
python src/manage_orders.py check ORDER_ID

# Clean up old orders (older than 90 days)
python src/manage_orders.py cleanup --days 90
```

## 📧 Email Requirements

The system processes emails that match ALL these criteria:

1. **From**: `noreply@tileprodepot.com`
2. **Subject**: Contains "New customer order"
3. **Body**: Contains "You've received the following order from"
4. **Products**: At least one product with "TileWare" in the name

### Example Email Format

The system expects emails like:
```
From: noreply@tileprodepot.com
Subject: [Tile Pro Depot] New customer order (43060) - May 28, 2025

You've received the following order from Tasha Waldron:

Order #43060 (May 28, 2025)

Product                                          Quantity    Price
----------------------------------------------------------------
TileWare Promessa™ Series Tee Hook (#T101-211-PC)    3     $130.20
```

## How It Works

1. **Email Fetching**: Connects to your IMAP server and searches for emails from `noreply@tileprodepot.com`
2. **Content Detection**: Checks if emails contain "New customer order" and "You've received the following order from"
3. **TileWare Detection**: Parses HTML to find products containing "TileWare"
4. **Data Extraction**: Uses Claude AI to intelligently extract:
   - Order ID
   - Customer name
   - TileWare products (name, SKU, quantity)
   - Shipping address
   - Shipping method
5. **Duplicate Check**: Verifies order hasn't been sent before using SQLite database
6. **Formatting**: Converts extracted data to CS team format
7. **Email Sending**: Sends formatted order to CS team with both plain text and HTML versions
8. **Order Tracking**: Records sent orders in database to prevent duplicate processing

## 📝 Output Format

Processed orders are sent to CS in this format:

```
Hi CS - Please place this order::::
Hi CS, please place this order -
TileWare Promessa™ Series Tee Hook - Contemporary - Polished Chrome (#T101-211-PC) x3

SHIP TO:
UPS GROUND

Tasha Waldron
40438 N Deep Lake Rd
Antioch, IL 60002

::::
```

## Project Structure

```
email-client-cli/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── .env                   # Your configuration (not in git)
├── order_tracking.db      # SQLite database for order tracking
├── CLAUDE.md              # Detailed project documentation
├── README.md              # This file
└── src/
    ├── __init__.py
    ├── email_fetcher.py   # IMAP email retrieval
    ├── email_parser.py    # HTML parsing and TileWare detection
    ├── claude_processor.py # Claude AI integration
    ├── order_formatter.py # Order formatting logic
    ├── email_sender.py    # SMTP email sending
    ├── order_tracker.py   # Order tracking and duplicate prevention
    ├── manage_orders.py   # Order management utility
    ├── test_connections.py # Connection testing utility
    └── utils/
        ├── __init__.py
        └── logger.py      # Logging configuration
```

## 🔧 Troubleshooting

### Connection Test Failed?

1. **IMAP Authentication Failed**
   - Ensure you're using an app-specific password, not your regular password
   - Check that 2FA is enabled on your Google account
   - Verify IMAP is enabled: Gmail Settings → Forwarding and POP/IMAP → Enable IMAP
   - For non-Gmail: Check your email provider's IMAP settings

2. **SMTP Authentication Failed**
   - Use the same app password as IMAP
   - Ensure "Less secure app access" is NOT the solution (use app passwords)
   - Check firewall isn't blocking port 587

3. **Claude API Failed**
   - Verify your API key starts with `sk-ant-api03-`
   - Check you have credits in your Anthropic account
   - Ensure the key has not expired

### No Emails Being Processed?

1. **Check Email Criteria**
   - Sender must be exactly `noreply@tileprodepot.com`
   - Subject must contain "New customer order"
   - Email must have "TileWare" products

2. **Check Email Location**
   - Emails must be in INBOX (not in folders)
   - Check if emails were already marked as read
   - Look in spam/junk folders

3. **Debug Mode**
   ```bash
   # Check last 7 days of emails
   python -c "from src.email_fetcher import EmailFetcher; import os; from dotenv import load_dotenv; load_dotenv(); f = EmailFetcher(os.getenv('IMAP_SERVER'), 993, os.getenv('EMAIL_ADDRESS'), os.getenv('EMAIL_PASSWORD')); print(f'Found {len(f.fetch_tile_pro_depot_emails(7))} emails')"
   ```

### Order Tracking Issues?

1. **Order Already Sent Message**
   - This is normal - the system prevents duplicate processing
   - Check order details: `python src/manage_orders.py view ORDER_ID`
   - View all sent orders: `python src/manage_orders.py list`

2. **Database Errors**
   - Ensure write permissions on `order_tracking.db`
   - Check disk space
   - Database corrupted? Delete and let it recreate (orders will need reprocessing)

3. **Check Order Status**
   ```bash
   # Check if specific order was sent
   python src/manage_orders.py check ORDER_ID
   
   # View order statistics
   python src/manage_orders.py stats
   ```

## 📊 Monitoring

The application creates detailed logs in `email_processor.log`:

```bash
# View real-time logs
tail -f email_processor.log

# Today's processed orders
grep "Successfully processed" email_processor.log | grep "$(date +%Y-%m-%d)"

# View errors only
grep ERROR email_processor.log

# Count processed orders
grep -c "Successfully processed and sent order" email_processor.log
```

## 💰 Cost Estimation

- **Claude Haiku** (default): ~$0.01 per 100 emails
- **Email Processing**: ~500 emails/month = $0.05/month
- **Monitoring**: Check your usage at [Anthropic Console](https://console.anthropic.com/)

## 🔒 Security Best Practices

1. **Never commit `.env` to git** (already in `.gitignore`)
2. **Use app-specific passwords** (not your regular email password)
3. **Rotate API keys** every 90 days
4. **Monitor logs** for suspicious activity
5. **Restrict CS_EMAIL** to internal addresses only

## 📈 Monitoring & Maintenance

### Common Maintenance Tasks

1. **Clear old logs** (monthly):
   ```bash
   mv email_processor.log email_processor.log.old
   ```

2. **Update dependencies** (quarterly):
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **Check API usage** (monthly):
   - Visit [Anthropic Console](https://console.anthropic.com/)
   - Review usage and costs

## Support

For issues:
1. Check `email_processor.log` for errors
2. Run `python src/test_connections.py` to verify setup
3. Review `CLAUDE.md` for technical details
4. Create an issue with:
   - Error messages from logs
   - Output of connection test
   - Sanitized `.env` (remove passwords/keys)