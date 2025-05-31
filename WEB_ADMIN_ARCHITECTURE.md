# Email Order Processing Admin Panel - Technical Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Frontend (React + TypeScript)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  Dashboard │ Orders List │ Order Details │ Email Queue │ Settings │ Reports  │
├─────────────────────────────────────────────────────────────────────────────┤
│                         API Gateway (FastAPI)                                │
│                    WebSocket + REST API + SSE Support                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  Auth     │  Orders    │  Email      │  Processing │  Analytics │  Config   │
│  Service  │  Service   │  Service    │  Service    │  Service   │  Service  │
├─────────────────────────────────────────────────────────────────────────────┤
│                          Shared Data Layer                                   │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  SQLite    │  │  Redis      │  │  File Store  │  │  Background Jobs │  │
│  │  Database  │  │  Cache/Queue │  │  (PDFs/Logs) │  │  (Celery)        │  │
│  └────────────┘  └─────────────┘  └──────────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│                    Existing Python Email Processor                           │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  ┌───────────────┐  │
│  │ Email       │  │ Claude API   │  │ Order Tracker │  │ PDF Generator │  │
│  │ Fetcher     │  │ Processor    │  │ (SQLite)      │  │ (Laticrete)   │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend
- **Web Framework**: FastAPI (Python 3.11+)
  - Async support for real-time features
  - Built-in OpenAPI documentation
  - WebSocket support
  - Excellent performance
  - Easy integration with existing Python codebase

- **Database**: 
  - **Primary**: SQLite (existing) with SQLAlchemy ORM
  - **Cache/Queue**: Redis for real-time features and job queuing
  - **Session Store**: Redis with secure session tokens

- **Background Jobs**: Celery with Redis broker
  - Email processing tasks
  - Report generation
  - Scheduled maintenance

- **Authentication**: 
  - JWT tokens with refresh mechanism
  - RBAC (Role-Based Access Control)
  - OAuth2 support for future SSO

### Frontend
- **Framework**: React 18 with TypeScript
  - Type safety for complex order data
  - Modern hooks-based architecture
  - Excellent ecosystem

- **State Management**: Zustand + React Query
  - Zustand for UI state
  - React Query for server state caching
  - Optimistic updates for better UX

- **UI Library**: Ant Design (antd) 5.x
  - Enterprise-ready components
  - Comprehensive data table features
  - Built-in form validation
  - Professional look

- **Real-time**: Socket.io-client
  - WebSocket with fallback
  - Auto-reconnection
  - Event-based updates

- **Build Tools**: Vite
  - Fast development
  - Optimized production builds
  - TypeScript support

## API Design

### RESTful Endpoints

```typescript
// Authentication
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/auth/refresh
GET    /api/auth/me

// Orders
GET    /api/orders                 // List with pagination/filters
GET    /api/orders/:id            // Single order details
POST   /api/orders/:id/resend     // Resend order email
PUT    /api/orders/:id            // Update order (manual edits)
DELETE /api/orders/:id            // Cancel/delete order
GET    /api/orders/:id/history    // Order processing history
GET    /api/orders/export         // Export to CSV/Excel

// Email Queue
GET    /api/emails/queue          // Pending emails
GET    /api/emails/processed      // Processed emails
POST   /api/emails/reprocess/:id  // Reprocess failed email
GET    /api/emails/:id/raw        // View raw email content

// Processing Control
POST   /api/processing/start      // Start email processor
POST   /api/processing/stop       // Stop email processor
GET    /api/processing/status     // Current processor status
POST   /api/processing/run-once   // Trigger single run

// Analytics
GET    /api/analytics/dashboard   // Dashboard stats
GET    /api/analytics/reports     // Available reports
GET    /api/analytics/trends      // Order trends data

// Configuration
GET    /api/config/settings       // Current settings
PUT    /api/config/settings       // Update settings
GET    /api/config/test-email     // Test email connection
GET    /api/config/test-claude    // Test Claude API
```

### WebSocket Events

```typescript
// Server -> Client
'order:new'          // New order processed
'order:updated'      // Order status changed
'order:error'        // Order processing error
'email:received'     // New email received
'email:processed'    // Email processed
'processor:status'   // Processor status change
'system:alert'       // System alerts/errors

// Client -> Server
'subscribe:orders'   // Subscribe to order updates
'subscribe:emails'   // Subscribe to email updates
'filter:update'      // Update real-time filters
```

## Database Schema Modifications

```sql
-- Extend existing tables
ALTER TABLE sent_orders ADD COLUMN reviewed_at TIMESTAMP;
ALTER TABLE sent_orders ADD COLUMN reviewed_by TEXT;
ALTER TABLE sent_orders ADD COLUMN manual_edits TEXT;
ALTER TABLE sent_orders ADD COLUMN tags TEXT;
ALTER TABLE sent_orders ADD COLUMN priority INTEGER DEFAULT 0;

-- New tables for web admin
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE user_sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    details TEXT,
    ip_address TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE email_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_uid TEXT UNIQUE,
    subject TEXT,
    from_address TEXT,
    received_at TIMESTAMP,
    status TEXT DEFAULT 'pending',
    processed_at TIMESTAMP,
    error_message TEXT,
    raw_content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE system_config (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX idx_email_queue_status ON email_queue(status);
```

## Project Structure

```
email-client-cli/
├── backend/                      # New FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # Database setup
│   │   ├── dependencies.py      # Shared dependencies
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # Auth endpoints
│   │   │   ├── orders.py        # Order endpoints
│   │   │   ├── emails.py        # Email endpoints
│   │   │   ├── processing.py    # Processing control
│   │   │   ├── analytics.py     # Analytics endpoints
│   │   │   └── config.py        # Config endpoints
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # User models
│   │   │   ├── order.py         # Order models
│   │   │   └── email.py         # Email models
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # Auth schemas
│   │   │   ├── order.py         # Order schemas
│   │   │   └── email.py         # Email schemas
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # Auth service
│   │   │   ├── order.py         # Order service
│   │   │   ├── email.py         # Email service
│   │   │   └── processor.py     # Processor control
│   │   ├── websocket/
│   │   │   ├── __init__.py
│   │   │   ├── manager.py       # WebSocket manager
│   │   │   └── events.py        # Event handlers
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── security.py      # Security utils
│   │       └── pagination.py    # Pagination helpers
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── api/
│   │   │   ├── client.ts        # API client setup
│   │   │   ├── orders.ts        # Order API calls
│   │   │   └── auth.ts          # Auth API calls
│   │   ├── components/
│   │   │   ├── common/
│   │   │   ├── orders/
│   │   │   ├── emails/
│   │   │   └── dashboard/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Orders.tsx
│   │   │   ├── OrderDetail.tsx
│   │   │   ├── Emails.tsx
│   │   │   └── Settings.tsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useAuth.ts
│   │   │   └── useOrders.ts
│   │   ├── store/
│   │   │   ├── auth.ts
│   │   │   └── ui.ts
│   │   ├── types/
│   │   │   ├── order.ts
│   │   │   └── email.ts
│   │   └── utils/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
├── src/                         # Existing CLI code
├── nginx/                       # Nginx config
│   └── nginx.conf
├── docker-compose.yml           # Full stack deployment
└── scripts/
    ├── migrate_db.py           # Database migrations
    └── create_admin.py         # Create admin user
```

## Integration Points

### 1. Database Integration
```python
# backend/app/services/order.py
from src.order_tracker import OrderTracker

class OrderService:
    def __init__(self):
        self.tracker = OrderTracker()  # Reuse existing
    
    async def get_orders(self, filters, pagination):
        # Use existing tracker methods
        return self.tracker.get_sent_orders(
            limit=pagination.limit,
            offset=pagination.offset
        )
```

### 2. Email Processing Control
```python
# backend/app/services/processor.py
import subprocess
import psutil

class ProcessorService:
    def start_processor(self):
        # Start main.py as subprocess
        self.process = subprocess.Popen(
            ["python", "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    
    def stop_processor(self):
        # Gracefully stop the processor
        if self.process:
            self.process.terminate()
```

### 3. Real-time Updates
```python
# backend/app/websocket/manager.py
from src.order_tracker import OrderTracker

class ConnectionManager:
    async def notify_new_order(self, order_id):
        # Broadcast to all connected clients
        await self.broadcast({
            "type": "order:new",
            "data": {"order_id": order_id}
        })
```

## Security Considerations

### Authentication & Authorization
- JWT tokens with 15-minute expiry, 7-day refresh tokens
- Role-based access: Admin, Manager, Viewer
- API key support for programmatic access
- Rate limiting per user/IP

### Data Security
- All passwords hashed with bcrypt
- Sensitive config encrypted at rest
- HTTPS only (enforced by nginx)
- CORS configured for frontend domain only
- SQL injection prevention via parameterized queries
- XSS protection via React's built-in escaping

### Audit Trail
- All data modifications logged
- User actions tracked with IP
- Sensitive data access logged
- Log retention policy (90 days)

## Performance Optimization

### Backend
- **Connection Pooling**: SQLite with WAL mode
- **Redis Caching**: 
  - Order lists (5-minute TTL)
  - User sessions
  - Real-time metrics
- **Async Processing**: FastAPI async endpoints
- **Pagination**: Cursor-based for large datasets
- **Query Optimization**: Proper indexes on all foreign keys

### Frontend
- **Code Splitting**: Route-based lazy loading
- **Data Caching**: React Query with stale-while-revalidate
- **Virtualization**: Virtual scrolling for large lists
- **Optimistic Updates**: Immediate UI feedback
- **Bundle Optimization**: Tree shaking, minification

### Monitoring
- **APM**: Sentry for error tracking
- **Metrics**: Prometheus + Grafana
- **Logs**: Structured logging with correlation IDs
- **Health Checks**: /health endpoint for monitoring

## Deployment Strategy

### Development
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Production (Docker Compose)
```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    environment:
      - DATABASE_URL=sqlite:///app/order_tracking.db
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./order_tracking.db:/app/order_tracking.db
      - ./resources:/app/resources
    depends_on:
      - redis

  frontend:
    build: ./frontend
    environment:
      - VITE_API_URL=http://backend:8000

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend

  celery:
    build: ./backend
    command: celery -A app.celery worker --loglevel=info
    depends_on:
      - redis
      - backend
```

### Incremental Rollout
1. **Phase 1**: Deploy read-only dashboard
   - View orders and statistics
   - No processing control
   
2. **Phase 2**: Add processing control
   - Start/stop processor
   - Manual order resending
   
3. **Phase 3**: Full features
   - Order editing
   - Email queue management
   - Advanced analytics

## Migration Plan

### Step 1: Database Preparation
```python
# scripts/migrate_db.py
def add_web_tables():
    """Add new tables for web admin"""
    # Run SQL migrations
    # Create admin user
    # Set up initial config
```

### Step 2: Parallel Operation
- Web admin runs alongside CLI
- Both use same SQLite database
- Web provides monitoring only initially

### Step 3: Gradual Feature Addition
- Add control features one by one
- Test thoroughly in staging
- Roll back if issues arise

### Step 4: Full Migration
- Web becomes primary interface
- CLI remains for automation/backup
- Document new workflows

This architecture provides a solid foundation for building the web admin panel while maintaining compatibility with the existing system. The modular design allows for incremental development and deployment without disrupting current operations.