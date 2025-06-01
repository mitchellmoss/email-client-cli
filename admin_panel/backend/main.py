"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os
from pathlib import Path

# Add parent directories to path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(current_dir))

# Now import with absolute paths
from config import settings
from database import engine, Base
from api import auth, orders, products, email_config, analytics, system, email_templates
from models import user as user_models
from auth import get_password_hash
from database import get_db_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create default admin user if not exists
    with get_db_session() as db:
        from models.user import User
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
# Use property access for dynamic CORS origins
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
app.include_router(email_templates.router, prefix=f"{settings.api_prefix}/email-templates", tags=["email-templates"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Email Order Processing Admin Panel API"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}