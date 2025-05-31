"""Order schemas."""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class OrderProduct(BaseModel):
    """Order product schema."""
    name: str
    sku: str
    quantity: int
    price: Optional[str] = None


class OrderResponse(BaseModel):
    """Order list response schema."""
    id: int
    order_id: str
    email_subject: Optional[str] = None
    sent_at: datetime
    sent_to: str
    customer_name: Optional[str] = None
    tileware_products: Optional[List[OrderProduct]] = None
    order_total: Optional[str] = None
    created_at: datetime


class OrderHistory(BaseModel):
    """Order history entry schema."""
    id: int
    order_id: str
    action: str
    details: Optional[str] = None
    timestamp: datetime


class OrderDetail(OrderResponse):
    """Detailed order response schema."""
    formatted_content: Optional[str] = None
    email_uid: Optional[str] = None
    history: List[OrderHistory] = []


class DailyOrderCount(BaseModel):
    """Daily order count schema."""
    date: str
    count: int


class OrderStats(BaseModel):
    """Order statistics schema."""
    total_orders_sent: int
    daily_counts: List[DailyOrderCount]
    duplicate_attempts_blocked: int
    period_days: int