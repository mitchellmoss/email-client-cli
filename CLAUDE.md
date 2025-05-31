# Email Client CLI - Tile Pro Depot Order Processor

## Project Overview
An intelligent email processing agent that monitors emails from Tile Pro Depot and automatically:
- Extracts and forwards TileWare product orders to customer service
- Extracts Laticrete product orders, cross-references pricing, fills PDF order forms, and sends to Laticrete CS team

## Key Features
- Periodic IMAP email fetching (not SMTP - SMTP is for sending only)
- Intelligent email parsing using Claude API
- Automatic order extraction and formatting
- Dual product support: TileWare and Laticrete
- Laticrete price list cross-referencing
- PDF order form generation for Laticrete orders
- Email forwarding with formatted order details or PDF attachments
- Comprehensive error handling and retry logic

## Architecture

### 1. Email Fetching Module (`src/email_fetcher.py`)
- **Protocol**: IMAP (Internet Message Access Protocol) for reading emails
- **Features**:
  - Connects to any IMAP server (Gmail, Outlook, etc.)
  - Filters emails by sender (`noreply@tileprodepot.com`)
  - Searches for "New customer order" in subject
  - Supports both read/unread email tracking
  - Implements connection pooling for efficiency

### 2. Email Parser Module (`src/email_parser.py`)
- **Purpose**: Extract TileWare and Laticrete products from HTML emails
- **Features**:
  - BeautifulSoup4 for HTML parsing
  - Pattern matching for TileWare and Laticrete products
  - Product type detection (tileware, laticrete, both, none)
  - Extracts basic order information
  - Validates order data structure

### 3. Claude API Integration (`src/claude_processor.py`)
- **Model**: Claude 3 Haiku (cost-effective)
- **Features**:
  - Intelligent extraction of complex order data
  - Separate prompts for TileWare and Laticrete products
  - Handles varied email formats
  - JSON response for structured data
  - Low temperature (0.1) for consistent parsing

### 4. Order Formatter Module (`src/order_formatter.py`)
- **Purpose**: Convert to CS team format
- **Features**:
  - Standardized output format
  - Product line formatting with SKUs
  - Address formatting
  - Fallback for missing data

### 5. Email Sender Module (`src/email_sender.py`)
- **Protocol**: SMTP for sending emails
- **Features**:
  - HTML and plain text versions
  - PDF attachment support
  - Retry logic with exponential backoff
  - Connection testing
  - Batch sending support

### 6. Laticrete Processor (`src/laticrete_processor.py`)
- **Purpose**: Handle Laticrete-specific order processing
- **Features**:
  - Price list enrichment from Excel file
  - PDF order form generation
  - Automated email with PDF attachment
  - End-to-end Laticrete order handling

### 7. Price List Reader (`src/price_list_reader.py`)
- **Purpose**: Parse and search Laticrete price list
- **Features**:
  - Excel file parsing with pandas
  - Product search by name or SKU
  - Flexible column mapping
  - Price and product info extraction

### 8. PDF Filler (`src/pdf_filler.py`)
- **Purpose**: Fill Laticrete PDF order forms
- **Features**:
  - AcroForm field detection and filling
  - Fallback text overlay for non-form PDFs
  - Order data to PDF mapping
  - Temporary file management

## Implementation Details

### Project Structure
```
email-client-cli/
├── main.py                 # Entry point with scheduler
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
├── .env                   # User configuration (gitignored)
├── .gitignore             # Git ignore patterns
├── CLAUDE.md              # This file
├── README.md              # User documentation
├── resources/
│   └── laticrete/
│       ├── lat_blank_orderform.pdf  # Laticrete order form template
│       └── lat_price_list.xlsx      # Laticrete product price list
└── src/
    ├── __init__.py
    ├── email_fetcher.py   # IMAP implementation
    ├── email_parser.py    # HTML parsing logic
    ├── claude_processor.py # AI integration
    ├── order_formatter.py # Output formatting
    ├── email_sender.py    # SMTP implementation
    ├── laticrete_processor.py # Laticrete order handling
    ├── price_list_reader.py   # Excel price list parser
    ├── pdf_filler.py         # PDF form filler
    ├── order_tracker.py      # Order deduplication
    ├── test_connections.py   # Testing utility
    ├── test_laticrete.py    # Laticrete testing
    └── utils/
        ├── __init__.py
        └── logger.py      # Logging setup
```

### Dependencies
```
anthropic>=0.18.0       # Claude API
imap-tools>=1.6.0       # IMAP library
beautifulsoup4>=4.12.0  # HTML parsing
python-dotenv>=1.0.0    # Environment variables
APScheduler>=3.10.0     # Task scheduling
colorlog>=6.8.0         # Colored logging
retry>=0.9.2            # Retry decorator

# PDF and Excel processing
pypdf>=3.17.0           # PDF manipulation
PyPDF2>=3.0.0          # PDF form handling
reportlab>=4.0.0       # PDF generation
openpyxl>=3.1.0        # Excel file reading
pandas>=2.0.0          # Data processing
```

## Email Processing Flow

### 1. Email Detection
```python
# Criteria in email_fetcher.py
- From: "noreply@tileprodepot.com"
- Subject contains: "New customer order"
- Body contains: "You've received the following order from"
```

### 2. Product Detection
```python
# TileWare patterns in email_parser.py
tileware_patterns = [
    r'tileware',
    r'TileWare',
    r'Tile\s*Ware',
    r'TILEWARE'
]

# Laticrete patterns in email_parser.py
laticrete_patterns = [
    r'laticrete',
    r'LATICRETE',
    r'Laticrete',
    r'LATI\s*CRETE'
]
```

### 3. Data Extraction (Claude)
```python
# Prompt structure extracts:
{
    "order_id": "43060",
    "customer_name": "Tasha Waldron",
    "tileware_products": [{
        "name": "TileWare Promessa™ Series Tee Hook",
        "sku": "T101-211-PC",
        "quantity": 3,
        "price": "$130.20"
    }],
    "shipping_address": {
        "name": "Tasha Waldron",
        "street": "40438 N Deep Lake Rd",
        "city": "Antioch",
        "state": "IL",
        "zip": "60002"
    },
    "shipping_method": "UPS GROUND",
    "total": "$155.20"
}
```

### 4. Output Format

#### TileWare Orders (Text Email)
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

#### Laticrete Orders (PDF Attachment)
- Email sent to LATICRETE_CS_EMAIL with:
  - HTML/Text email body with order summary
  - Attached PDF order form filled with:
    - Customer information
    - Product details with SKUs
    - Quantities and prices from price list
    - Shipping address
    - Order date and number

## Configuration Guide

### Required Environment Variables
```bash
# Email Reading (IMAP)
IMAP_SERVER=imap.gmail.com      # IMAP server host
IMAP_PORT=993                    # IMAP port (993 for SSL)
EMAIL_ADDRESS=monitor@gmail.com  # Email to monitor
EMAIL_PASSWORD=xxxx xxxx xxxx    # App password (16 chars)

# AI Processing
ANTHROPIC_API_KEY=sk-ant-api03-xxx  # Claude API key

# Email Sending (SMTP)
SMTP_SERVER=smtp.gmail.com      # SMTP server host
SMTP_PORT=587                    # SMTP port (587 for TLS)
SMTP_USERNAME=sender@gmail.com  # Sender email
SMTP_PASSWORD=xxxx xxxx xxxx    # App password

# Processing
CS_EMAIL=cs@company.com         # Where to send TileWare orders
LATICRETE_CS_EMAIL=lat-cs@company.com  # Where to send Laticrete orders
CHECK_INTERVAL_MINUTES=5        # Check frequency
LOG_LEVEL=INFO                  # Logging verbosity
LOG_FILE=email_processor.log    # Log file path
```

### Gmail Setup
1. Enable 2-Factor Authentication
2. Generate App Password:
   - myaccount.google.com → Security → 2-Step Verification → App passwords
   - Select "Mail" → Generate
3. Enable IMAP:
   - Gmail Settings → Forwarding and POP/IMAP → Enable IMAP

## Cost Analysis

### Claude API Pricing (as of 2024)
- **Haiku**: $0.25 / 1M input tokens, $1.25 / 1M output tokens
- **Average email**: ~2000 tokens input, ~500 tokens output
- **Cost per email**: ~$0.0001 (1/100th of a cent)
- **Monthly estimate** (500 emails): ~$0.05

### Optimization Strategies
1. Use Haiku model (cheapest, sufficient for parsing)
2. Cache common patterns
3. Batch process when possible
4. Use basic parser first, Claude only for complex cases

## Security Considerations

### Credentials
- App passwords only (never regular passwords)
- Environment variables (never hardcode)
- `.env` in `.gitignore`
- Rotate keys quarterly

### Data Protection
- No PII in logs
- Encrypted connections (TLS/SSL)
- Limited email retention
- Audit trail for processed orders

### Access Control
- Restrict CS_EMAIL to internal domains
- Monitor for unusual activity
- Rate limiting on API calls
- Failed authentication alerts

## Monitoring & Debugging

### Log Levels
- **DEBUG**: Detailed processing steps
- **INFO**: Normal operations
- **WARNING**: Non-critical issues
- **ERROR**: Processing failures

### Key Log Messages
```
"Starting email processing cycle..."
"Found X new emails from Tile Pro Depot"
"Processing order email: [subject]"
"Successfully processed and sent order #X"
"Error processing email: [error]"
```

### Debug Commands
```bash
# Test connections
python src/test_connections.py

# Check for emails (debug mode)
python -c "from src.email_fetcher import EmailFetcher; ..."

# View recent logs
tail -n 100 email_processor.log | grep "Successfully processed"

# Monitor in real-time
tail -f email_processor.log
```

## Error Handling

### Retry Logic
- **IMAP failures**: 3 retries with 2s backoff
- **SMTP failures**: 3 retries with exponential backoff
- **Claude API**: Handle rate limits gracefully
- **Network errors**: Automatic reconnection

### Common Issues
1. **Authentication**: App password required
2. **No emails found**: Check filters/folder
3. **Claude errors**: Check API key/credits
4. **SMTP blocked**: Firewall/port issues

## Performance Optimization

### Current Implementation
- Single-threaded processing
- Sequential email processing
- 5-minute check interval
- ~2-3 seconds per email

### Future Optimizations
1. Concurrent email processing
2. Database for processed emails
3. Caching for common patterns
4. Webhook integration
5. Queue-based architecture

## Development Guidelines

### Adding New Features
1. Update `requirements.txt` for new dependencies
2. Follow existing module patterns
3. Add comprehensive logging
4. Update both README.md and CLAUDE.md
5. Test with `src/test_connections.py`

### Testing
```bash
# Unit tests (future)
python -m pytest tests/

# Integration test
python main.py --once

# Connection test
python src/test_connections.py
```

## Deployment Considerations

### Local Deployment
```bash
# Run in background
nohup python main.py &

# Or use screen/tmux
screen -S email-client
python main.py
# Ctrl+A, D to detach
```

### Production Deployment
1. Use systemd service (Linux)
2. Docker container (cross-platform)
3. Cloud Functions (serverless)
4. Kubernetes CronJob (scalable)

### Systemd Example
```ini
[Unit]
Description=Email Client CLI
After=network.target

[Service]
Type=simple
User=emailbot
WorkingDirectory=/opt/email-client-cli
Environment="PATH=/opt/email-client-cli/venv/bin"
ExecStart=/opt/email-client-cli/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Maintenance Schedule

### Daily
- Monitor logs for errors
- Check processed order count

### Weekly
- Review API usage/costs
- Check for missed emails

### Monthly
- Rotate logs
- Review error patterns
- Update documentation

### Quarterly
- Update dependencies
- Rotate API keys
- Performance review
- Update Laticrete price list if needed

## Laticrete Processing Details

### Overview
The system automatically detects and processes Laticrete product orders differently from TileWare orders:
1. Detects Laticrete products in order emails
2. Extracts order information using Claude
3. Cross-references products with Excel price list
4. Fills out PDF order form
5. Sends email with PDF attachment to Laticrete CS team

### Laticrete-Specific Files
- **Price List**: `resources/laticrete/lat_price_list.xlsx`
  - Excel file with product names, SKUs, and prices
  - Automatically parsed to match order products
  - Supports flexible column naming
  
- **Order Form**: `resources/laticrete/lat_blank_orderform.pdf`
  - Blank PDF template for orders
  - Filled programmatically with order data
  - Supports both form fields and text overlay

### Processing Flow
1. **Detection**: Email parser identifies Laticrete products
2. **Extraction**: Claude extracts order details with Laticrete-specific prompt
3. **Enrichment**: Price list reader matches products and adds pricing
4. **PDF Generation**: PDF filler creates completed order form
5. **Email Delivery**: Sends to LATICRETE_CS_EMAIL with PDF attachment

### Testing Laticrete Features
```bash
# Run Laticrete test suite
python src/test_laticrete.py

# Test individual components
python src/price_list_reader.py    # Test price list parsing
python src/pdf_filler.py           # Test PDF generation
```

### Troubleshooting Laticrete Processing
- **Products not found**: Check price list Excel file has correct columns
- **PDF not filling**: Verify PDF form fields or use text overlay mode
- **Email not sending**: Ensure LATICRETE_CS_EMAIL is set in .env
- **Mixed orders**: System processes TileWare and Laticrete separately