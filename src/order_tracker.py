"""Order tracking module for preventing duplicate sends."""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any, Tuple
from contextlib import contextmanager
import threading
import logging

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class OrderTracker:
    """Track processed orders to prevent duplicate sends."""
    
    def __init__(self, db_path: str = "order_tracking.db"):
        """Initialize the order tracker with database."""
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()
        
    def _init_database(self):
        """Initialize database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            
            # Create sent_orders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sent_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE NOT NULL,
                    email_subject TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_to TEXT NOT NULL,
                    customer_name TEXT,
                    tileware_products TEXT,
                    order_total TEXT,
                    formatted_content TEXT,
                    email_uid TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_id ON sent_orders(order_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON sent_orders(created_at)")
            
            # Create processing log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_processing_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT,
                    action TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_order_id ON order_processing_log(order_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_timestamp ON order_processing_log(timestamp)")
            
            conn.commit()
            logger.info(f"Order tracking database initialized at {self.db_path}")
            
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
            
    def has_order_been_sent(self, order_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if an order has already been sent.
        
        Args:
            order_id: The order ID to check
            
        Returns:
            Tuple of (is_sent, order_details)
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT * FROM sent_orders 
                        WHERE order_id = ?
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, (order_id,))
                    
                    row = cursor.fetchone()
                    if row:
                        # Convert row to dict
                        order_details = dict(row)
                        self._log_action(order_id, "duplicate_check", "Order already sent")
                        return True, order_details
                    else:
                        self._log_action(order_id, "duplicate_check", "Order not found")
                        return False, None
                        
            except Exception as e:
                logger.error(f"Error checking order {order_id}: {e}")
                return False, None
                
    def mark_order_as_sent(self, order_id: str, email_data: Dict[str, Any], 
                          order_details: Dict[str, Any], formatted_content: str,
                          recipient: str) -> bool:
        """
        Mark an order as successfully sent.
        
        Args:
            order_id: The order ID
            email_data: Email metadata
            order_details: Extracted order details
            formatted_content: The formatted order text sent
            recipient: Email recipient
            
        Returns:
            True if successfully recorded, False otherwise
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Prepare tileware products as JSON
                    products_json = json.dumps(order_details.get('tileware_products', []))
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO sent_orders (
                            order_id, email_subject, sent_to, customer_name,
                            tileware_products, order_total, formatted_content,
                            email_uid
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        order_id,
                        email_data.get('subject', ''),
                        recipient,
                        order_details.get('customer_name', ''),
                        products_json,
                        order_details.get('total', ''),
                        formatted_content,
                        email_data.get('uid', '')
                    ))
                    
                    conn.commit()
                    
                    self._log_action(order_id, "sent", f"Order sent to {recipient}")
                    logger.info(f"Order {order_id} marked as sent")
                    return True
                    
            except Exception as e:
                logger.error(f"Error marking order {order_id} as sent: {e}")
                self._log_action(order_id, "error", f"Failed to mark as sent: {e}")
                return False
                
    def _log_action(self, order_id: str, action: str, details: str):
        """Log an action to the processing log."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO order_processing_log (order_id, action, details)
                    VALUES (?, ?, ?)
                """, (order_id, action, details))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging action: {e}")
            
    def get_sent_orders(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get list of sent orders.
        
        Args:
            limit: Maximum number of orders to return
            offset: Number of orders to skip
            
        Returns:
            List of order dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM sent_orders 
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error retrieving sent orders: {e}")
            return []
            
    def get_order_details(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific order."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM sent_orders 
                    WHERE order_id = ?
                """, (order_id,))
                
                row = cursor.fetchone()
                if row:
                    details = dict(row)
                    # Parse JSON products
                    if details.get('tileware_products'):
                        details['tileware_products'] = json.loads(details['tileware_products'])
                    return details
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving order {order_id}: {e}")
            return None
            
    def get_order_history(self, order_id: str) -> List[Dict[str, Any]]:
        """Get processing history for an order."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM order_processing_log 
                    WHERE order_id = ?
                    ORDER BY timestamp DESC
                """, (order_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error retrieving order history: {e}")
            return []
            
    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get order processing statistics.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                since_date = datetime.now() - timedelta(days=days)
                
                # Total orders sent
                cursor.execute("""
                    SELECT COUNT(DISTINCT order_id) as total
                    FROM sent_orders
                    WHERE created_at >= ?
                """, (since_date,))
                total = cursor.fetchone()['total']
                
                # Orders by day
                cursor.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM sent_orders
                    WHERE created_at >= ?
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """, (since_date,))
                daily_counts = [dict(row) for row in cursor.fetchall()]
                
                # Duplicate attempts blocked
                cursor.execute("""
                    SELECT COUNT(*) as duplicates
                    FROM order_processing_log
                    WHERE action = 'duplicate_check' 
                    AND details = 'Order already sent'
                    AND timestamp >= ?
                """, (since_date,))
                duplicates = cursor.fetchone()['duplicates']
                
                return {
                    'total_orders_sent': total,
                    'daily_counts': daily_counts,
                    'duplicate_attempts_blocked': duplicates,
                    'period_days': days
                }
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
            
    def cleanup_old_records(self, days: int = 90) -> int:
        """
        Remove old records from the database.
        
        Args:
            days: Remove records older than this many days
            
        Returns:
            Number of records removed
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cutoff_date = datetime.now() - timedelta(days=days)
                    
                    # Delete old orders
                    cursor.execute("""
                        DELETE FROM sent_orders 
                        WHERE created_at < ?
                    """, (cutoff_date,))
                    orders_deleted = cursor.rowcount
                    
                    # Delete old log entries
                    cursor.execute("""
                        DELETE FROM order_processing_log 
                        WHERE timestamp < ?
                    """, (cutoff_date,))
                    logs_deleted = cursor.rowcount
                    
                    conn.commit()
                    
                    # Vacuum to reclaim space
                    cursor.execute("VACUUM")
                    
                    total_deleted = orders_deleted + logs_deleted
                    logger.info(f"Cleaned up {total_deleted} old records")
                    return total_deleted
                    
            except Exception as e:
                logger.error(f"Error cleaning up old records: {e}")
                return 0