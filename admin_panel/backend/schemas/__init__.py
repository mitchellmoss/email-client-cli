"""Pydantic schemas for API."""

try:
    from .user import UserCreate, UserResponse, Token, TokenData
except ImportError:
    from user import UserCreate, UserResponse, Token, TokenData

try:
    from .order import OrderResponse, OrderDetail, OrderStats
except ImportError:
    from order import OrderResponse, OrderDetail, OrderStats

try:
    from .product import ProductMappingCreate, ProductMappingUpdate, ProductMappingResponse
except ImportError:
    from product import ProductMappingCreate, ProductMappingUpdate, ProductMappingResponse

__all__ = [
    "UserCreate", "UserResponse", "Token", "TokenData",
    "OrderResponse", "OrderDetail", "OrderStats",
    "ProductMappingCreate", "ProductMappingUpdate", "ProductMappingResponse"
]