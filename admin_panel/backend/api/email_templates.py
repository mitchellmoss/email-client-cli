"""Email templates endpoints for vendor-specific templates."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
import os
from pathlib import Path
from dotenv import load_dotenv, set_key

try:
    from ..auth import get_current_active_user
except ImportError:
    from auth import get_current_active_user

try:
    from ..models.user import User
except ImportError:
    from models.user import User

try:
    from ..config import settings
except ImportError:
    from config import settings

router = APIRouter()


# Default templates for each vendor
DEFAULT_TEMPLATES = {
    "tileware": {
        "name": "TileWare",
        "subject": "TileWare Order #{order_id} - Action Required",
        "body": """Hi CS - Please place this order:
{products}

SHIP TO:
{shipping_method}

{customer_name}
{shipping_address}

::::""",
        "format": "text",
        "attachments": False,
        "variables": ["order_id", "products", "shipping_method", "customer_name", "shipping_address"]
    },
    "laticrete": {
        "name": "Laticrete",
        "subject": "Laticrete Order #{order_id} - {customer_name}",
        "body": """New Laticrete Order

Please process the attached Laticrete order form.

Order Summary:
- Order ID: {order_id}
- Customer: {customer_name}
- Date: {order_date}
- Total Items: {item_count}

Products:
{product_list}

Shipping Address:
{shipping_address}

Please verify all pricing before processing.""",
        "format": "html",
        "attachments": True,
        "attachment_type": "pdf",
        "variables": ["order_id", "customer_name", "order_date", "item_count", "product_list", "shipping_address"]
    }
}


@router.get("/")
async def get_email_templates(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get all vendor-specific email templates."""
    # Load from .env file
    env_path = settings.email_processor_config
    load_dotenv(env_path)
    
    templates = {}
    
    # Get TileWare template
    templates["tileware"] = {
        "name": "TileWare",
        "subject": os.getenv("TILEWARE_EMAIL_SUBJECT", DEFAULT_TEMPLATES["tileware"]["subject"]),
        "body": os.getenv("TILEWARE_EMAIL_BODY", DEFAULT_TEMPLATES["tileware"]["body"]),
        "format": "text/html",
        "attachments": False,
        "recipient": os.getenv("CS_EMAIL", ""),
        "variables": DEFAULT_TEMPLATES["tileware"]["variables"]
    }
    
    # Get Laticrete template
    templates["laticrete"] = {
        "name": "Laticrete",
        "subject": os.getenv("LATICRETE_EMAIL_SUBJECT", DEFAULT_TEMPLATES["laticrete"]["subject"]),
        "body": os.getenv("LATICRETE_EMAIL_BODY", DEFAULT_TEMPLATES["laticrete"]["body"]),
        "format": "html",
        "attachments": True,
        "attachment_type": "pdf",
        "recipient": os.getenv("LATICRETE_CS_EMAIL", ""),
        "variables": DEFAULT_TEMPLATES["laticrete"]["variables"]
    }
    
    # Add signature that's used for all vendors
    templates["signature"] = {
        "text": os.getenv("EMAIL_SIGNATURE_TEXT", """--
Mitchell Moss
Installations Plus Inc.
774-233-0210 | 508-733-5839
mitchell@installplusinc.com
installplusinc.com
131 Flanders Rd, Westborough, MA, 01581

Connect with us:
LinkedIn: https://www.linkedin.com/company/10612759
Facebook: http://www.facebook.com/installplusinc
Instagram: https://www.instagram.com/installations_plus/"""),
        "html": os.getenv("EMAIL_SIGNATURE_HTML", "")  # HTML signature is complex, empty by default
    }
    
    return {
        "vendors": templates,
        "available_variables": {
            "tileware": DEFAULT_TEMPLATES["tileware"]["variables"],
            "laticrete": DEFAULT_TEMPLATES["laticrete"]["variables"]
        }
    }


@router.put("/")
async def update_email_templates(
    templates: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """Update vendor-specific email templates."""
    env_path = settings.email_processor_config
    
    try:
        vendors = templates.get("vendors", {})
        
        # Update TileWare templates
        if "tileware" in vendors:
            tileware = vendors["tileware"]
            if "subject" in tileware:
                set_key(env_path, "TILEWARE_EMAIL_SUBJECT", tileware["subject"])
            if "body" in tileware:
                set_key(env_path, "TILEWARE_EMAIL_BODY", tileware["body"])
            if "recipient" in tileware:
                set_key(env_path, "CS_EMAIL", tileware["recipient"])
        
        # Update Laticrete templates
        if "laticrete" in vendors:
            laticrete = vendors["laticrete"]
            if "subject" in laticrete:
                set_key(env_path, "LATICRETE_EMAIL_SUBJECT", laticrete["subject"])
            if "body" in laticrete:
                set_key(env_path, "LATICRETE_EMAIL_BODY", laticrete["body"])
            if "recipient" in laticrete:
                set_key(env_path, "LATICRETE_CS_EMAIL", laticrete["recipient"])
        
        # Update signature
        if "signature" in vendors:
            signature = vendors["signature"]
            if "text" in signature:
                set_key(env_path, "EMAIL_SIGNATURE_TEXT", signature["text"])
            if "html" in signature:
                set_key(env_path, "EMAIL_SIGNATURE_HTML", signature["html"])
        
        return {"message": "Email templates updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update templates: {str(e)}")


@router.get("/preview")
async def preview_email_template(
    vendor: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Preview email template with sample data."""
    if vendor not in ["tileware", "laticrete"]:
        raise HTTPException(status_code=400, detail="Invalid vendor")
    
    # Sample data for preview
    sample_data = {
        "order_id": "43210",
        "customer_name": "John Doe",
        "order_date": "May 31, 2025",
        "item_count": "3",
        "products": """TileWare Promessa™ Series Towel Bar (#T101-024-PC) x1
TileWare Promessa™ Series Toilet Paper Holder (#T101-050-PC) x2""",
        "product_list": """- LAT123 | LATICRETE 254 Platinum | Qty: 5 | $25.99/ea
- LAT456 | LATICRETE HYDRO BAN | Qty: 2 | $89.99/ea""",
        "shipping_method": "UPS GROUND",
        "shipping_address": """123 Main Street
Anytown, CA 12345"""
    }
    
    templates = await get_email_templates(current_user)
    template = templates["vendors"][vendor]
    
    # Replace variables in subject and body
    subject = template["subject"]
    body = template["body"]
    
    for var, value in sample_data.items():
        subject = subject.replace(f"{{{var}}}", value)
        body = body.replace(f"{{{var}}}", value)
    
    return {
        "vendor": vendor,
        "subject": subject,
        "body": body,
        "format": template["format"],
        "attachments": template.get("attachments", False)
    }


@router.post("/reset/{vendor}")
async def reset_vendor_template(
    vendor: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """Reset a vendor template to default."""
    if vendor not in DEFAULT_TEMPLATES:
        raise HTTPException(status_code=400, detail="Invalid vendor")
    
    env_path = settings.email_processor_config
    
    try:
        if vendor == "tileware":
            set_key(env_path, "TILEWARE_EMAIL_SUBJECT", DEFAULT_TEMPLATES["tileware"]["subject"])
            set_key(env_path, "TILEWARE_EMAIL_BODY", DEFAULT_TEMPLATES["tileware"]["body"])
        elif vendor == "laticrete":
            set_key(env_path, "LATICRETE_EMAIL_SUBJECT", DEFAULT_TEMPLATES["laticrete"]["subject"])
            set_key(env_path, "LATICRETE_EMAIL_BODY", DEFAULT_TEMPLATES["laticrete"]["body"])
        
        return {"message": f"{vendor.title()} template reset to default"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset template: {str(e)}")