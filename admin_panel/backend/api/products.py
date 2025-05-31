"""Product mapping endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

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
    from ..models.product import ProductMapping
except ImportError:
    from models.product import ProductMapping

try:
    from ..schemas.product import (
        ProductMappingCreate,
        ProductMappingUpdate,
        ProductMappingResponse
    )
except ImportError:
    from schemas.product import (
        ProductMappingCreate,
        ProductMappingUpdate,
        ProductMappingResponse
    )

router = APIRouter()


@router.get("/mappings", response_model=List[ProductMappingResponse])
async def get_product_mappings(
    product_type: Optional[str] = Query(None, regex="^(tileware|laticrete)$"),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get product mappings with filtering."""
    query = db.query(ProductMapping)
    
    if product_type:
        query = query.filter(ProductMapping.product_type == product_type)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (ProductMapping.original_name.ilike(search_term)) |
            (ProductMapping.mapped_name.ilike(search_term)) |
            (ProductMapping.sku.ilike(search_term))
        )
    
    if is_active is not None:
        query = query.filter(ProductMapping.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()


@router.post("/mappings", response_model=ProductMappingResponse)
async def create_product_mapping(
    mapping: ProductMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new product mapping."""
    # Check if mapping already exists
    existing = db.query(ProductMapping).filter(
        ProductMapping.product_type == mapping.product_type,
        ProductMapping.original_name == mapping.original_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Mapping for this product already exists"
        )
    
    db_mapping = ProductMapping(
        **mapping.dict(),
        created_by=current_user.email
    )
    
    db.add(db_mapping)
    db.commit()
    db.refresh(db_mapping)
    
    return db_mapping


@router.put("/mappings/{mapping_id}", response_model=ProductMappingResponse)
async def update_product_mapping(
    mapping_id: int,
    mapping: ProductMappingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a product mapping."""
    db_mapping = db.query(ProductMapping).filter(
        ProductMapping.id == mapping_id
    ).first()
    
    if not db_mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    for field, value in mapping.dict(exclude_unset=True).items():
        setattr(db_mapping, field, value)
    
    db.commit()
    db.refresh(db_mapping)
    
    return db_mapping


@router.delete("/mappings/{mapping_id}")
async def delete_product_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a product mapping."""
    db_mapping = db.query(ProductMapping).filter(
        ProductMapping.id == mapping_id
    ).first()
    
    if not db_mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    db.delete(db_mapping)
    db.commit()
    
    return {"message": "Mapping deleted successfully"}