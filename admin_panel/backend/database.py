"""Database configuration and session management."""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

try:
    from .config import settings
except ImportError:
    from config import settings

# Create engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Metadata for existing tables (lazy loaded to avoid startup delays)
_metadata = None

def get_reflected_metadata():
    """Get reflected metadata, loading it lazily to avoid startup delays."""
    global _metadata
    if _metadata is None:
        _metadata = MetaData()
        _metadata.reflect(bind=engine)
    return _metadata


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