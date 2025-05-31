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