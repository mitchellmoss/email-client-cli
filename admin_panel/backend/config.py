"""Configuration management for admin panel."""

from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pathlib import Path

# Get the project root directory  
PROJECT_ROOT = Path(__file__).parent.parent.parent

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
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Admin user (for initial setup)
    admin_email: str = "admin@example.com"
    admin_password: str = "changeme"
    
    # Email Configuration (from main .env file)
    # IMAP Settings
    imap_server: str = ""
    imap_port: int = 993
    email_address: str = ""
    email_password: str = ""
    
    # SMTP Settings
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    
    # Recipients
    cs_email: str = ""
    laticrete_cs_email: str = ""
    
    # Claude API
    anthropic_api_key: str = ""
    
    # Processing Settings
    check_interval_minutes: int = 5
    log_level: str = "INFO"
    log_file: str = "email_processor.log"
    
    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        case_sensitive = False
        env_file_encoding = 'utf-8'


settings = Settings()