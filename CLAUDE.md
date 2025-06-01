# Email Client CLI - Tile Pro Depot Order Processor

## Project Overview
An intelligent email processing agent that monitors emails from Tile Pro Depot and automatically:
- Extracts and forwards TileWare product orders to customer service
- Extracts Laticrete product orders, cross-references pricing, fills PDF order forms, and sends to Laticrete CS team
- Prevents duplicate order processing with persistent order tracking
- Provides comprehensive order management and monitoring capabilities

## Key Features
- Periodic IMAP email fetching (not SMTP - SMTP is for sending only)
- Intelligent email parsing using Claude API
- Automatic order extraction and formatting
- Dual product support: TileWare and Laticrete
- Laticrete price list cross-referencing
- PDF order form generation for Laticrete orders
- Email forwarding with formatted order details or PDF attachments
- Comprehensive error handling and retry logic
- Order tracking database to prevent duplicate sends
- Order management CLI utilities
- **NEW: Web Admin Panel for monitoring and management**

## Architecture

### 1. Email Fetching Module (`src/email_fetcher.py`)
- **Protocol**: IMAP (Internet Message Access Protocol) for reading emails
- **Features**:
  - Connects to any IMAP server (Gmail, Outlook, etc.)
  - Filters emails by sender (`noreply@tileprodepot.com`)
  - Searches for "New customer order" in subject
  - Supports both read/unread email tracking
  - Implements connection pooling for efficiency
  - Prevents marking emails as read on server (preserves original state)

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
  - Robust error handling for malformed responses
  - Automatic retry on API failures

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
  - Email signature support
  - Configurable sender name
  - MIME multipart message construction

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
  - Multiple PDF library support (PyMuPDF, pdfrw, pypdf)
  - Automatic method selection with fallback
  - Order data to PDF mapping
  - Temporary file management
  - Dynamic field mapping based on order data
  - Support for both fillable forms and text overlay

### 9. Order Tracker Module (`src/order_tracker.py`)
- **Purpose**: Prevent duplicate order sends and track order history
- **Features**:
  - SQLite database with WAL mode for concurrency
  - Order deduplication by order ID
  - Full order history tracking
  - Thread-safe operations
  - Order search and management capabilities
  - Automatic database initialization

### 10. Order Management Utility (`src/manage_orders.py`)
- **Purpose**: CLI utility for viewing and managing processed orders
- **Features**:
  - List all processed orders
  - Search orders by ID, customer, or date
  - View detailed order information
  - Export order data
  - Delete old orders
  - Tabulated output for readability

### 11. Web Admin Panel (`admin_panel/`)
- **Purpose**: Web-based monitoring and management interface
- **Backend** (`admin_panel/backend/`):
  - FastAPI with Python
  - JWT authentication
  - RESTful API endpoints
  - Integration with existing Python modules
  - Real-time system status
- **Frontend** (`admin_panel/frontend/`):
  - React with TypeScript
  - Tailwind CSS for styling
  - Real-time dashboard
  - Order management interface
  - Product matching for Laticrete
  - System configuration
- **Documentation**:
  - `admin_panel/README.md` - Overview and features
  - `admin_panel/SETUP_GUIDE.md` - Installation guide
  - `admin_panel/ADMIN_PANEL_SUMMARY.md` - Technical summary

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
├── order_tracking.db      # SQLite database for order tracking
├── logs/                  # Log files directory
├── start_all.sh           # Unix startup script (all services)
├── start_all.py           # Cross-platform startup script
├── start_all.bat          # Windows startup script
├── stop_all.sh            # Unix stop script
├── STARTUP_GUIDE.md       # Startup documentation
├── admin_panel/           # Web admin panel
│   ├── backend/          # FastAPI backend
│   │   ├── main.py      # API entry point
│   │   ├── auth.py      # JWT authentication
│   │   ├── database.py  # Database models
│   │   ├── config.py    # Configuration settings
│   │   ├── api/         # API routes
│   │   │   ├── auth.py
│   │   │   ├── orders.py
│   │   │   ├── products.py
│   │   │   ├── system.py
│   │   │   └── email_config.py
│   │   ├── models/      # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   └── frontend/        # React frontend
│       ├── src/         # React components
│       │   ├── pages/   # Page components
│       │   ├── components/ # UI components
│       │   └── api/     # API client
│       └── package.json # Frontend dependencies
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
    ├── order_tracker.py      # Order deduplication & history
    ├── manage_orders.py      # Order management CLI
    ├── test_connections.py   # Testing utility
    ├── test_laticrete.py    # Laticrete testing
    ├── test_order_tracking.py # Order tracking tests
    ├── test_one_email.py    # Single email testing
    ├── test_inbox.py        # Inbox testing utility
    ├── debug_email_search.py # Email debugging tool
    ├── search_order.py      # Order search utility
    └── utils/
        ├── __init__.py
        └── logger.py      # Logging setup
```

### Dependencies
```
# Core dependencies
anthropic>=0.18.0       # Claude API
imap-tools>=1.6.0       # IMAP library
beautifulsoup4>=4.12.0  # HTML parsing
python-dotenv>=1.0.0    # Environment variables
APScheduler>=3.10.0     # Task scheduling

# Email parsing
lxml>=5.0.0             # XML/HTML parser
html5lib>=1.1           # HTML5 parser

# PDF and Excel processing
pypdf>=3.17.0           # PDF manipulation
PyPDF2>=3.0.0          # PDF form handling
reportlab>=4.0.0       # PDF generation
pdfrw>=0.4             # PDF reader/writer
PyMuPDF>=1.23.0        # PDF toolkit (fitz)
openpyxl>=3.1.0        # Excel file reading
pandas>=2.0.0          # Data processing

# Logging and utilities
colorlog>=6.8.0         # Colored logging
retry>=0.9.2            # Retry decorator
tabulate>=0.9.0         # Table formatting

# Development dependencies
pytest>=8.0.0           # Testing framework
pytest-asyncio>=0.23.0  # Async test support
black>=24.0.0          # Code formatter
flake8>=7.0.0          # Linter
```

## Email Processing Flow

### Overview
1. **Fetch**: IMAP connection retrieves new order emails
2. **Parse**: BeautifulSoup extracts HTML content
3. **Detect**: Identify TileWare/Laticrete products
4. **Extract**: Claude API processes order details
5. **Check**: Verify order not already processed
6. **Format**: Prepare email content or PDF
7. **Send**: Deliver to appropriate CS team
8. **Track**: Record in database

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

### 4. Order Tracking
```python
# Before sending, check if order already processed
if tracker.is_order_sent(order_id):
    logger.info(f"Order {order_id} already sent, skipping")
    return

# After successful send, record in database
tracker.record_sent_order(
    order_id=order_id,
    email_subject=email_subject,
    sent_to=recipient_email,
    customer_name=customer_name,
    products=products,
    order_total=total,
    formatted_content=email_content
)
```

### 5. Output Format

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

## Database Schema

### Order Tracking Database (`order_tracking.db`)
The system uses SQLite with WAL mode for concurrent access. Main tables:

#### sent_orders
- **id**: Primary key
- **order_id**: Unique order identifier from Tile Pro Depot
- **email_subject**: Original email subject
- **sent_at**: Timestamp when order was sent to CS
- **sent_to**: Email address order was sent to
- **customer_name**: Customer name from order
- **tileware_products**: JSON array of TileWare products
- **order_total**: Total order amount
- **formatted_content**: Formatted email content sent
- **email_uid**: IMAP email UID
- **created_at**: Record creation timestamp
- **order_data**: JSON blob with complete order details
- **product_type**: Type of products (tileware/laticrete/both)
- **laticrete_products**: JSON array of Laticrete products

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
ORDER_TRACKING_DB=order_tracking.db  # SQLite database for order tracking


# Admin Panel (optional)
ADMIN_EMAIL=admin@example.com   # Default admin login
ADMIN_PASSWORD=changeme         # Default admin password
JWT_SECRET=your-secret-key      # JWT token secret
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

### Order Management Commands
```bash
# List all orders
python src/manage_orders.py list

# Search orders by customer
python src/manage_orders.py search --customer "John Doe"

# Search orders by order ID
python src/manage_orders.py search --order-id 43060

# View order details
python src/manage_orders.py view ORDER_ID

# Delete old orders
python src/manage_orders.py cleanup --days 90

# Export orders to JSON
python src/manage_orders.py export --output orders.json
```

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
"Order #X already sent, skipping"
"Saved order #X to tracking database"
```

### Log File Locations
- **Main log**: `email_processor.log` (root directory)
- **Organized logs**: `logs/` directory
  - `logs/email_processor.log` - Email processing logs
  - `logs/admin_backend.log` - API server logs
  - `logs/admin_frontend.log` - Frontend dev server logs

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

# Check duplicate prevention
sqlite3 order_tracking.db "SELECT order_id, sent_at FROM sent_orders ORDER BY sent_at DESC LIMIT 10;"

# View order statistics
sqlite3 order_tracking.db "SELECT COUNT(*) as total, product_type FROM sent_orders GROUP BY product_type;"
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
5. **Duplicate sends**: Check order_tracking.db integrity
6. **Database locked**: Multiple processes accessing DB

## Performance Optimization

### Current Implementation
- Single-threaded processing
- Sequential email processing
- 5-minute check interval
- ~2-3 seconds per email
- SQLite with WAL mode for concurrent access
- Connection pooling for IMAP/SMTP
- Efficient duplicate detection via indexed order_id

### Future Optimizations
1. Concurrent email processing
2. ~~Database for processed emails~~ ✓ Implemented
3. Caching for common patterns
4. Webhook integration
5. Queue-based architecture
6. Real-time email notifications
7. Advanced analytics dashboard

## Development Guidelines

### Adding New Features
1. Update `requirements.txt` for new dependencies
2. Follow existing module patterns
3. Add comprehensive logging
4. Update both README.md and CLAUDE.md
5. Test with `src/test_connections.py`

### Testing
```bash
# Unit tests
python -m pytest tests/

# Integration test
python main.py --once

# Connection test
python src/test_connections.py

# Test single email processing
python src/test_one_email.py

# Order management utility
python src/manage_orders.py stats    # View statistics
python src/manage_orders.py list     # List recent orders
python src/manage_orders.py view ORDER_ID  # View specific order
python src/manage_orders.py check ORDER_ID # Check if order was sent
python src/manage_orders.py cleanup --days 90  # Clean old orders

# Test inbox access
python src/test_inbox.py

# Test order tracking
python src/test_order_tracking.py

# Debug email search
python src/debug_email_search.py

# Order management
python src/manage_orders.py --help
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
- Archive old orders (beyond retention period)
- Database optimization (VACUUM)

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
- **Price matching failures**: Run `python src/verify_laticrete_matching.py` to diagnose
- **PDF library errors**: System will try multiple methods automatically

## Web Admin Panel

### Overview
The admin panel provides a modern web interface for monitoring and managing the email processing system without interrupting the CLI operation.

### Features
1. **Dashboard**: Real-time system monitoring
   - System status (running/stopped)
   - Order statistics and trends
   - Recent activity logs
   - Processing metrics

2. **Order Management**:
   - View all processed orders
   - Search and filter capabilities
   - Resend orders to CS teams
   - Export order data

3. **Product Matching**:
   - Map unmatched Laticrete products
   - Manage SKU mappings
   - Update pricing information
   - Bulk import/export

4. **System Configuration**:
   - Email server settings (IMAP/SMTP)
   - Connection testing
   - Email templates
   - System control (start/stop)

### Technical Stack
- **Backend**: FastAPI (Python) with JWT authentication
- **Frontend**: React + TypeScript + Tailwind CSS
- **Database**: Same SQLite database as CLI
- **API**: RESTful with OpenAPI documentation

### Quick Start
```bash
# Backend (Terminal 1)
cd admin_panel/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./run_dev.sh

# Frontend (Terminal 2)
cd admin_panel/frontend
npm install
npm run dev

# Access at http://localhost:5173
# Login: admin@example.com / changeme
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Integration
The admin panel integrates seamlessly with the existing CLI system:
- Uses the same database (`order_tracking.db`)
- Imports existing Python modules
- Reads the same `.env` configuration
- Can control the email processor remotely

### Security
- JWT-based authentication
- Admin role protection
- Secure API endpoints
- Session management
- Audit logging for all actions

## Startup Scripts

### Overview
The project includes cross-platform startup scripts that launch all components with a single command.

### Scripts Provided
1. **start_all.sh** (Mac/Linux)
   - Bash script with colored output
   - Automatic virtual environment setup
   - Health checks for service readiness
   - Combined log tailing

2. **start_all.py** (Cross-platform)
   - Python-based launcher
   - Works on Windows, Mac, and Linux
   - Process management and monitoring
   - Graceful shutdown handling

3. **start_all.bat** (Windows)
   - Batch script for Windows
   - Opens services in separate windows
   - Automatic dependency installation

4. **stop_all.sh** (Mac/Linux)
   - Stops all running services
   - Cleans up background processes

### Features
- Automatic virtual environment creation
- Dependency installation (pip and npm)
- Service health monitoring
- Log file management
- Graceful shutdown on Ctrl+C
- Colored console output
- Cross-platform compatibility

### Usage
```bash
# Start all services
./start_all.sh      # Mac/Linux
python start_all.py # Any platform
start_all.bat       # Windows

# Stop all services
./stop_all.sh       # Mac/Linux
# or Ctrl+C in the startup terminal
```

## Production Deployment

### Overview
The project is production-ready with comprehensive configuration for Linux server deployment. All components support configurable URLs and domains.

### Production Files Added
1. **`.env.production.example`** - Production environment template
2. **`admin_panel/backend/config.py`** - Dynamic CORS and URL configuration
3. **`admin_panel/frontend/.env.production`** - Frontend API URL config
4. **Docker Configuration**:
   - `Dockerfile` - Main email processor
   - `admin_panel/backend/Dockerfile` - API server
   - `admin_panel/frontend/Dockerfile` - React frontend
   - `docker-compose.prod.yml` - Orchestration
5. **Systemd Services**:
   - `deploy/systemd/email-processor.service`
   - `deploy/systemd/email-admin-backend.service`
6. **Nginx Configuration**:
   - `deploy/nginx/email-admin.conf` - Full HTTPS setup
7. **Deployment Scripts**:
   - `deploy/deploy.sh` - Automated deployment
   - `deploy/setup-ssl.sh` - Let's Encrypt SSL
8. **`PRODUCTION_DEPLOYMENT.md`** - Comprehensive deployment guide

### Key Production Features
- **Configurable URLs**: Frontend and backend URLs can be set via environment
- **Dynamic CORS**: Automatically configured based on frontend URL
- **Security Hardening**: Production validates secrets, enforces HTTPS
- **Multiple Deployment Options**: Docker, systemd, or manual
- **SSL/TLS Ready**: Nginx config with Let's Encrypt integration
- **Health Checks**: Built-in monitoring endpoints
- **Log Management**: Centralized logging with rotation

### Quick Production Deploy
```bash
# On Linux server
git clone <repo>
cd email-client-cli
cp .env.production.example .env.production
# Edit .env.production with your settings

# Deploy
export DOMAIN=your-domain.com
export FRONTEND_API_URL=https://api.your-domain.com
sudo ./deploy/deploy.sh
sudo ./deploy/setup-ssl.sh
```

### URL Configuration
- **Backend CORS**: Set via `FRONTEND_URL` and `CORS_ORIGINS` in `.env.production`
- **Frontend API**: Set via `VITE_API_URL` at build time or in `.env.production`
- **Nginx Routing**: Handles `/api/` proxy to backend, serves frontend static files

See `PRODUCTION_DEPLOYMENT.md` for detailed instructions.

## Recent Updates & Version History

### Version 2.2.0 (January 2025)
- Added production deployment configuration
- Implemented configurable URLs for frontend/backend
- Added Docker and systemd deployment options
- Created automated deployment scripts
- Enhanced security for production environments

### Version 2.1.0 (May 2024)
- Added order tracking database to prevent duplicate sends
- Implemented order management CLI utilities
- Added comprehensive test suite
- Improved email fetcher to preserve read status
- Enhanced PDF filling with multiple library support

### Version 2.0.0 (April 2024)
- Introduced Web Admin Panel with React/FastAPI
- Added Laticrete product processing with PDF generation
- Implemented price list matching from Excel
- Added startup scripts for all platforms
- Enhanced logging and error handling

### Version 1.0.0 (March 2024)
- Initial release with TileWare order processing
- Basic email fetching and parsing
- Claude API integration for order extraction
- SMTP email forwarding to CS team