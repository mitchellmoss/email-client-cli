"""Product mapping models."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.sql import func

from database import Base


class ProductMapping(Base):
    """Product name to SKU mapping."""
    
    __tablename__ = "product_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    product_type = Column(String, nullable=False)  # 'tileware' or 'laticrete'
    original_name = Column(String, nullable=False, index=True)
    mapped_name = Column(String, nullable=False)
    sku = Column(String, nullable=False, index=True)
    price = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String)
    notes = Column(Text)