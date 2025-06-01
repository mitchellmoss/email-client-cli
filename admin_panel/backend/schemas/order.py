"""Order schemas."""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class OrderProduct(BaseModel):
    """Order product schema."""
    name: str
    sku: Optional[str] = None
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
    order_data: Optional[Dict[str, Any]] = None
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
    order_data: Optional[Dict[str, Any]] = None
    original_html: Optional[str] = None
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


class OrderUpdate(BaseModel):
    """Order update schema."""
    order_id: Optional[str] = None
    email_subject: Optional[str] = None
    sent_to: Optional[str] = None
    customer_name: Optional[str] = None
    tileware_products: Optional[List[OrderProduct]] = None
    order_total: Optional[str] = None
    formatted_content: Optional[str] = None
    order_data: Optional[Dict[str, Any]] = None
    original_html: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json
        
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, dict):
            # Handle tileware_products if it's a JSON string
            if 'tileware_products' in value and isinstance(value['tileware_products'], str):
                try:
                    import json
                    value['tileware_products'] = json.loads(value['tileware_products'])
                except:
                    pass
            # Handle order_data if it's a JSON string
            if 'order_data' in value and isinstance(value['order_data'], str):
                try:
                    import json
                    value['order_data'] = json.loads(value['order_data'])
                except:
                    pass
        return value