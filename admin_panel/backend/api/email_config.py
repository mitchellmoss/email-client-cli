"""Email configuration endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import os
from pathlib import Path
from dotenv import load_dotenv, set_key

from database import get_db
from auth import get_current_active_user
from models.user import User
from config import settings

router = APIRouter()


@router.get("/")
async def get_email_config(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get current email configuration."""
    # Load from .env file
    env_path = settings.email_processor_config
    load_dotenv(env_path)
    
    config = {
        "imap": {
            "server": os.getenv("IMAP_SERVER", ""),
            "port": int(os.getenv("IMAP_PORT", "993")),
            "email_address": os.getenv("EMAIL_ADDRESS", ""),
            "has_password": bool(os.getenv("EMAIL_PASSWORD"))
        },
        "smtp": {
            "server": os.getenv("SMTP_SERVER", ""),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME", ""),
            "has_password": bool(os.getenv("SMTP_PASSWORD"))
        },
        "recipients": {
            "cs_email": os.getenv("CS_EMAIL", ""),
            "laticrete_cs_email": os.getenv("LATICRETE_CS_EMAIL", "")
        },
        "processing": {
            "check_interval_minutes": int(os.getenv("CHECK_INTERVAL_MINUTES", "5")),
            "log_level": os.getenv("LOG_LEVEL", "INFO")
        },
        "templates": {
            "subject": os.getenv("EMAIL_SUBJECT_TEMPLATE", "TileWare Order #{order_id} - Action Required"),
            "body": os.getenv("EMAIL_BODY_TEMPLATE", """Hi CS - Please place this order:
{products}

SHIP TO:
{shipping_method}

{customer_name}
{shipping_address}

::::""")
        }
    }
    
    return config


@router.put("/")
async def update_email_config(
    config: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """Update email configuration."""
    env_path = settings.email_processor_config
    
    try:
        # Update IMAP settings
        if "imap" in config:
            if "server" in config["imap"]:
                set_key(env_path, "IMAP_SERVER", config["imap"]["server"])
            if "port" in config["imap"]:
                set_key(env_path, "IMAP_PORT", str(config["imap"]["port"]))
            if "email_address" in config["imap"]:
                set_key(env_path, "EMAIL_ADDRESS", config["imap"]["email_address"])
            if "password" in config["imap"] and config["imap"]["password"]:
                set_key(env_path, "EMAIL_PASSWORD", config["imap"]["password"])
        
        # Update SMTP settings
        if "smtp" in config:
            if "server" in config["smtp"]:
                set_key(env_path, "SMTP_SERVER", config["smtp"]["server"])
            if "port" in config["smtp"]:
                set_key(env_path, "SMTP_PORT", str(config["smtp"]["port"]))
            if "username" in config["smtp"]:
                set_key(env_path, "SMTP_USERNAME", config["smtp"]["username"])
            if "password" in config["smtp"] and config["smtp"]["password"]:
                set_key(env_path, "SMTP_PASSWORD", config["smtp"]["password"])
        
        # Update recipients
        if "recipients" in config:
            if "cs_email" in config["recipients"]:
                set_key(env_path, "CS_EMAIL", config["recipients"]["cs_email"])
            if "laticrete_cs_email" in config["recipients"]:
                set_key(env_path, "LATICRETE_CS_EMAIL", config["recipients"]["laticrete_cs_email"])
        
        # Update processing settings
        if "processing" in config:
            if "check_interval_minutes" in config["processing"]:
                set_key(env_path, "CHECK_INTERVAL_MINUTES", str(config["processing"]["check_interval_minutes"]))
            if "log_level" in config["processing"]:
                set_key(env_path, "LOG_LEVEL", config["processing"]["log_level"])
        
        # Update email templates
        if "templates" in config:
            if "subject" in config["templates"]:
                set_key(env_path, "EMAIL_SUBJECT_TEMPLATE", config["templates"]["subject"])
            if "body" in config["templates"]:
                set_key(env_path, "EMAIL_BODY_TEMPLATE", config["templates"]["body"])
        
        return {"message": "Configuration updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@router.post("/test-connection")
async def test_email_connection(
    connection_type: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Test email connection."""
    import sys
    sys.path.append(str(settings.project_root))
    
    try:
        if connection_type == "imap":
            from src.email_fetcher import EmailFetcher
            fetcher = EmailFetcher()
            fetcher.connect()
            fetcher.disconnect()
            return {"status": "success", "message": "IMAP connection successful"}
            
        elif connection_type == "smtp":
            from src.email_sender import EmailSender
            sender = EmailSender()
            # Test connection by creating instance (constructor tests connection)
            return {"status": "success", "message": "SMTP connection successful"}
            
        else:
            raise HTTPException(status_code=400, detail="Invalid connection type")
            
    except Exception as e:
        return {"status": "error", "message": str(e)}