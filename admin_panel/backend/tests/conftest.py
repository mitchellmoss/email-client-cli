"""
Pytest configuration and fixtures for admin panel backend tests
"""
import os
import sys
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import Base, get_db
from auth import create_access_token, get_password_hash
from models.user import User
from models.product import ProductMapping


# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_db_engine():
    """Create a test database engine"""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create a test database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_db_session) -> Generator[TestClient, None, None]:
    """Create a test client with test database"""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db_session) -> User:
    """Create a test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_superuser=False
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def superuser(test_db_session) -> User:
    """Create a test superuser"""
    user = User(
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("adminpassword123"),
        is_active=True,
        is_superuser=True
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user) -> dict:
    """Create authentication headers for test user"""
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def superuser_auth_headers(superuser) -> dict:
    """Create authentication headers for superuser"""
    token = create_access_token(data={"sub": superuser.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_product_mapping(test_db_session) -> ProductMapping:
    """Create a sample product mapping"""
    mapping = ProductMapping(
        original_name="TileWare Original Product",
        mapped_name="TileWare Mapped Product",
        mapped_sku="TW-001",
        product_type="tileware",
        confidence_score=0.95
    )
    test_db_session.add(mapping)
    test_db_session.commit()
    test_db_session.refresh(mapping)
    return mapping


@pytest.fixture
def sample_order_data() -> dict:
    """Sample order data for testing"""
    return {
        "order_id": "12345",
        "customer_name": "John Doe",
        "email": "john@example.com",
        "phone": "555-1234",
        "order_date": "2024-01-15T10:30:00",
        "status": "pending",
        "total_amount": 299.99,
        "products": [
            {
                "name": "TileWare Premium Tile",
                "sku": "TW-001",
                "quantity": 2,
                "price": 149.99
            }
        ],
        "shipping_address": {
            "name": "John Doe",
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip": "12345",
            "country": "USA"
        },
        "shipping_method": "Standard",
        "tracking_number": None,
        "notes": "Please handle with care"
    }


@pytest.fixture
def mock_email_data() -> dict:
    """Mock email data for testing"""
    return {
        "subject": "New customer order #12345",
        "from": "noreply@tileprodepot.com",
        "date": "2024-01-15T10:30:00",
        "body": """
        You've received the following order from John Doe:
        
        Order #12345
        
        Product: TileWare Premium Tile
        SKU: TW-001
        Quantity: 2
        Price: $149.99
        
        Ship to:
        John Doe
        123 Main St
        Anytown, CA 12345
        
        Total: $299.99
        """
    }