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
try:
    from ..config import settings
except ImportError:
    from config import settings


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