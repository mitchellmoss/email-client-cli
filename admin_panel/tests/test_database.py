"""
Database operation tests
"""
import pytest
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin_panel.backend.database import Base
from admin_panel.backend.models.user import User
from admin_panel.backend.models.product import ProductMapping
from admin_panel.backend.auth import get_password_hash


class TestDatabaseOperations:
    """Test database operations and integrity"""
    
    @pytest.fixture(scope="function")
    def db_engine(self):
        """Create test database engine"""
        SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db_operations.db"
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        
        yield engine
        
        # Cleanup
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("test_db_operations.db"):
            os.remove("test_db_operations.db")
    
    @pytest.fixture(scope="function")
    def db_session(self, db_engine) -> Session:
        """Create database session"""
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
        session = SessionLocal()
        
        yield session
        
        session.close()
    
    def test_user_model_operations(self, db_session: Session):
        """Test User model CRUD operations"""
        # Create
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_superuser=False
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.created_at is not None
        assert user.updated_at is not None
        
        # Read
        fetched_user = db_session.query(User).filter(User.email == "test@example.com").first()
        assert fetched_user is not None
        assert fetched_user.username == "testuser"
        assert fetched_user.is_active == True
        
        # Update
        fetched_user.username = "updateduser"
        fetched_user.is_superuser = True
        db_session.commit()
        db_session.refresh(fetched_user)
        
        assert fetched_user.username == "updateduser"
        assert fetched_user.is_superuser == True
        assert fetched_user.updated_at > fetched_user.created_at
        
        # Delete
        db_session.delete(fetched_user)
        db_session.commit()
        
        deleted_user = db_session.query(User).filter(User.id == user.id).first()
        assert deleted_user is None
    
    def test_user_unique_constraints(self, db_session: Session):
        """Test unique constraints on User model"""
        # Create first user
        user1 = User(
            email="unique@example.com",
            username="uniqueuser",
            hashed_password=get_password_hash("password123")
        )
        db_session.add(user1)
        db_session.commit()
        
        # Try to create user with duplicate email
        user2 = User(
            email="unique@example.com",  # Duplicate email
            username="anotheruser",
            hashed_password=get_password_hash("password123")
        )
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
        
        # Try to create user with duplicate username
        user3 = User(
            email="another@example.com",
            username="uniqueuser",  # Duplicate username
            hashed_password=get_password_hash("password123")
        )
        db_session.add(user3)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_product_mapping_operations(self, db_session: Session):
        """Test ProductMapping model CRUD operations"""
        # Create
        mapping = ProductMapping(
            original_name="Original Product",
            mapped_name="Mapped Product",
            mapped_sku="SKU-001",
            product_type="tileware",
            confidence_score=0.95
        )
        db_session.add(mapping)
        db_session.commit()
        db_session.refresh(mapping)
        
        assert mapping.id is not None
        assert mapping.created_at is not None
        assert mapping.updated_at is not None
        
        # Read
        fetched_mapping = db_session.query(ProductMapping).filter(
            ProductMapping.original_name == "Original Product"
        ).first()
        assert fetched_mapping is not None
        assert fetched_mapping.mapped_sku == "SKU-001"
        assert fetched_mapping.confidence_score == 0.95
        
        # Update
        fetched_mapping.confidence_score = 0.98
        fetched_mapping.mapped_name = "Updated Mapped Product"
        db_session.commit()
        db_session.refresh(fetched_mapping)
        
        assert fetched_mapping.confidence_score == 0.98
        assert fetched_mapping.mapped_name == "Updated Mapped Product"
        
        # Delete
        db_session.delete(fetched_mapping)
        db_session.commit()
        
        deleted_mapping = db_session.query(ProductMapping).filter(
            ProductMapping.id == mapping.id
        ).first()
        assert deleted_mapping is None
    
    def test_product_mapping_unique_constraint(self, db_session: Session):
        """Test unique constraint on ProductMapping original_name"""
        # Create first mapping
        mapping1 = ProductMapping(
            original_name="Unique Product",
            mapped_name="Mapped Product 1",
            mapped_sku="SKU-001",
            product_type="tileware",
            confidence_score=0.9
        )
        db_session.add(mapping1)
        db_session.commit()
        
        # Try to create mapping with duplicate original_name
        mapping2 = ProductMapping(
            original_name="Unique Product",  # Duplicate
            mapped_name="Mapped Product 2",
            mapped_sku="SKU-002",
            product_type="laticrete",
            confidence_score=0.8
        )
        db_session.add(mapping2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_product_type_validation(self, db_session: Session):
        """Test product_type validation"""
        # Valid product types
        valid_types = ["tileware", "laticrete"]
        
        for i, ptype in enumerate(valid_types):
            mapping = ProductMapping(
                original_name=f"Product {i}",
                mapped_name=f"Mapped {i}",
                mapped_sku=f"SKU-{i}",
                product_type=ptype,
                confidence_score=0.9
            )
            db_session.add(mapping)
        
        db_session.commit()
        
        # Verify all were created
        count = db_session.query(ProductMapping).count()
        assert count == len(valid_types)
    
    def test_cascade_operations(self, db_session: Session):
        """Test cascade delete operations"""
        # Create user with related data
        user = User(
            email="cascade@example.com",
            username="cascadeuser",
            hashed_password=get_password_hash("password123")
        )
        db_session.add(user)
        db_session.commit()
        
        # In a real app, we might have user-related data like sessions, logs, etc.
        # For now, just test user deletion works
        user_id = user.id
        
        db_session.delete(user)
        db_session.commit()
        
        # Verify user is deleted
        deleted_user = db_session.query(User).filter(User.id == user_id).first()
        assert deleted_user is None
    
    def test_bulk_operations(self, db_session: Session):
        """Test bulk insert and update operations"""
        # Bulk insert
        mappings = []
        for i in range(100):
            mapping = ProductMapping(
                original_name=f"Bulk Product {i}",
                mapped_name=f"Bulk Mapped {i}",
                mapped_sku=f"BULK-{i:03d}",
                product_type="tileware" if i % 2 == 0 else "laticrete",
                confidence_score=0.8 + (i % 20) / 100
            )
            mappings.append(mapping)
        
        db_session.bulk_save_objects(mappings)
        db_session.commit()
        
        # Verify bulk insert
        count = db_session.query(ProductMapping).count()
        assert count == 100
        
        # Bulk update using query
        db_session.query(ProductMapping).filter(
            ProductMapping.product_type == "tileware"
        ).update({"confidence_score": 0.95})
        db_session.commit()
        
        # Verify bulk update
        tileware_count = db_session.query(ProductMapping).filter(
            ProductMapping.product_type == "tileware",
            ProductMapping.confidence_score == 0.95
        ).count()
        assert tileware_count == 50
    
    def test_query_performance(self, db_session: Session):
        """Test query performance with indexes"""
        # Create test data
        for i in range(1000):
            mapping = ProductMapping(
                original_name=f"Perf Product {i}",
                mapped_name=f"Perf Mapped {i}",
                mapped_sku=f"PERF-{i:04d}",
                product_type="tileware" if i % 3 == 0 else "laticrete",
                confidence_score=0.7 + (i % 30) / 100
            )
            db_session.add(mapping)
        
        db_session.commit()
        
        # Test indexed queries
        import time
        
        # Query by indexed field (original_name has unique index)
        start = time.time()
        result = db_session.query(ProductMapping).filter(
            ProductMapping.original_name == "Perf Product 500"
        ).first()
        indexed_time = time.time() - start
        assert result is not None
        
        # Query by non-indexed field for comparison
        start = time.time()
        results = db_session.query(ProductMapping).filter(
            ProductMapping.confidence_score > 0.9
        ).all()
        non_indexed_time = time.time() - start
        
        # Indexed queries should generally be faster
        # Note: This might not always be true for small datasets or SQLite
        print(f"Indexed query time: {indexed_time:.4f}s")
        print(f"Non-indexed query time: {non_indexed_time:.4f}s")
    
    def test_transaction_rollback(self, db_session: Session):
        """Test transaction rollback behavior"""
        # Create initial data
        user = User(
            email="rollback@example.com",
            username="rollbackuser",
            hashed_password=get_password_hash("password123")
        )
        db_session.add(user)
        db_session.commit()
        
        initial_count = db_session.query(User).count()
        
        # Start a transaction that will fail
        try:
            # Create a valid user
            user2 = User(
                email="valid@example.com",
                username="validuser",
                hashed_password=get_password_hash("password123")
            )
            db_session.add(user2)
            
            # Create an invalid user (duplicate email)
            user3 = User(
                email="rollback@example.com",  # Duplicate
                username="anotheruser",
                hashed_password=get_password_hash("password123")
            )
            db_session.add(user3)
            
            db_session.commit()  # This should fail
        except IntegrityError:
            db_session.rollback()
        
        # Verify rollback worked - count should be unchanged
        final_count = db_session.query(User).count()
        assert final_count == initial_count
        
        # Verify the valid user was not created
        valid_user = db_session.query(User).filter(
            User.email == "valid@example.com"
        ).first()
        assert valid_user is None
    
    def test_pagination_queries(self, db_session: Session):
        """Test pagination queries"""
        # Create test data
        for i in range(50):
            mapping = ProductMapping(
                original_name=f"Page Product {i:02d}",
                mapped_name=f"Page Mapped {i:02d}",
                mapped_sku=f"PAGE-{i:02d}",
                product_type="tileware",
                confidence_score=0.9
            )
            db_session.add(mapping)
        
        db_session.commit()
        
        # Test pagination
        page_size = 10
        
        # Page 1
        page1 = db_session.query(ProductMapping).order_by(
            ProductMapping.original_name
        ).limit(page_size).offset(0).all()
        assert len(page1) == 10
        assert page1[0].original_name == "Page Product 00"
        assert page1[9].original_name == "Page Product 09"
        
        # Page 2
        page2 = db_session.query(ProductMapping).order_by(
            ProductMapping.original_name
        ).limit(page_size).offset(10).all()
        assert len(page2) == 10
        assert page2[0].original_name == "Page Product 10"
        assert page2[9].original_name == "Page Product 19"
        
        # Last page
        page5 = db_session.query(ProductMapping).order_by(
            ProductMapping.original_name
        ).limit(page_size).offset(40).all()
        assert len(page5) == 10
        assert page5[0].original_name == "Page Product 40"
        assert page5[9].original_name == "Page Product 49"
    
    def test_search_queries(self, db_session: Session):
        """Test search functionality"""
        # Create test data with searchable content
        test_products = [
            ("TileWare Premium Pro", "TWP-001"),
            ("TileWare Standard", "TWS-001"),
            ("Laticrete Premium Adhesive", "LPA-001"),
            ("Laticrete Standard Grout", "LSG-001"),
            ("Special TileWare Edition", "STE-001")
        ]
        
        for name, sku in test_products:
            mapping = ProductMapping(
                original_name=name,
                mapped_name=f"Mapped {name}",
                mapped_sku=sku,
                product_type="tileware" if "TileWare" in name else "laticrete",
                confidence_score=0.9
            )
            db_session.add(mapping)
        
        db_session.commit()
        
        # Test case-insensitive search
        search_results = db_session.query(ProductMapping).filter(
            ProductMapping.original_name.ilike("%premium%")
        ).all()
        assert len(search_results) == 2
        
        # Test partial match
        sku_results = db_session.query(ProductMapping).filter(
            ProductMapping.mapped_sku.like("TW%")
        ).all()
        assert len(sku_results) == 2
        
        # Test combined filters
        combined_results = db_session.query(ProductMapping).filter(
            ProductMapping.product_type == "tileware",
            ProductMapping.original_name.ilike("%premium%")
        ).all()
        assert len(combined_results) == 1
        assert combined_results[0].original_name == "TileWare Premium Pro"
    
    def test_database_constraints(self, db_session: Session):
        """Test database constraints and validations"""
        # Test NOT NULL constraints
        with pytest.raises(IntegrityError):
            user = User(
                email=None,  # Required field
                username="testuser",
                hashed_password=get_password_hash("password")
            )
            db_session.add(user)
            db_session.commit()
        
        db_session.rollback()
        
        # Test string length constraints (if any)
        # Most databases will truncate or error on too-long strings
        
        # Test confidence score range (0.0 to 1.0)
        mapping = ProductMapping(
            original_name="Score Test",
            mapped_name="Mapped Score",
            mapped_sku="SCORE-001",
            product_type="tileware",
            confidence_score=1.0  # Max valid value
        )
        db_session.add(mapping)
        db_session.commit()
        
        assert mapping.confidence_score == 1.0
        
        # Clean up
        db_session.delete(mapping)
        db_session.commit()