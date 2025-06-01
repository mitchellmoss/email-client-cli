#!/bin/bash
# Production deployment script for Email Client CLI with Admin Panel

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_USER="emailbot"
DEPLOY_PATH="/opt/email-client-cli"
SYSTEMD_PATH="/etc/systemd/system"
NGINX_PATH="/etc/nginx/sites-available"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

print_status "Starting Email Client CLI deployment..."

# Create deployment user if doesn't exist
if ! id "$DEPLOY_USER" &>/dev/null; then
    print_status "Creating deployment user: $DEPLOY_USER"
    useradd -m -s /bin/bash $DEPLOY_USER
fi

# Create deployment directory
print_status "Setting up deployment directory..."
mkdir -p $DEPLOY_PATH
chown -R $DEPLOY_USER:$DEPLOY_USER $DEPLOY_PATH

# Copy application files
print_status "Copying application files..."
cp -r ./* $DEPLOY_PATH/
chown -R $DEPLOY_USER:$DEPLOY_USER $DEPLOY_PATH

# Create logs directory
mkdir -p $DEPLOY_PATH/logs
chown $DEPLOY_USER:$DEPLOY_USER $DEPLOY_PATH/logs

# Check for production environment file
if [ ! -f "$DEPLOY_PATH/.env.production" ]; then
    print_warning "Production environment file not found!"
    print_warning "Please create $DEPLOY_PATH/.env.production based on .env.production.example"
    cp $DEPLOY_PATH/.env.production.example $DEPLOY_PATH/.env.production
    print_error "Edit $DEPLOY_PATH/.env.production with your settings before continuing"
    exit 1
fi

# Install Python dependencies for main application
print_status "Installing Python dependencies for main application..."
cd $DEPLOY_PATH
sudo -u $DEPLOY_USER python3 -m venv venv
sudo -u $DEPLOY_USER venv/bin/pip install --upgrade pip
sudo -u $DEPLOY_USER venv/bin/pip install -r requirements.txt

# Install Python dependencies for admin backend
print_status "Installing Python dependencies for admin backend..."
cd $DEPLOY_PATH/admin_panel/backend
sudo -u $DEPLOY_USER python3 -m venv venv
sudo -u $DEPLOY_USER venv/bin/pip install --upgrade pip
sudo -u $DEPLOY_USER venv/bin/pip install -r requirements.txt
sudo -u $DEPLOY_USER venv/bin/pip install gunicorn

# Build frontend
print_status "Building frontend application..."
cd $DEPLOY_PATH/admin_panel/frontend

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install Node.js and npm first."
    exit 1
fi

# Read API URL from environment
if [ -z "$FRONTEND_API_URL" ]; then
    print_warning "FRONTEND_API_URL not set, using default"
    FRONTEND_API_URL="https://api.your-domain.com"
fi

# Install dependencies and build
sudo -u $DEPLOY_USER npm ci
sudo -u $DEPLOY_USER VITE_API_URL="$FRONTEND_API_URL" npm run build

# Setup systemd services
print_status "Installing systemd services..."
cp $DEPLOY_PATH/deploy/systemd/*.service $SYSTEMD_PATH/
systemctl daemon-reload

# Setup nginx configuration
print_status "Setting up nginx configuration..."
if [ -f "$NGINX_PATH/email-admin.conf" ]; then
    print_warning "Nginx configuration already exists. Backing up..."
    cp $NGINX_PATH/email-admin.conf $NGINX_PATH/email-admin.conf.backup
fi

cp $DEPLOY_PATH/deploy/nginx/email-admin.conf $NGINX_PATH/

# Update nginx config with actual domain
if [ ! -z "$DOMAIN" ]; then
    print_status "Updating nginx configuration with domain: $DOMAIN"
    sed -i "s/your-domain.com/$DOMAIN/g" $NGINX_PATH/email-admin.conf
else
    print_warning "DOMAIN not set. Please update nginx configuration manually."
fi

# Enable nginx site
ln -sf $NGINX_PATH/email-admin.conf /etc/nginx/sites-enabled/

# Test nginx configuration
print_status "Testing nginx configuration..."
nginx -t

# Set up database
print_status "Setting up database..."
touch $DEPLOY_PATH/order_tracking.db
chown $DEPLOY_USER:$DEPLOY_USER $DEPLOY_PATH/order_tracking.db
chmod 664 $DEPLOY_PATH/order_tracking.db

# Start services
print_status "Starting services..."
systemctl enable email-processor
systemctl enable email-admin-backend
systemctl start email-processor
systemctl start email-admin-backend

# Reload nginx
systemctl reload nginx

# Check service status
print_status "Checking service status..."
sleep 2
systemctl status email-processor --no-pager
systemctl status email-admin-backend --no-pager

print_status "Deployment complete!"
print_status "=================="
print_status "Next steps:"
print_status "1. Update $DEPLOY_PATH/.env.production with your settings"
print_status "2. Update nginx configuration with your domain"
print_status "3. Set up SSL certificates with certbot"
print_status "4. Configure firewall (ports 80, 443)"
print_status "5. Access admin panel at https://your-domain.com"
print_status ""
print_status "Useful commands:"
print_status "- systemctl status email-processor"
print_status "- systemctl status email-admin-backend"
print_status "- journalctl -u email-processor -f"
print_status "- journalctl -u email-admin-backend -f"
print_status "- tail -f $DEPLOY_PATH/logs/*.log"