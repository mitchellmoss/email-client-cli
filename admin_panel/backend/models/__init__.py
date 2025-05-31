"""Database models."""

try:
    from .user import User
except ImportError:
    from user import User

try:
    from .product import ProductMapping
except ImportError:
    from product import ProductMapping

__all__ = ["User", "ProductMapping"]