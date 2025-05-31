"""Analytics endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import Dict, Any, List

from ..database import get_db
from ..auth import get_current_active_user
from ..models.user import User

router = APIRouter()


@router.get("/overview")
async def get_analytics_overview(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get analytics overview."""
    since_date = datetime.now() - timedelta(days=days)
    
    # Order volume by day
    volume_query = """
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as orders,
            COUNT(DISTINCT customer_name) as unique_customers
        FROM sent_orders
        WHERE created_at >= :since_date
        GROUP BY DATE(created_at)
        ORDER BY date
    """
    volume_result = db.execute(text(volume_query), {"since_date": since_date})
    volume_data = [dict(row._mapping) for row in volume_result]
    
    # Product distribution
    product_query = """
        SELECT 
            CASE 
                WHEN tileware_products LIKE '%tileware%' THEN 'TileWare'
                WHEN tileware_products LIKE '%laticrete%' THEN 'Laticrete'
                ELSE 'Other'
            END as product_type,
            COUNT(*) as count
        FROM sent_orders
        WHERE created_at >= :since_date
        GROUP BY product_type
    """
    product_result = db.execute(text(product_query), {"since_date": since_date})
    product_data = [dict(row._mapping) for row in product_result]
    
    # Processing performance
    performance_query = """
        SELECT 
            DATE(timestamp) as date,
            COUNT(CASE WHEN action = 'sent' THEN 1 END) as successful,
            COUNT(CASE WHEN action = 'error' THEN 1 END) as errors,
            COUNT(CASE WHEN action = 'duplicate_check' AND details = 'Order already sent' THEN 1 END) as duplicates_blocked
        FROM order_processing_log
        WHERE timestamp >= :since_date
        GROUP BY DATE(timestamp)
        ORDER BY date
    """
    performance_result = db.execute(text(performance_query), {"since_date": since_date})
    performance_data = [dict(row._mapping) for row in performance_result]
    
    # Top customers
    customer_query = """
        SELECT 
            customer_name,
            COUNT(*) as order_count,
            SUM(CAST(REPLACE(REPLACE(order_total, '$', ''), ',', '') AS FLOAT)) as total_value
        FROM sent_orders
        WHERE created_at >= :since_date
        AND customer_name IS NOT NULL
        GROUP BY customer_name
        ORDER BY order_count DESC
        LIMIT 10
    """
    customer_result = db.execute(text(customer_query), {"since_date": since_date})
    customer_data = [dict(row._mapping) for row in customer_result]
    
    return {
        "period_days": days,
        "volume_by_day": volume_data,
        "product_distribution": product_data,
        "processing_performance": performance_data,
        "top_customers": customer_data
    }


@router.get("/email-metrics")
async def get_email_metrics(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get email processing metrics."""
    since_date = datetime.now() - timedelta(days=days)
    
    # Email processing times (mock data for now)
    processing_times = {
        "average_processing_time": 2.5,  # seconds
        "min_processing_time": 1.2,
        "max_processing_time": 5.8
    }
    
    # Error rates
    error_query = """
        SELECT 
            COUNT(CASE WHEN action = 'error' THEN 1 END) as errors,
            COUNT(*) as total_actions
        FROM order_processing_log
        WHERE timestamp >= :since_date
    """
    error_result = db.execute(text(error_query), {"since_date": since_date}).fetchone()
    error_rate = (error_result.errors / error_result.total_actions * 100) if error_result.total_actions > 0 else 0
    
    # Duplicate prevention effectiveness
    duplicate_query = """
        SELECT 
            COUNT(*) as duplicates_blocked
        FROM order_processing_log
        WHERE action = 'duplicate_check' 
        AND details = 'Order already sent'
        AND timestamp >= :since_date
    """
    duplicate_result = db.execute(text(duplicate_query), {"since_date": since_date}).fetchone()
    
    return {
        "period_days": days,
        "processing_times": processing_times,
        "error_rate": round(error_rate, 2),
        "duplicates_blocked": duplicate_result.duplicates_blocked,
        "total_emails_processed": error_result.total_actions
    }


@router.get("/export")
async def export_analytics_data(
    report_type: str = Query(..., regex="^(orders|analytics|all)$"),
    format: str = Query("csv", regex="^(csv|json)$"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export analytics data."""
    # This would generate CSV/JSON exports
    # For now, return a placeholder
    return {
        "message": f"Export {report_type} data as {format} for last {days} days",
        "download_url": f"/api/v1/analytics/download/{report_type}.{format}"
    }