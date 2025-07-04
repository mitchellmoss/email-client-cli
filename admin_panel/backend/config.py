"""Configuration management for admin panel."""

from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pathlib import Path
import secrets

# Get the project root directory  
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Production mode detection
IS_PRODUCTION = os.getenv("PRODUCTION", "false").lower() == "true"

class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    api_title: str = "Email Order Admin Panel"
    api_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT}/order_tracking.db")
    database_path: str = os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "order_tracking.db"))
    
    # Integration with existing system
    project_root: Path = Path(os.getenv("PROJECT_ROOT", str(PROJECT_ROOT)))
    email_processor_config: Path = Path(os.getenv("EMAIL_PROCESSOR_CONFIG", str(PROJECT_ROOT / ".env")))
    
    # CORS
    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins from environment or default."""
        if IS_PRODUCTION:
            # In production, get from environment variable
            origins_str = os.getenv("CORS_ORIGINS", "")
            frontend_url = os.getenv("FRONTEND_URL", "")
            
            origins = []
            if frontend_url:
                origins.append(frontend_url)
            
            if origins_str:
                origins.extend([origin.strip() for origin in origins_str.split(",") if origin.strip()])
            
            return origins if origins else ["http://localhost:3000", "http://localhost:5173"]
        else:
            # In development, allow localhost and local network access
            origins = [
                "http://localhost:3000", 
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173"
            ]
            
            # Add support for dynamically configured CORS origins from environment
            env_origins = os.getenv("CORS_ORIGINS", "")
            if env_origins:
                # Parse comma-separated origins from environment
                for origin in env_origins.split(","):
                    origin = origin.strip()
                    if origin and origin not in origins:
                        origins.append(origin)
            
            # If no environment CORS set, add common local network ranges
            if not env_origins:
                # Add support for common local network IP ranges
                # 192.168.x.x range
                for subnet in [0, 1, 100, 131]:  # Common subnets including yours
                    origins.extend([
                        f"http://192.168.{subnet}.{j}:5173" 
                        for j in range(1, 255)
                    ][:50])  # Limit per subnet
                
                # 10.x.x.x range (common for some local networks)
                origins.extend([
                    f"http://10.0.0.{j}:5173" 
                    for j in range(1, 255)
                ][:50])
            
            return origins
    
    # Admin user (for initial setup)
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "changeme")
    
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
    
    # Email Templates (configurable via admin UI)
    tileware_email_subject: str = "TileWare Order #{order_id} - Action Required"
    tileware_email_body: str = "{products}\n\nSHIP TO:\n{shipping_method}\n\n{shipping_address}\n\n::::"
    laticrete_email_subject: str = "Laticrete Order #{order_id} - {customer_name}"
    laticrete_email_body: str = "New Laticrete Order\n\nPlease find the attached order form for processing.\n\nCustomer: {customer_name}\nOrder ID: {order_id}\n\nPlease verify pricing before processing."
    email_signature_text: str = ""
    
    class Config:
        env_file = os.getenv("ENV_FILE", str(PROJECT_ROOT / ".env"))
        case_sensitive = False
        env_file_encoding = 'utf-8'
        extra = "allow"  # Allow extra fields from .env
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate production settings
        if IS_PRODUCTION:
            if self.secret_key == "your-secret-key-change-in-production":
                raise ValueError("SECRET_KEY must be set in production!")
            if self.admin_password == "changeme":
                raise ValueError("ADMIN_PASSWORD must be changed in production!")


settings = Settings()