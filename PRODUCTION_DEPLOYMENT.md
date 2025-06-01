# Production Deployment Guide

This guide covers deploying the Email Client CLI with Admin Panel on a Linux server.

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Root or sudo access
- Domain name pointed to your server
- Ports 80 and 443 open in firewall
- Python 3.8+
- Node.js 16+ and npm
- nginx
- Git

## Quick Start

1. **Clone the repository on your server:**
   ```bash
   git clone https://github.com/yourusername/email-client-cli.git
   cd email-client-cli
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.production.example .env.production
   # Edit with your actual values
   nano .env.production
   ```

   Key variables to set:
   - `FRONTEND_URL`: Your domain (e.g., https://admin.example.com)
   - `CORS_ORIGINS`: Allowed origins for API
   - `SECRET_KEY`: Generate with `openssl rand -hex 32`
   - Email credentials (IMAP/SMTP)
   - API keys

3. **Run deployment script:**
   ```bash
   # Set your domain and API URL
   export DOMAIN=example.com
   export FRONTEND_API_URL=https://api.example.com
   
   # Run deployment
   sudo ./deploy/deploy.sh
   ```

4. **Set up SSL:**
   ```bash
   sudo ./deploy/setup-ssl.sh
   ```

## Manual Deployment Steps

### 1. System Setup

```bash
# Create deployment user
sudo useradd -m -s /bin/bash emailbot
sudo usermod -aG sudo emailbot

# Create deployment directory
sudo mkdir -p /opt/email-client-cli
sudo chown emailbot:emailbot /opt/email-client-cli
```

### 2. Install Dependencies

```bash
# System packages
sudo apt update
sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx

# Install Node.js (if not present)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 3. Deploy Application

```bash
# Copy files to deployment directory
sudo -u emailbot cp -r . /opt/email-client-cli/
cd /opt/email-client-cli

# Create Python virtual environments
sudo -u emailbot python3 -m venv venv
sudo -u emailbot admin_panel/backend/venv/bin/pip install -r requirements.txt

cd admin_panel/backend
sudo -u emailbot python3 -m venv venv
sudo -u emailbot venv/bin/pip install -r requirements.txt gunicorn
```

### 4. Build Frontend

```bash
cd /opt/email-client-cli/admin_panel/frontend
sudo -u emailbot npm ci
sudo -u emailbot VITE_API_URL="https://api.your-domain.com" npm run build
```

### 5. Configure Services

```bash
# Copy systemd services
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable email-processor email-admin-backend
sudo systemctl start email-processor email-admin-backend
```

### 6. Configure Nginx

```bash
# Copy nginx config
sudo cp deploy/nginx/email-admin.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/email-admin.conf /etc/nginx/sites-enabled/

# Update domain in config
sudo sed -i "s/your-domain.com/example.com/g" /etc/nginx/sites-available/email-admin.conf

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### 7. Set Up SSL

```bash
sudo certbot --nginx -d example.com -d www.example.com -d api.example.com
```

## Configuration Options

### Frontend URL Configuration

The frontend needs to know where the API is located. This can be configured in several ways:

1. **Build-time configuration** (recommended for production):
   ```bash
   VITE_API_URL="https://api.example.com" npm run build
   ```

2. **Environment file**:
   Create `admin_panel/frontend/.env.production`:
   ```
   VITE_API_URL=https://api.example.com
   ```

3. **Docker build argument**:
   ```bash
   docker build --build-arg VITE_API_URL=https://api.example.com -t email-admin-frontend .
   ```

### Backend URL Configuration

The backend CORS settings must allow your frontend domain:

```bash
# In .env.production
FRONTEND_URL=https://admin.example.com
CORS_ORIGINS=https://admin.example.com,https://www.admin.example.com
```

### Database Location

By default, the SQLite database is at `/opt/email-client-cli/order_tracking.db`. To change:

```bash
# In .env.production
DATABASE_PATH=/var/lib/email-client-cli/order_tracking.db
DATABASE_URL=sqlite:////var/lib/email-client-cli/order_tracking.db
```

## Docker Deployment

For Docker deployment:

```bash
# Build and run with docker-compose
cd /opt/email-client-cli
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Monitoring

### Check Service Status

```bash
# Main email processor
sudo systemctl status email-processor
sudo journalctl -u email-processor -f

# Admin backend
sudo systemctl status email-admin-backend
sudo journalctl -u email-admin-backend -f

# View logs
tail -f /opt/email-client-cli/logs/*.log
```

### Health Checks

- Frontend: `https://your-domain.com/health`
- Backend API: `https://your-domain.com/api/health`
- Direct backend: `http://localhost:8000/health`

## Security Checklist

- [ ] Change default admin password
- [ ] Generate secure JWT secret key
- [ ] Configure firewall (ufw/iptables)
- [ ] Set up SSL certificates
- [ ] Restrict database file permissions
- [ ] Enable nginx security headers
- [ ] Set up log rotation
- [ ] Configure fail2ban for login attempts
- [ ] Regular security updates

## Troubleshooting

### Frontend can't connect to API

1. Check CORS settings in backend
2. Verify API URL in frontend build
3. Check nginx proxy configuration
4. Verify backend is running: `curl http://localhost:8000/health`

### Database errors

1. Check file permissions: `ls -la /opt/email-client-cli/order_tracking.db`
2. Ensure emailbot user owns the file
3. Check disk space: `df -h`

### SSL issues

1. Verify domain DNS points to server
2. Check firewall allows ports 80/443
3. Run certbot manually: `sudo certbot certonly --nginx -d your-domain.com`

### Service won't start

1. Check logs: `sudo journalctl -u service-name -n 100`
2. Verify Python/Node paths in service files
3. Check environment file exists and is readable

## Maintenance

### Backup

```bash
# Backup script
#!/bin/bash
BACKUP_DIR="/backup/email-client-cli"
mkdir -p $BACKUP_DIR

# Database
cp /opt/email-client-cli/order_tracking.db $BACKUP_DIR/order_tracking_$(date +%Y%m%d).db

# Configuration
cp /opt/email-client-cli/.env.production $BACKUP_DIR/

# Logs (optional)
tar -czf $BACKUP_DIR/logs_$(date +%Y%m%d).tar.gz /opt/email-client-cli/logs/
```

### Updates

```bash
# Stop services
sudo systemctl stop email-processor email-admin-backend

# Pull updates
cd /opt/email-client-cli
sudo -u emailbot git pull

# Update dependencies
sudo -u emailbot venv/bin/pip install -r requirements.txt
sudo -u emailbot admin_panel/backend/venv/bin/pip install -r admin_panel/backend/requirements.txt

# Rebuild frontend
cd admin_panel/frontend
sudo -u emailbot npm ci
sudo -u emailbot VITE_API_URL="https://api.your-domain.com" npm run build

# Restart services
sudo systemctl start email-processor email-admin-backend
```

## Support

For issues or questions:
1. Check logs in `/opt/email-client-cli/logs/`
2. Review systemd journal: `journalctl -u email-processor`
3. Verify environment configuration
4. Check nginx error logs: `/var/log/nginx/email-admin-error.log`