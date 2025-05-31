#!/usr/bin/env python3
"""Add order_data column to store full order details for Laticrete orders."""

import sqlite3
import json
from pathlib import Path

def migrate_database(db_path: str):
    """Add order_data column to sent_orders table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(sent_orders)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'order_data' not in columns:
            print("Adding order_data column...")
            cursor.execute("ALTER TABLE sent_orders ADD COLUMN order_data TEXT")
            conn.commit()
            print("✓ order_data column added successfully")
        else:
            print("✓ order_data column already exists")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = Path(__file__).parent.parent / "order_tracking.db"
    migrate_database(str(db_path))