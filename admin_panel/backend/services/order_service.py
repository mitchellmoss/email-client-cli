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
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

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
        logger.info(f"Resend requested for order: {order_id}")
        
        # Try to find the order with the original ID first (since DB stores with prefixes)
        order = self.order_tracker.get_order_details(order_id)
        
        if not order:
            # If not found and has a prefix, try without it
            if '-' in order_id:
                parts = order_id.split('-')
                if len(parts) == 2 and parts[1].isdigit():
                    clean_order_id = parts[1]
                    order = self.order_tracker.get_order_details(clean_order_id)
            
            if not order:
                logger.error(f"Order not found: {order_id}")
                return False
        
        logger.info(f"Order found: {order.get('order_id')}, has order_data: {bool(order.get('order_data'))}")
        
        try:
            # Check if this is a Laticrete order
            if order_id.startswith('LAT-') and order.get('order_data'):
                # Handle Laticrete orders with PDF regeneration
                logger.info(f"Processing as Laticrete order")
                return self._resend_laticrete_order(order)
            else:
                # Handle regular TileWare orders
                logger.info(f"Processing as TileWare order")
                return self._resend_tileware_order(order, order_id)
            
        except Exception as e:
            logger.error(f"Exception in resend_order: {e}", exc_info=True)
            self.order_tracker._log_action(
                order.get('order_id', order_id),
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
    
    def update_order(self, order_id: str, updates: Dict[str, Any], user_email: str) -> Optional[Dict[str, Any]]:
        """Update an order with validation and audit logging."""
        try:
            # First check if the order exists
            existing_order = self.get_order_detail(order_id)
            if not existing_order:
                logger.error(f"Order not found for update: {order_id}")
                return None
            
            # Prepare the update data
            update_fields = []
            params = {"original_order_id": order_id}
            
            # Track changes for audit log
            changes = {}
            
            # Handle order_id update with duplicate check
            if "order_id" in updates and updates["order_id"] != order_id:
                new_order_id = updates["order_id"]
                # Check for duplicates
                duplicate_check = self.db.execute(
                    text("SELECT COUNT(*) FROM sent_orders WHERE order_id = :new_id AND order_id != :old_id"),
                    {"new_id": new_order_id, "old_id": order_id}
                ).scalar()
                
                if duplicate_check > 0:
                    raise ValueError(f"Order ID {new_order_id} already exists")
                
                update_fields.append("order_id = :new_order_id")
                params["new_order_id"] = new_order_id
                changes["order_id"] = {"old": order_id, "new": new_order_id}
            
            # Handle other field updates
            field_mapping = {
                "email_subject": "email_subject",
                "sent_to": "sent_to",
                "customer_name": "customer_name",
                "order_total": "order_total",
                "formatted_content": "formatted_content",
                "original_html": "original_html"
            }
            
            for field_key, db_field in field_mapping.items():
                if field_key in updates:
                    update_fields.append(f"{db_field} = :{field_key}")
                    params[field_key] = updates[field_key]
                    old_value = existing_order.get(field_key)
                    changes[field_key] = {"old": old_value, "new": updates[field_key]}
            
            # Handle JSON fields
            if "tileware_products" in updates:
                # Convert to JSON string
                products_json = json.dumps(updates["tileware_products"]) if updates["tileware_products"] else None
                update_fields.append("tileware_products = :tileware_products")
                params["tileware_products"] = products_json
                old_products = existing_order.get("tileware_products")
                changes["tileware_products"] = {
                    "old": old_products,
                    "new": updates["tileware_products"]
                }
            
            if "order_data" in updates:
                # Convert to JSON string
                order_data_json = json.dumps(updates["order_data"]) if updates["order_data"] else None
                update_fields.append("order_data = :order_data")
                params["order_data"] = order_data_json
                # Handle order_data that might already be parsed
                old_order_data = existing_order.get("order_data")
                if isinstance(old_order_data, str):
                    try:
                        old_order_data = json.loads(old_order_data)
                    except:
                        old_order_data = None
                changes["order_data"] = {
                    "old": old_order_data,
                    "new": updates["order_data"]
                }
            
            if not update_fields:
                logger.warning(f"No valid fields to update for order {order_id}")
                return existing_order
            
            # Build and execute update query
            update_query = f"""
                UPDATE sent_orders 
                SET {', '.join(update_fields)}
                WHERE order_id = :original_order_id
            """
            
            self.db.execute(text(update_query), params)
            
            # Log the update action with detailed changes
            audit_details = {
                "user": user_email,
                "action": "order_updated",
                "changes": changes,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.order_tracker._log_action(
                order_id,
                "updated",
                json.dumps(audit_details)
            )
            
            # If order_id was changed, update the log entries
            if "order_id" in updates and updates["order_id"] != order_id:
                self.db.execute(
                    text("UPDATE order_processing_log SET order_id = :new_id WHERE order_id = :old_id"),
                    {"new_id": updates["order_id"], "old_id": order_id}
                )
            
            self.db.commit()
            
            # Return the updated order
            final_order_id = updates.get("order_id", order_id)
            return self.get_order_detail(final_order_id)
            
        except ValueError as ve:
            self.db.rollback()
            logger.error(f"Validation error updating order {order_id}: {ve}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating order {order_id}: {e}", exc_info=True)
            return None
    
    def _resend_tileware_order(self, order: Dict[str, Any], order_id: str) -> bool:
        """Resend a TileWare order."""
        # Get email signature from settings
        email_signature = os.getenv('EMAIL_SIGNATURE_TEXT', '')
        
        # Initialize email sender with environment variables and signature
        sender = EmailSender(
            smtp_server=os.getenv('SMTP_SERVER'),
            smtp_port=int(os.getenv('SMTP_PORT', 587)),
            username=os.getenv('SMTP_USERNAME'),
            password=os.getenv('SMTP_PASSWORD'),
            signature_html=email_signature if email_signature else None
        )
        
        # Send the formatted content
        success = sender.send_order_to_cs(
            recipient=order['sent_to'],
            order_text=order['formatted_content'],
            original_order_id=order_id
        )
        
        if success:
            # Log the resend action using the actual order ID from the database
            self.order_tracker._log_action(
                order.get('order_id', order_id),
                "resent",
                f"Order resent to {order['sent_to']}"
            )
        
        return success
    
    def _resend_laticrete_order(self, order: Dict[str, Any]) -> bool:
        """Resend a Laticrete order with PDF regeneration."""
        # Import here to avoid circular imports and module issues
        import sys
        import os
        from pathlib import Path
        
        # Ensure the src module is in the path
        project_root = Path(__file__).parent.parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from src.laticrete_processor import LatricreteProcessor
        
        try:
            # Get the stored order data
            order_data = order.get('order_data')
            if not order_data:
                logger.error(f"No order_data found for Laticrete order {order.get('order_id')}")
                # Fallback: try to reconstruct from available data
                order_data = {
                    'order_id': order['order_id'].replace('LAT-', ''),
                    'customer_name': order['customer_name'],
                    'laticrete_products': [],
                    'shipping_address': {}
                }
            
            logger.info(f"Resending Laticrete order {order.get('order_id')} with {len(order_data.get('laticrete_products', []))} products")
            
            # Initialize Laticrete processor
            processor = LatricreteProcessor()
            
            # Process the order (enriches prices, fills PDF, sends email)
            success = processor.process_order(order_data)
            
            if success:
                # Log the resend action
                self.order_tracker._log_action(
                    order['order_id'],
                    "resent",
                    f"Laticrete order with PDF resent to {order['sent_to']}"
                )
                logger.info(f"Successfully resent Laticrete order {order.get('order_id')}")
            else:
                logger.error(f"Failed to resend Laticrete order {order.get('order_id')}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error resending Laticrete order {order.get('order_id')}: {e}", exc_info=True)
            # Also log to a file for debugging
            import traceback
            with open('/tmp/laticrete_resend_error.log', 'w') as f:
                f.write(f"Error resending Laticrete order {order.get('order_id')}: {e}\n")
                f.write(traceback.format_exc())
            return False