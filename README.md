# Email Client CLI - Tile Pro Depot Order Processor

An intelligent email processing system that monitors emails from Tile Pro Depot and automatically processes customer orders for TileWare and Laticrete products.

## 📑 Table of Contents

- [Key Features](#-key-features)
- [Quick Start](#-quick-start)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Usage](#-usage)
- [How It Works](#-how-it-works)
- [Output Formats](#-output-formats)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [Monitoring & Logs](#-monitoring--logs)
- [Cost Estimation](#-cost-estimation)
- [Security](#-security-best-practices)
- [Maintenance](#️-maintenance)
- [Support](#-support)

## ✨ Key Features

- 📧 **Automated Email Monitoring** - Continuously monitors inbox for new Tile Pro Depot orders
- 🤖 **AI-Powered Extraction** - Uses Claude AI to intelligently parse complex order emails
- 📦 **Dual Product Support** - Handles both TileWare and Laticrete product orders differently
- 📄 **PDF Order Forms** - Automatically fills Laticrete PDF forms with order details
- 💰 **Price List Integration** - Cross-references Laticrete products with Excel price list
- 🔄 **Duplicate Prevention** - Tracks processed orders to avoid sending duplicates
- 🌐 **Web Admin Panel** - Modern web interface for monitoring and management
- 📊 **Real-time Dashboard** - Monitor system status, view statistics, and manage orders

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd email-client-cli

# 2. Copy and configure environment
cp .env.example .env
# Edit .env with your credentials (see Configuration section)

# 3. Test your setup
python src/test_connections.py

# 4. Start all services with one command!
./start_all.sh      # Mac/Linux
python start_all.py # Cross-platform (recommended)
start_all.bat       # Windows
```

This automatically starts:
- ✅ Email processor (monitors and processes orders)
- ✅ Admin backend API (http://localhost:8000)
- ✅ Admin frontend UI (http://localhost:5173)

**Default login**: `admin@example.com` / `changeme`

## 📋 Prerequisites

- **Python 3.8+** - Required for the email processor
- **Node.js 16+** - Required for the admin panel (optional)
- **Email account** with IMAP access enabled
- **Anthropic API key** for Claude AI
- **Gmail/SMTP** account for sending emails

## 📦 Installation

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd email-client-cli

# Create and activate virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate    # Mac/Linux
# or
venv\Scripts\activate       # Windows

# Install Python dependencies
pip install -r requirements.txt

# Optional: Install admin panel dependencies
cd admin_panel/frontend && npm install && cd ../..
```

### Step 2: Get Required Credentials

#### Gmail App Password (Required for IMAP/SMTP)

1. **Enable 2-Factor Authentication**:
   - Go to [Google Account Settings](https://myaccount.google.com/)
   - Navigate to **Security** → **2-Step Verification**
   - Turn on 2-Step Verification

2. **Generate App Password**:
   - In Security settings, find **App passwords**
   - Select app: **Mail**
   - Select device: **Other** (name it "Email Client CLI")
   - Click **Generate**
   - Save the 16-character password (spaces don't matter)

#### Claude API Key

1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to **API Keys**
4. Click **Create Key**
5. Name it "Email Client CLI"
6. Copy the key (starts with `sk-ant-api03-`)

### Step 3: Configuration

```bash
# Copy the example configuration
cp .env.example .env

# Edit .env with your favorite editor
nano .env  # or vim, code, etc.
```

Configure your `.env` file:

```env
# === Email Reading (IMAP) ===
IMAP_SERVER=imap.gmail.com          # Gmail users keep this
IMAP_PORT=993                       # Standard IMAP SSL port
EMAIL_ADDRESS=your-email@gmail.com  # Your monitoring email
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx  # 16-char app password from Step 2

# === Claude AI ===
ANTHROPIC_API_KEY=sk-ant-api03-...  # Your Claude API key from Step 2

# === Email Sending (SMTP) ===
SMTP_SERVER=smtp.gmail.com          # Gmail users keep this
SMTP_PORT=587                       # Standard SMTP TLS port
SMTP_USERNAME=your-email@gmail.com  # Usually same as EMAIL_ADDRESS
SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # Usually same as EMAIL_PASSWORD

# === Recipients ===
CS_EMAIL=customerservice@company.com         # TileWare orders go here
LATICRETE_CS_EMAIL=laticrete-cs@company.com # Laticrete orders go here

# === Processing Options ===
CHECK_INTERVAL_MINUTES=5            # How often to check emails (default: 5)
LOG_LEVEL=INFO                      # DEBUG, INFO, WARNING, ERROR
LOG_FILE=email_processor.log        # Where to save logs
```

### Step 4: Verify Setup

```bash
# Test all connections
python src/test_connections.py
```

✅ **Success looks like**:
```
========================================
🔧 Email Client Connection Test
========================================

Checking environment variables...
✅ All required environment variables are set!

Testing IMAP connection...
✅ IMAP connection successful!
   Connected to: imap.gmail.com:993
   Authenticated as: your-email@gmail.com

Testing SMTP connection...
✅ SMTP connection successful!
   Connected to: smtp.gmail.com:587
   Authenticated as: your-email@gmail.com

Testing Claude API connection...
✅ Claude API connection successful!
   Using model: claude-3-haiku-20240307

========================================
✅ All connections successful! You're ready to go!
========================================
```

❌ **If any test fails**, see the Troubleshooting section below.

## 🚀 Usage

### Quick Start (Recommended)

Use the all-in-one startup script to launch everything:

```bash
# Cross-platform (recommended)
python start_all.py

# Platform-specific alternatives
./start_all.sh    # Mac/Linux
start_all.bat     # Windows
```

This automatically:
- ✅ Creates virtual environments if needed
- ✅ Installs all dependencies
- ✅ Starts the email processor
- ✅ Launches the admin panel
- ✅ Opens your browser to the dashboard

**To stop all services**: Press `Ctrl+C` in the terminal

### Manual Operation

#### Email Processor Only
```bash
# Run continuously (checks every 5 minutes)
python main.py

# Run once and exit
python main.py --once

# Run with custom interval
python main.py --interval 10  # Check every 10 minutes
```

#### Admin Panel Only
```bash
# Terminal 1: Backend API
cd admin_panel/backend
./run_dev.sh

# Terminal 2: Frontend UI
cd admin_panel/frontend
npm run dev
```

### 🌐 Web Admin Panel

Access at: **http://localhost:5173**

**Default credentials**:
- Email: `admin@example.com`
- Password: `changeme`

**Features**:
- 📊 **Dashboard** - Real-time system status and statistics
- 📦 **Orders** - View, search, and resend processed orders
- 🔗 **Product Matching** - Map Laticrete products to SKUs
- ⚙️ **Settings** - Configure email servers and templates
- 📝 **Logs** - View live system logs

### 📋 Order Management CLI

```bash
# View statistics
python src/manage_orders.py stats

# List recent orders (last 10)
python src/manage_orders.py list

# Search for specific order
python src/manage_orders.py view 43060

# Check if order was sent
python src/manage_orders.py check 43060

# Clean old orders (>90 days)
python src/manage_orders.py cleanup --days 90

# Export orders to CSV
python src/manage_orders.py export --output orders.csv
```

## 📧 How It Works

### Email Processing Flow

1. **Email Detection** - Monitors inbox for emails from Tile Pro Depot
2. **Content Parsing** - Extracts order information using AI
3. **Product Routing**:
   - **TileWare** → Formats and sends text email to CS team
   - **Laticrete** → Fills PDF form and sends with attachment
4. **Duplicate Check** - Prevents sending the same order twice
5. **Order Tracking** - Records in database for history

### Email Criteria

The system only processes emails that match **ALL** of these:

✉️ **From**: `noreply@tileprodepot.com`  
📋 **Subject**: Contains "New customer order"  
📝 **Body**: Contains "You've received the following order from"  
📦 **Products**: At least one "TileWare" or "Laticrete" product

### Example Order Email
```
From: noreply@tileprodepot.com
Subject: [Tile Pro Depot] New customer order (43060)

You've received the following order from Tasha Waldron:

Order #43060 (May 28, 2025)

Product                                    Quantity    Price
----------------------------------------------------------
TileWare Promessa™ Series Tee Hook (#T101-211-PC)  3   $130.20
LATICRETE 254 Platinum (#0254-0050)                2   $45.00

Shipping: UPS GROUND
Total: $175.20
```


## 📤 Output Formats

### TileWare Orders
Sent as formatted text email to `CS_EMAIL`:

```
Subject: Order #43060 - Tasha Waldron

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

### Laticrete Orders
Sent to `LATICRETE_CS_EMAIL` with:
- 📧 Email with order summary
- 📎 PDF attachment containing:
  - Filled order form
  - Customer details
  - Product info with prices from Excel sheet
  - Shipping information

## 📁 Project Structure

```
email-client-cli/
├── main.py                    # Main entry point
├── start_all.py              # Cross-platform launcher
├── requirements.txt          # Python dependencies
├── .env.example             # Configuration template
├── .env                     # Your settings (gitignored)
├── order_tracking.db        # Order history database
│
├── admin_panel/             # Web interface
│   ├── backend/            # FastAPI REST API
│   └── frontend/           # React dashboard
│
├── resources/laticrete/     # Laticrete files
│   ├── lat_blank_orderform.pdf
│   └── lat_price_list.xlsx
│
└── src/                     # Core modules
    ├── email_fetcher.py    # IMAP email reader
    ├── email_parser.py     # HTML parser
    ├── claude_processor.py # AI integration
    ├── order_formatter.py  # Order formatting
    ├── email_sender.py     # SMTP sender
    ├── order_tracker.py    # Duplicate prevention
    ├── laticrete_processor.py
    ├── manage_orders.py    # CLI management
    └── test_connections.py # Setup verification
```

## 🔧 Troubleshooting

### Connection Test Failures

#### ❌ IMAP Authentication Failed
```
Error: [AUTHENTICATIONFAILED] Invalid credentials
```
**Solutions**:
- ✅ Use app password, not regular password
- ✅ Enable 2FA on Google Account first
- ✅ Enable IMAP: Gmail Settings → Forwarding and POP/IMAP
- ✅ Check EMAIL_ADDRESS matches exactly
- ✅ For Outlook: Use `outlook.office365.com` as IMAP_SERVER

#### ❌ SMTP Authentication Failed
```
Error: (535, b'5.7.8 Username and Password not accepted')
```
**Solutions**:
- ✅ Use same app password as IMAP
- ✅ Don't use "Less secure apps" - use app passwords
- ✅ Check port 587 isn't blocked by firewall
- ✅ Verify SMTP_USERNAME matches EMAIL_ADDRESS

#### ❌ Claude API Failed
```
Error: Invalid API Key
```
**Solutions**:
- ✅ Key should start with `sk-ant-api03-`
- ✅ Check for extra spaces or quotes
- ✅ Verify credits at [console.anthropic.com](https://console.anthropic.com)
- ✅ Generate new key if expired

### Email Processing Issues

#### 📧 No Emails Found
```bash
# Debug: Check for emails in last 7 days
python src/debug_email_search.py

# Check specific folder
python src/test_inbox.py
```

**Common causes**:
- Emails in spam/promotions folder
- Already marked as read
- Wrong sender address in filter
- No recent orders

#### 🔄 "Order already sent" Message
This is **normal behavior** - prevents duplicates!

```bash
# View order details
python src/manage_orders.py view 43060

# Force resend (use carefully)
python src/manage_orders.py resend 43060
```

#### ❌ Laticrete PDF Not Filling
**Check**:
- `resources/laticrete/lat_blank_orderform.pdf` exists
- `resources/laticrete/lat_price_list.xlsx` has correct columns
- Product names match between email and price list

### Admin Panel Issues

#### 🌐 Can't Access http://localhost:5173
- Check both backend and frontend are running
- Try http://127.0.0.1:5173 instead
- Verify no other app using ports 5173 or 8000
- Check firewall settings

#### 🔑 Can't Login
- Default: `admin@example.com` / `changeme`
- Clear browser cache/cookies
- Check backend is running on port 8000

## 📊 Monitoring & Logs

### View Logs
```bash
# Real-time monitoring
tail -f email_processor.log

# Today's orders
grep "Successfully processed" email_processor.log | grep "$(date +%Y-%m-%d)"

# Error tracking
grep ERROR email_processor.log

# Order count
grep -c "Successfully processed" email_processor.log
```

### Log Levels
- **DEBUG**: Detailed processing steps
- **INFO**: Normal operations
- **WARNING**: Non-critical issues  
- **ERROR**: Failed processing

## 💰 Cost Estimation

| Usage | Emails/Month | Est. Cost |
|-------|--------------|-----------|
| Light | 100 | $0.01 |
| Normal | 500 | $0.05 |
| Heavy | 2000 | $0.20 |

Using Claude 3 Haiku (most cost-effective)

## 🔒 Security Best Practices

1. **Environment Files**
   - Never commit `.env` to version control
   - Use `.env.example` as template only

2. **Credentials**
   - Use app-specific passwords only
   - Rotate API keys every 90 days
   - Monitor for unusual activity

3. **Access Control**
   - Restrict CS_EMAIL to internal domains
   - Use strong admin panel password
   - Enable HTTPS in production

## 🛠️ Maintenance

### Daily
- Monitor error logs
- Check processing status

### Weekly  
- Review order statistics
- Verify email delivery

### Monthly
```bash
# Rotate logs
mv email_processor.log email_processor.log.$(date +%Y%m)

# Clean old orders
python src/manage_orders.py cleanup --days 90

# Check API usage
# Visit console.anthropic.com
```

### Quarterly
```bash
# Update dependencies
pip install --upgrade -r requirements.txt
cd admin_panel/frontend && npm update

# Update Laticrete price list if needed
# Replace resources/laticrete/lat_price_list.xlsx
```

## 📚 Additional Resources

- **Technical Documentation**: See `CLAUDE.md` for implementation details
- **API Documentation**: http://localhost:8000/docs (when running)
- **Anthropic Console**: https://console.anthropic.com
- **Gmail App Passwords**: https://myaccount.google.com/apppasswords

## 🤝 Support

Need help? Follow these steps:

1. **Check the logs**:
   ```bash
   tail -n 50 email_processor.log
   ```

2. **Run diagnostics**:
   ```bash
   python src/test_connections.py
   python src/manage_orders.py stats
   ```

3. **Common fixes**:
   - Restart all services: `python start_all.py`
   - Clear browser cache for admin panel
   - Regenerate app password if authentication fails

4. **Report an issue** with:
   - Error messages from logs
   - Output of `test_connections.py`
   - Your `.env` (remove passwords!)
   - Steps to reproduce

---

Built with ❤️ using Python, FastAPI, React, and Claude AI