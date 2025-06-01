"""Order management endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
from datetime import datetime, timedelta

try:
    from ..database import get_db
except ImportError:
    from database import get_db

try:
    from ..auth import get_current_active_user
except ImportError:
    from auth import get_current_active_user

try:
    from ..models.user import User
except ImportError:
    from models.user import User

try:
    from ..schemas.order import OrderResponse, OrderDetail, OrderStats, OrderUpdate
except ImportError:
    from schemas.order import OrderResponse, OrderDetail, OrderStats, OrderUpdate

try:
    from ..services.order_service import OrderService
except ImportError:
    from services.order_service import OrderService

router = APIRouter()


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of orders with filtering and pagination."""
    service = OrderService(db)
    return service.get_orders(
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/stats", response_model=OrderStats)
async def get_order_stats(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get order statistics."""
    service = OrderService(db)
    return service.get_statistics(days)


@router.get("/{order_id}", response_model=OrderDetail)
async def get_order_detail(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information about a specific order."""
    service = OrderService(db)
    order = service.get_order_detail(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order


@router.post("/{order_id}/resend")
async def resend_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Resend an order email."""
    service = OrderService(db)
    success = service.resend_order(order_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to resend order")
    
    return {"message": "Order resent successfully"}


@router.patch("/{order_id}", response_model=OrderDetail)
async def update_order(
    order_id: str,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an order with validation and audit logging."""
    service = OrderService(db)
    
    # Convert Pydantic model to dict, excluding None values
    updates = order_update.dict(exclude_none=True)
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    try:
        # Pass the current user's email for audit logging
        updated_order = service.update_order(order_id, updates, current_user.email)
        
        if not updated_order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return updated_order
        
    except ValueError as ve:
        # Handle validation errors (e.g., duplicate order_id)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Log the error and return a generic error message
        import logging
        logging.error(f"Error updating order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error updating order")


@router.delete("/{order_id}")
async def delete_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an order (superuser only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    service = OrderService(db)
    success = service.delete_order(order_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"message": "Order deleted successfully"}