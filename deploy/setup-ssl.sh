#!/bin/bash
# SSL setup script using Let's Encrypt

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

# Get domain from user or environment
if [ -z "$DOMAIN" ]; then
    read -p "Enter your domain name (e.g., example.com): " DOMAIN
fi

if [ -z "$EMAIL" ]; then
    read -p "Enter your email for Let's Encrypt notifications: " EMAIL
fi

print_status "Setting up SSL for domain: $DOMAIN"

# Install certbot if not present
if ! command -v certbot &> /dev/null; then
    print_status "Installing certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Get certificates
print_status "Obtaining SSL certificates..."
certbot certonly --nginx \
    --non-interactive \
    --agree-tos \
    --email $EMAIL \
    --domains $DOMAIN,www.$DOMAIN,api.$DOMAIN \
    --redirect

# Update nginx configuration
print_status "Updating nginx configuration..."
sed -i "s|#ssl_certificate|ssl_certificate|g" /etc/nginx/sites-available/email-admin.conf
sed -i "s|#ssl_certificate_key|ssl_certificate_key|g" /etc/nginx/sites-available/email-admin.conf

# Test and reload nginx
nginx -t
systemctl reload nginx

# Set up auto-renewal
print_status "Setting up auto-renewal..."
cat > /etc/cron.d/certbot-renewal << EOF
# Renew certificates twice daily
0 0,12 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
EOF

print_status "SSL setup complete!"
print_status "Your site is now accessible at https://$DOMAIN"
print_status "Certificates will auto-renew via cron"