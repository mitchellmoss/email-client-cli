#!/usr/bin/env python3
"""Add columns for failed order tracking."""

import sqlite3
from pathlib import Path

def migrate_database(db_path: str):
    """Add failed order tracking columns to sent_orders table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(sent_orders)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Existing columns: {columns}")
        
        # Add missing columns
        columns_to_add = [
            ("status", "TEXT DEFAULT 'sent'"),
            ("error_message", "TEXT"),
            ("raw_email_content", "TEXT"),
            ("product_type", "TEXT"),
            ("laticrete_products", "TEXT"),
            ("order_data", "TEXT")
        ]
        
        for column_name, column_def in columns_to_add:
            if column_name not in columns:
                print(f"Adding column: {column_name}")
                cursor.execute(f"ALTER TABLE sent_orders ADD COLUMN {column_name} {column_def}")
                conn.commit()
                print(f"✓ {column_name} column added successfully")
            else:
                print(f"✓ {column_name} column already exists")
        
        # Create index on status column
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON sent_orders(status)")
        conn.commit()
        print("✓ Status index created successfully")
        
        # Update existing records to have 'sent' status
        cursor.execute("UPDATE sent_orders SET status = 'sent' WHERE status IS NULL")
        rows_updated = cursor.rowcount
        conn.commit()
        print(f"✓ Updated {rows_updated} existing records with 'sent' status")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = Path(__file__).parent.parent / "order_tracking.db"
    print(f"Migrating database: {db_path}")
    migrate_database(str(db_path))
    print("Migration completed!")