# Email Order Processing Admin Panel

A web-based administration panel for the Email Client CLI system that processes orders from Tile Pro Depot.

## Quick Start

### Backend Setup

1. Navigate to the backend directory:
```bash
cd admin_panel/backend
```

2. Run the development server:
```bash
./run_dev.sh
```

Or manually:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install psutil  # For system monitoring
uvicorn main:app --reload
```

3. Access the API:
- API URL: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Alternative API Docs: http://localhost:8000/redoc

4. Default login credentials:
- Email: admin@example.com
- Password: changeme

### Frontend Setup (Coming Soon)

The React frontend will be added in the next phase. For now, you can test the API using:
- The interactive API documentation at http://localhost:8000/docs
- Tools like Postman or curl
- Python scripts using the requests library

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login with email/password
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/users` - Create new user (superuser only)

### Orders
- `GET /api/v1/orders` - List orders with filtering
- `GET /api/v1/orders/stats` - Get order statistics
- `GET /api/v1/orders/{order_id}` - Get order details
- `POST /api/v1/orders/{order_id}/resend` - Resend an order
- `DELETE /api/v1/orders/{order_id}` - Delete an order (superuser only)

### Product Mappings
- `GET /api/v1/products/mappings` - List product mappings
- `POST /api/v1/products/mappings` - Create mapping
- `PUT /api/v1/products/mappings/{id}` - Update mapping
- `DELETE /api/v1/products/mappings/{id}` - Delete mapping

### Email Configuration
- `GET /api/v1/email-config` - Get current config
- `PUT /api/v1/email-config` - Update config
- `POST /api/v1/email-config/test-connection` - Test email connection

### Analytics
- `GET /api/v1/analytics/overview` - Get analytics overview
- `GET /api/v1/analytics/email-metrics` - Get email processing metrics
- `GET /api/v1/analytics/export` - Export analytics data

### System Control
- `GET /api/v1/system/status` - Get system status
- `POST /api/v1/system/start` - Start email processor
- `POST /api/v1/system/stop` - Stop email processor
- `POST /api/v1/system/restart` - Restart email processor
- `GET /api/v1/system/logs` - View system logs
- `DELETE /api/v1/system/logs` - Clear logs (superuser only)

## Testing the API

### 1. Get Authentication Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme"
```

### 2. Use Token for Authenticated Requests

```bash
TOKEN="your-token-here"

# Get orders
curl -X GET "http://localhost:8000/api/v1/orders" \
  -H "Authorization: Bearer $TOKEN"

# Get system status
curl -X GET "http://localhost:8000/api/v1/system/status" \
  -H "Authorization: Bearer $TOKEN"
```

## Architecture

The admin panel consists of:

1. **FastAPI Backend**: 
   - RESTful API with JWT authentication
   - Direct integration with existing Python modules
   - SQLite database (shared with CLI system)

2. **React Frontend** (coming soon):
   - TypeScript for type safety
   - Tailwind CSS for styling
   - shadcn/ui components
   - React Query for data fetching

3. **Integration Points**:
   - Uses the same SQLite database as the CLI
   - Can control the CLI process (start/stop)
   - Reads from the same .env configuration
   - Leverages existing email processing modules

## Development

### Adding New Endpoints

1. Create schema in `schemas/`
2. Add model if needed in `models/`
3. Create API endpoint in `api/`
4. Add business logic in `services/`
5. Update main.py to include new router

### Database Migrations

When adding new tables:

```bash
cd admin_panel/backend
alembic init migrations  # Only first time
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Security

- JWT tokens for authentication
- Password hashing with bcrypt
- CORS protection
- Input validation with Pydantic
- SQL injection protection via SQLAlchemy

## Next Steps

1. Implement React frontend
2. Add WebSocket support for real-time updates
3. Implement batch operations
4. Add export functionality
5. Create Docker deployment configuration