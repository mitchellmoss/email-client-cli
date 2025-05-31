# Email Client CLI Admin Panel - Setup Guide

## Overview
A complete web-based admin panel for the Email Client CLI system with:
- FastAPI backend with JWT authentication
- React frontend with TypeScript and Tailwind CSS
- Real-time system monitoring
- Order management and resending
- Product matching for Laticrete items
- Email configuration management

## Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn
- The main email-client-cli system configured and working

## Quick Start

### 1. Backend Setup

Navigate to the backend directory:
```bash
cd admin_panel/backend
```

Install dependencies and start the server:
```bash
# Using the provided script
chmod +x run_dev.sh
./run_dev.sh

# Or manually
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install psutil  # For system monitoring
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 2. Frontend Setup

In a new terminal, navigate to the frontend directory:
```bash
cd admin_panel/frontend
```

Install dependencies and start the development server:
```bash
npm install
npm run dev
```

The frontend will be available at:
- http://localhost:5173

### 3. Default Login Credentials
- Email: `admin@example.com`
- Password: `changeme`

**Important**: Change these credentials after first login!

## Features

### Dashboard
- System status monitoring
- Order statistics (7-day view)
- Recent logs preview
- Real-time updates every 30 seconds

### Orders Management
- View all processed orders
- Search and filter orders
- View detailed order information
- Resend orders with one click
- Delete orders (admin only)

### Product Matching
- Map unmatched Laticrete products to SKUs
- Set pricing for matched products
- Edit existing mappings
- Search functionality

### Settings
- **Email Configuration**
  - IMAP settings for reading emails
  - SMTP settings for sending emails
  - Customer service email addresses
  - Check interval configuration
  - Connection testing

- **Email Templates**
  - Customize email subject and body
  - Use variables like {order_id}, {customer_name}

- **System Control**
  - Start/stop email processor
  - View system status and uptime
  - Monitor real-time logs

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/users` - Create user (admin only)

### Orders
- `GET /api/v1/orders` - List orders
- `GET /api/v1/orders/stats` - Get statistics
- `GET /api/v1/orders/{order_id}` - Get order details
- `POST /api/v1/orders/{order_id}/resend` - Resend order
- `DELETE /api/v1/orders/{order_id}` - Delete order

### Products
- `GET /api/v1/products/mappings` - List mappings
- `POST /api/v1/products/mappings` - Create mapping
- `PUT /api/v1/products/mappings/{id}` - Update mapping
- `DELETE /api/v1/products/mappings/{id}` - Delete mapping

### Email Configuration
- `GET /api/v1/email-config` - Get config
- `PUT /api/v1/email-config` - Update config
- `POST /api/v1/email-config/test-connection` - Test connection

### System
- `GET /api/v1/system/status` - Get status
- `POST /api/v1/system/start` - Start processor
- `POST /api/v1/system/stop` - Stop processor
- `GET /api/v1/system/logs` - View logs

## Troubleshooting

### Backend Issues
1. **Port already in use**: Change port in `uvicorn` command
2. **Import errors**: Ensure you're in the virtual environment
3. **Database errors**: Check that `order_tracking.db` exists in the root directory
4. **Permission errors**: Ensure the user has read/write access to the database

### Frontend Issues
1. **Build errors**: Delete `node_modules` and reinstall
2. **API connection errors**: Check that backend is running on port 8000
3. **Blank page**: Check browser console for errors
4. **Style issues**: Ensure Tailwind CSS is properly configured

### Common Problems
1. **Can't login**: 
   - Verify backend is running
   - Check default credentials
   - Look for errors in backend logs

2. **Orders not showing**:
   - Ensure the main email processor has run at least once
   - Check that `order_tracking.db` has data

3. **System control not working**:
   - Ensure the backend has permission to control processes
   - Check that the main `main.py` is in the correct path

## Development

### Adding New Features
1. Backend: Add new endpoints in `admin_panel/backend/api/`
2. Frontend: Add new pages in `admin_panel/frontend/src/pages/`
3. Update navigation in `Layout.tsx`
4. Add routes in `App.tsx`

### Building for Production

Backend:
```bash
# Use a production ASGI server
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

Frontend:
```bash
npm run build
# Serve the dist folder with a web server
```

### Environment Variables
Create a `.env` file in the backend directory:
```env
SECRET_KEY=your-secret-key-here
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=secure-password
DATABASE_URL=sqlite:///../../../order_tracking.db
```

## Security Considerations
1. Change default admin credentials immediately
2. Use strong SECRET_KEY for JWT tokens
3. Enable HTTPS in production
4. Restrict CORS origins in production
5. Implement rate limiting
6. Regular security updates

## Next Steps
1. Deploy behind a reverse proxy (nginx/Apache)
2. Set up SSL certificates
3. Configure monitoring and alerting
4. Implement automated backups
5. Add user management features