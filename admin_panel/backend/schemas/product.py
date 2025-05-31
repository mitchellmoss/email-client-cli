"""Product mapping schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProductMappingBase(BaseModel):
    """Base product mapping schema."""
    product_type: str  # 'tileware' or 'laticrete'
    original_name: str
    mapped_name: str
    sku: str
    price: Optional[float] = None
    is_active: bool = True
    notes: Optional[str] = None


class ProductMappingCreate(ProductMappingBase):
    """Schema for creating a product mapping."""
    pass


class ProductMappingUpdate(BaseModel):
    """Schema for updating a product mapping."""
    mapped_name: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ProductMappingResponse(ProductMappingBase):
    """Schema for product mapping responses."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True