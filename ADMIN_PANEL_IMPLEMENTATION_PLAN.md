# Email Order Processing Admin Panel - Implementation Plan

## Overview
This plan outlines the step-by-step implementation of a web-based admin panel for the email order processing system. The panel will provide a UI for monitoring orders, managing product mappings, configuring email settings, and viewing analytics.

## Architecture Overview

### Tech Stack
- **Backend**: FastAPI (Python) - integrates seamlessly with existing Python modules
- **Frontend**: React with TypeScript, Tailwind CSS, shadcn/ui components
- **Database**: SQLite (existing) + Alembic for migrations
- **Authentication**: JWT tokens with FastAPI security
- **Deployment**: Docker containers with nginx reverse proxy

## Project Structure

```
email-client-cli/
├── existing files...
├── admin_panel/
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Configuration management
│   │   ├── database.py             # Database connection/sessions
│   │   ├── auth.py                 # Authentication logic
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── order.py            # Order models
│   │   │   ├── user.py             # User model
│   │   │   ├── product.py          # Product mapping models
│   │   │   └── email_config.py     # Email configuration models
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── order.py            # Pydantic schemas
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   └── email_config.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Auth endpoints
│   │   │   ├── orders.py           # Order management endpoints
│   │   │   ├── products.py         # Product mapping endpoints
│   │   │   ├── email_config.py     # Email config endpoints
│   │   │   ├── analytics.py        # Analytics endpoints
│   │   │   └── system.py           # System control endpoints
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── order_service.py    # Business logic
│   │   │   ├── email_service.py
│   │   │   └── analytics_service.py
│   │   ├── migrations/             # Alembic migrations
│   │   │   └── alembic.ini
│   │   └── requirements.txt
│   │
│   ├── frontend/
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── vite.config.ts
│   │   ├── tailwind.config.js
│   │   ├── public/
│   │   └── src/
│   │       ├── main.tsx
│   │       ├── App.tsx
│   │       ├── api/              # API client
│   │       ├── components/       # Reusable components
│   │       ├── pages/           # Page components
│   │       ├── hooks/           # Custom hooks
│   │       ├── store/           # State management
│   │       └── utils/           # Utilities
│   │
│   └── docker/
│       ├── Dockerfile.backend
│       ├── Dockerfile.frontend
│       ├── docker-compose.yml
│       └── nginx.conf
```

## Implementation Steps

### Phase 1: Backend Foundation (Days 1-3)

#### Step 1: Set up FastAPI Backend
Create the basic FastAPI application structure with database integration.

**File: admin_panel/backend/requirements.txt**
```txt
# Web framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.25
alembic==1.13.1

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Validation
pydantic==2.5.3
pydantic-settings==2.1.0
email-validator==2.1.0

# CORS
python-cors==1.0.0

# Development
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
```

**File: admin_panel/backend/config.py**
```python
"""Configuration management for admin panel."""

from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    api_title: str = "Email Order Admin Panel"
    api_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = f"sqlite:///{PROJECT_ROOT}/order_tracking.db"
    
    # Integration with existing system
    project_root: Path = PROJECT_ROOT
    email_processor_config: Path = PROJECT_ROOT / ".env"
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]
    
    # Admin user (for initial setup)
    admin_email: str = "admin@example.com"
    admin_password: str = "changeme"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
```

**File: admin_panel/backend/database.py**
```python
"""Database configuration and session management."""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from .config import settings

# Create engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Metadata for existing tables
metadata = MetaData()
metadata.reflect(bind=engine)


def get_db():
    """Dependency for FastAPI to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**File: admin_panel/backend/models/user.py**
```python
"""User model for authentication."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from ..database import Base


class User(Base):
    """Admin user model."""
    
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**File: admin_panel/backend/auth.py**
```python
"""Authentication logic."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models.user import User
from .schemas.user import TokenData

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure the current user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

**File: admin_panel/backend/main.py**
```python
"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from .config import settings
from .database import engine, Base
from .api import auth, orders, products, email_config, analytics, system
from .models import user as user_models
from .auth import get_password_hash
from .database import get_db_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create default admin user if not exists
    with get_db_session() as db:
        from .models.user import User
        admin = db.query(User).filter(User.email == settings.admin_email).first()
        if not admin:
            admin = User(
                email=settings.admin_email,
                hashed_password=get_password_hash(settings.admin_password),
                is_superuser=True
            )
            db.add(admin)
            db.commit()
    
    yield
    # Cleanup


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.api_prefix}/auth", tags=["auth"])
app.include_router(orders.router, prefix=f"{settings.api_prefix}/orders", tags=["orders"])
app.include_router(products.router, prefix=f"{settings.api_prefix}/products", tags=["products"])
app.include_router(email_config.router, prefix=f"{settings.api_prefix}/email-config", tags=["email-config"])
app.include_router(analytics.router, prefix=f"{settings.api_prefix}/analytics", tags=["analytics"])
app.include_router(system.router, prefix=f"{settings.api_prefix}/system", tags=["system"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Email Order Processing Admin Panel API"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
```

#### Step 2: Create API Endpoints

**File: admin_panel/backend/api/auth.py**
```python
"""Authentication endpoints."""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..schemas.user import Token, UserResponse, UserCreate
from ..auth import (
    verify_password,
    create_access_token,
    get_current_active_user,
    get_password_hash
)
from ..config import settings

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login endpoint."""
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new user (superuser only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        is_active=user_data.is_active,
        is_superuser=user_data.is_superuser
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user
```

**File: admin_panel/backend/api/orders.py**
```python
"""Order management endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
from datetime import datetime, timedelta

from ..database import get_db
from ..auth import get_current_active_user
from ..models.user import User
from ..schemas.order import OrderResponse, OrderDetail, OrderStats
from ..services.order_service import OrderService

router = APIRouter()


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of orders with filtering and pagination."""
    service = OrderService(db)
    return service.get_orders(
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/stats", response_model=OrderStats)
async def get_order_stats(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get order statistics."""
    service = OrderService(db)
    return service.get_statistics(days)


@router.get("/{order_id}", response_model=OrderDetail)
async def get_order_detail(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information about a specific order."""
    service = OrderService(db)
    order = service.get_order_detail(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order


@router.post("/{order_id}/resend")
async def resend_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Resend an order email."""
    service = OrderService(db)
    success = service.resend_order(order_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to resend order")
    
    return {"message": "Order resent successfully"}


@router.delete("/{order_id}")
async def delete_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an order (superuser only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    service = OrderService(db)
    success = service.delete_order(order_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"message": "Order deleted successfully"}
```

### Phase 2: Frontend Setup (Days 4-6)

#### Step 3: Initialize React Frontend

**File: admin_panel/frontend/package.json**
```json
{
  "name": "email-order-admin-panel",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.1",
    "axios": "^1.6.5",
    "react-query": "^3.39.3",
    "zustand": "^4.4.7",
    "@radix-ui/react-alert-dialog": "^1.0.5",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-label": "^2.0.2",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-separator": "^1.0.3",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-toast": "^1.1.5",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "date-fns": "^3.2.0",
    "lucide-react": "^0.309.0",
    "recharts": "^2.10.4",
    "tailwind-merge": "^2.2.0",
    "tailwindcss-animate": "^1.0.7"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@typescript-eslint/eslint-plugin": "^6.14.0",
    "@typescript-eslint/parser": "^6.14.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.55.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.3.0",
    "typescript": "^5.2.2",
    "vite": "^5.0.8"
  }
}
```

**File: admin_panel/frontend/src/App.tsx**
```tsx
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from '@/components/ui/toaster';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import Layout from '@/components/Layout';
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import Orders from '@/pages/Orders';
import OrderDetail from '@/pages/OrderDetail';
import Products from '@/pages/Products';
import EmailConfig from '@/pages/EmailConfig';
import SystemControl from '@/pages/SystemControl';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <Layout />
                </PrivateRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="orders" element={<Orders />} />
              <Route path="orders/:orderId" element={<OrderDetail />} />
              <Route path="products" element={<Products />} />
              <Route path="email-config" element={<EmailConfig />} />
              <Route path="system" element={<SystemControl />} />
            </Route>
          </Routes>
          <Toaster />
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
```

**File: admin_panel/frontend/src/pages/Dashboard.tsx**
```tsx
import { useQuery } from 'react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Overview } from '@/components/Overview';
import { RecentOrders } from '@/components/RecentOrders';
import { api } from '@/api/client';
import { Loader2 } from 'lucide-react';

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery(
    ['orderStats'],
    () => api.get('/orders/stats').then(res => res.data)
  );

  const { data: recentOrders, isLoading: ordersLoading } = useQuery(
    ['recentOrders'],
    () => api.get('/orders?limit=10').then(res => res.data)
  );

  const { data: systemStatus } = useQuery(
    ['systemStatus'],
    () => api.get('/system/status').then(res => res.data),
    { refetchInterval: 30000 } // Refresh every 30 seconds
  );

  if (statsLoading || ordersLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
      </div>
      
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Total Orders (7d)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.total_orders_sent || 0}</div>
                <p className="text-xs text-muted-foreground">
                  {stats?.duplicate_attempts_blocked || 0} duplicates blocked
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  System Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {systemStatus?.is_running ? 'Running' : 'Stopped'}
                </div>
                <p className="text-xs text-muted-foreground">
                  Last check: {systemStatus?.last_check || 'Never'}
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Processing Rate
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {systemStatus?.processing_rate || 0}/hr
                </div>
                <p className="text-xs text-muted-foreground">
                  Average processing time
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Error Rate
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {systemStatus?.error_rate || 0}%
                </div>
                <p className="text-xs text-muted-foreground">
                  Last 24 hours
                </p>
              </CardContent>
            </Card>
          </div>
          
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            <Card className="col-span-4">
              <CardHeader>
                <CardTitle>Overview</CardTitle>
              </CardHeader>
              <CardContent className="pl-2">
                <Overview data={stats?.daily_counts || []} />
              </CardContent>
            </Card>
            
            <Card className="col-span-3">
              <CardHeader>
                <CardTitle>Recent Orders</CardTitle>
                <CardDescription>
                  Latest processed orders
                </CardDescription>
              </CardHeader>
              <CardContent>
                <RecentOrders orders={recentOrders || []} />
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

### Phase 3: Integration & Services (Days 7-9)

#### Step 4: Create Service Layer

**File: admin_panel/backend/services/order_service.py**
```python
"""Order service for business logic."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
import json
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.order_tracker import OrderTracker
from src.email_sender import EmailSender
from src.order_formatter import OrderFormatter
from ..config import settings


class OrderService:
    """Service for order-related operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.order_tracker = OrderTracker(str(settings.project_root / "order_tracking.db"))
    
    def get_orders(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get filtered list of orders."""
        query = """
            SELECT 
                id,
                order_id,
                email_subject,
                sent_at,
                sent_to,
                customer_name,
                tileware_products,
                order_total,
                created_at
            FROM sent_orders
            WHERE 1=1
        """
        
        params = {}
        
        if search:
            query += """ AND (
                order_id LIKE :search OR 
                customer_name LIKE :search OR 
                email_subject LIKE :search
            )"""
            params['search'] = f'%{search}%'
        
        if date_from:
            query += " AND created_at >= :date_from"
            params['date_from'] = date_from
        
        if date_to:
            query += " AND created_at <= :date_to"
            params['date_to'] = date_to
        
        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :skip"
        params['limit'] = limit
        params['skip'] = skip
        
        result = self.db.execute(text(query), params)
        
        orders = []
        for row in result:
            order = dict(row._mapping)
            if order['tileware_products']:
                order['tileware_products'] = json.loads(order['tileware_products'])
            orders.append(order)
        
        return orders
    
    def get_order_detail(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed order information."""
        order = self.order_tracker.get_order_details(order_id)
        if order:
            # Get processing history
            order['history'] = self.order_tracker.get_order_history(order_id)
        return order
    
    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get order statistics."""
        return self.order_tracker.get_statistics(days)
    
    def resend_order(self, order_id: str) -> bool:
        """Resend an order email."""
        order = self.order_tracker.get_order_details(order_id)
        if not order:
            return False
        
        try:
            # Initialize email sender
            sender = EmailSender()
            
            # Send the formatted content
            success = sender.send_order_email(
                to_email=order['sent_to'],
                order_content=order['formatted_content'],
                order_id=order_id
            )
            
            if success:
                # Log the resend action
                self.order_tracker._log_action(
                    order_id,
                    "resent",
                    f"Order resent to {order['sent_to']}"
                )
            
            return success
            
        except Exception as e:
            self.order_tracker._log_action(
                order_id,
                "resend_error",
                str(e)
            )
            return False
    
    def delete_order(self, order_id: str) -> bool:
        """Delete an order record."""
        try:
            # Delete from sent_orders
            self.db.execute(
                text("DELETE FROM sent_orders WHERE order_id = :order_id"),
                {"order_id": order_id}
            )
            
            # Delete from processing log
            self.db.execute(
                text("DELETE FROM order_processing_log WHERE order_id = :order_id"),
                {"order_id": order_id}
            )
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            return False
```

### Phase 4: Advanced Features (Days 10-12)

#### Step 5: Product Mapping Management

**File: admin_panel/backend/models/product.py**
```python
"""Product mapping models."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.sql import func

from ..database import Base


class ProductMapping(Base):
    """Product name to SKU mapping."""
    
    __tablename__ = "product_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    product_type = Column(String, nullable=False)  # 'tileware' or 'laticrete'
    original_name = Column(String, nullable=False, index=True)
    mapped_name = Column(String, nullable=False)
    sku = Column(String, nullable=False, index=True)
    price = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String)
    notes = Column(Text)
```

**File: admin_panel/backend/api/products.py**
```python
"""Product mapping endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
import pandas as pd
import io

from ..database import get_db
from ..auth import get_current_active_user
from ..models.user import User
from ..models.product import ProductMapping
from ..schemas.product import (
    ProductMappingCreate,
    ProductMappingUpdate,
    ProductMappingResponse
)

router = APIRouter()


@router.get("/mappings", response_model=List[ProductMappingResponse])
async def get_product_mappings(
    product_type: Optional[str] = Query(None, regex="^(tileware|laticrete)$"),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get product mappings with filtering."""
    query = db.query(ProductMapping)
    
    if product_type:
        query = query.filter(ProductMapping.product_type == product_type)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (ProductMapping.original_name.ilike(search_term)) |
            (ProductMapping.mapped_name.ilike(search_term)) |
            (ProductMapping.sku.ilike(search_term))
        )
    
    if is_active is not None:
        query = query.filter(ProductMapping.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()


@router.post("/mappings", response_model=ProductMappingResponse)
async def create_product_mapping(
    mapping: ProductMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new product mapping."""
    # Check if mapping already exists
    existing = db.query(ProductMapping).filter(
        ProductMapping.product_type == mapping.product_type,
        ProductMapping.original_name == mapping.original_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Mapping for this product already exists"
        )
    
    db_mapping = ProductMapping(
        **mapping.dict(),
        created_by=current_user.email
    )
    
    db.add(db_mapping)
    db.commit()
    db.refresh(db_mapping)
    
    return db_mapping


@router.put("/mappings/{mapping_id}", response_model=ProductMappingResponse)
async def update_product_mapping(
    mapping_id: int,
    mapping: ProductMappingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a product mapping."""
    db_mapping = db.query(ProductMapping).filter(
        ProductMapping.id == mapping_id
    ).first()
    
    if not db_mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    for field, value in mapping.dict(exclude_unset=True).items():
        setattr(db_mapping, field, value)
    
    db.commit()
    db.refresh(db_mapping)
    
    return db_mapping


@router.delete("/mappings/{mapping_id}")
async def delete_product_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a product mapping."""
    db_mapping = db.query(ProductMapping).filter(
        ProductMapping.id == mapping_id
    ).first()
    
    if not db_mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    db.delete(db_mapping)
    db.commit()
    
    return {"message": "Mapping deleted successfully"}


@router.post("/mappings/import")
async def import_product_mappings(
    file: UploadFile = File(...),
    product_type: str = Query(..., regex="^(tileware|laticrete)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Import product mappings from Excel/CSV file."""
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(
            status_code=400,
            detail="File must be Excel (.xlsx, .xls) or CSV"
        )
    
    try:
        # Read file
        contents = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        # Validate columns
        required_columns = ['original_name', 'mapped_name', 'sku']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(
                status_code=400,
                detail=f"File must contain columns: {required_columns}"
            )
        
        # Import mappings
        imported = 0
        skipped = 0
        
        for _, row in df.iterrows():
            # Check if exists
            existing = db.query(ProductMapping).filter(
                ProductMapping.product_type == product_type,
                ProductMapping.original_name == row['original_name']
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            mapping = ProductMapping(
                product_type=product_type,
                original_name=row['original_name'],
                mapped_name=row['mapped_name'],
                sku=row['sku'],
                price=row.get('price'),
                created_by=current_user.email
            )
            
            db.add(mapping)
            imported += 1
        
        db.commit()
        
        return {
            "message": f"Import completed",
            "imported": imported,
            "skipped": skipped
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Phase 5: Deployment & Testing (Days 13-14)

#### Step 6: Docker Configuration

**File: admin_panel/docker/docker-compose.yml**
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ..
      dockerfile: docker/Dockerfile.backend
    environment:
      - DATABASE_URL=sqlite:////app/data/order_tracking.db
      - PROJECT_ROOT=/app
    volumes:
      - ../../order_tracking.db:/app/data/order_tracking.db
      - ../../.env:/app/.env
      - ../../src:/app/src
      - ../../resources:/app/resources
    ports:
      - "8000:8000"
    restart: unless-stopped

  frontend:
    build:
      context: ..
      dockerfile: docker/Dockerfile.frontend
    environment:
      - VITE_API_URL=http://localhost:8000
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
```

**File: admin_panel/docker/Dockerfile.backend**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend/
COPY ../src/ ./src/
COPY ../resources/ ./resources/

# Create data directory
RUN mkdir -p /app/data

# Run application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**File: admin_panel/docker/Dockerfile.frontend**
```dockerfile
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./
RUN npm ci

# Copy source
COPY frontend/ .

# Build
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY docker/nginx-frontend.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Testing Strategy

**File: admin_panel/backend/tests/test_orders.py**
```python
"""Test order endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..main import app
from ..database import Base, get_db
from ..auth import get_password_hash
from ..models.user import User

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture
def test_user():
    """Create test user."""
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpass"),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()
    db.close()


@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpass"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_orders(auth_headers):
    """Test getting orders list."""
    response = client.get("/api/v1/orders", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_order_stats(auth_headers):
    """Test getting order statistics."""
    response = client.get("/api/v1/orders/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_orders_sent" in data
    assert "daily_counts" in data


def test_unauthorized_access():
    """Test accessing without authentication."""
    response = client.get("/api/v1/orders")
    assert response.status_code == 401
```

## Quick Start Guide

### 1. Backend Setup
```bash
cd admin_panel/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic init migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# Start server
uvicorn main:app --reload
```

### 2. Frontend Setup
```bash
cd admin_panel/frontend
npm install
npm run dev
```

### 3. Access the Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Default login: admin@example.com / changeme

## Key Integration Points

1. **Order Tracker Integration**: The backend directly uses the existing `OrderTracker` class
2. **Email Service Integration**: Can trigger email sends through existing `EmailSender`
3. **Configuration Sharing**: Reads from the same `.env` file
4. **Database Sharing**: Uses the same SQLite database with additional tables

## Next Steps

1. Implement remaining API endpoints (email config, analytics, system control)
2. Add real-time order monitoring with WebSockets
3. Implement batch operations for orders
4. Add export functionality (CSV, PDF reports)
5. Create automated tests for all endpoints
6. Set up CI/CD pipeline
7. Add monitoring and logging dashboards
8. Implement role-based access control
9. Add email template editor
10. Create mobile-responsive design

This implementation plan provides a solid foundation for building the admin panel while maintaining compatibility with the existing CLI system. The modular architecture allows for incremental development and easy testing of individual components.