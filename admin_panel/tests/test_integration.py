"""
End-to-end integration tests for the admin panel
"""
import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from admin_panel.backend.main import app
from admin_panel.backend.database import Base, get_db
from admin_panel.backend.auth import create_access_token, get_password_hash
from admin_panel.backend.models.user import User
from admin_panel.backend.models.product import ProductMapping
from src.order_tracker import OrderTracker


class TestEndToEndFlow:
    """Test complete workflows from login to order processing"""
    
    @pytest.fixture(scope="function")
    def test_db(self):
        """Create a test database"""
        SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        yield TestingSessionLocal()
        
        # Cleanup
        Base.metadata.drop_all(bind=engine)
        os.remove("test_integration.db")
    
    @pytest.fixture(scope="function")
    def client(self, test_db):
        """Create test client with test database"""
        def override_get_db():
            try:
                yield test_db
            finally:
                test_db.close()
        
        app.dependency_overrides[get_db] = override_get_db
        
        with TestClient(app) as c:
            yield c
        
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def admin_user(self, test_db):
        """Create an admin user"""
        user = User(
            email="admin@example.com",
            username="admin",
            hashed_password=get_password_hash("adminpass123"),
            is_active=True,
            is_superuser=True
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        return user
    
    @pytest.fixture
    def regular_user(self, test_db):
        """Create a regular user"""
        user = User(
            email="user@example.com",
            username="regularuser",
            hashed_password=get_password_hash("userpass123"),
            is_active=True,
            is_superuser=False
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        return user
    
    def test_complete_authentication_flow(self, client: TestClient, admin_user: User):
        """Test complete authentication workflow"""
        # 1. Login
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": admin_user.email,
                "password": "adminpass123"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get current user info
        me_response = client.get("/api/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["email"] == admin_user.email
        
        # 3. Change password
        change_pass_response = client.post(
            "/api/auth/change-password",
            json={
                "current_password": "adminpass123",
                "new_password": "newadminpass456"
            },
            headers=headers
        )
        assert change_pass_response.status_code == 200
        
        # 4. Login with new password
        new_login_response = client.post(
            "/api/auth/login",
            data={
                "username": admin_user.email,
                "password": "newadminpass456"
            }
        )
        assert new_login_response.status_code == 200
        
        # 5. Create a new user (admin only)
        new_user_response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "newuserpass123",
                "is_active": True,
                "is_superuser": False
            },
            headers=headers
        )
        assert new_user_response.status_code == 201
        
        # 6. Logout
        logout_response = client.post("/api/auth/logout", headers=headers)
        assert logout_response.status_code == 200
    
    def test_product_mapping_workflow(self, client: TestClient, admin_user: User):
        """Test complete product mapping workflow"""
        # Login
        token = create_access_token(data={"sub": admin_user.email})
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. Check initial mappings (should be empty)
        mappings_response = client.get("/api/products/mappings", headers=headers)
        assert mappings_response.status_code == 200
        assert mappings_response.json()["total"] == 0
        
        # 2. Create multiple mappings
        mappings_to_create = [
            {
                "original_name": "TileWare Premium Tile A",
                "mapped_name": "TileWare Premium Tile Pro A",
                "mapped_sku": "TW-PREM-A",
                "product_type": "tileware",
                "confidence_score": 0.95
            },
            {
                "original_name": "Laticrete Adhesive B",
                "mapped_name": "Laticrete Pro Adhesive B",
                "mapped_sku": "LAT-ADH-B",
                "product_type": "laticrete",
                "confidence_score": 0.88
            }
        ]
        
        created_ids = []
        for mapping in mappings_to_create:
            create_response = client.post(
                "/api/products/mappings",
                json=mapping,
                headers=headers
            )
            assert create_response.status_code == 201
            created_ids.append(create_response.json()["id"])
        
        # 3. Verify mappings were created
        mappings_response = client.get("/api/products/mappings", headers=headers)
        assert mappings_response.status_code == 200
        assert mappings_response.json()["total"] == 2
        
        # 4. Search for specific mapping
        search_response = client.get(
            "/api/products/mappings?search=premium",
            headers=headers
        )
        assert search_response.status_code == 200
        assert len(search_response.json()["mappings"]) == 1
        
        # 5. Update a mapping
        update_response = client.put(
            f"/api/products/mappings/{created_ids[0]}",
            json={
                "mapped_name": "Updated TileWare Premium",
                "confidence_score": 0.99
            },
            headers=headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["mapped_name"] == "Updated TileWare Premium"
        
        # 6. Get statistics
        stats_response = client.get("/api/products/stats", headers=headers)
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total_mappings"] == 2
        assert stats["mappings_by_type"]["tileware"] == 1
        assert stats["mappings_by_type"]["laticrete"] == 1
        
        # 7. Delete a mapping
        delete_response = client.delete(
            f"/api/products/mappings/{created_ids[1]}",
            headers=headers
        )
        assert delete_response.status_code == 200
        
        # 8. Verify deletion
        final_mappings = client.get("/api/products/mappings", headers=headers)
        assert final_mappings.json()["total"] == 1
    
    def test_order_processing_workflow(self, client: TestClient, admin_user: User, test_db: Session):
        """Test complete order processing workflow"""
        # Setup
        token = create_access_token(data={"sub": admin_user.email})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create product mapping
        mapping = ProductMapping(
            original_name="TileWare Test Product",
            mapped_name="TileWare Test Product Pro",
            mapped_sku="TW-TEST-001",
            product_type="tileware",
            confidence_score=0.95
        )
        test_db.add(mapping)
        test_db.commit()
        
        # 1. Check initial orders (should be empty)
        orders_response = client.get("/api/orders", headers=headers)
        assert orders_response.status_code == 200
        assert orders_response.json()["total"] == 0
        
        # 2. Simulate order creation (would normally come from email processing)
        # In real scenario, this would be done by the email processor
        order_data = {
            "order_id": "TEST-001",
            "customer_name": "Test Customer",
            "email": "customer@test.com",
            "order_date": datetime.now().isoformat(),
            "status": "pending",
            "total_amount": 299.99,
            "products": [
                {
                    "name": "TileWare Test Product",
                    "sku": "TW-TEST-001",
                    "quantity": 2,
                    "price": 149.99
                }
            ],
            "shipping_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "TC",
                "zip": "12345"
            },
            "shipping_method": "Standard"
        }
        
        # Note: In real app, orders would be created by the email processor
        # Here we're simulating the order retrieval
        
        # 3. Get order statistics
        stats_response = client.get("/api/orders/stats", headers=headers)
        assert stats_response.status_code == 200
        
        # 4. Export orders (even if empty)
        export_response = client.get(
            "/api/orders/export?format=csv",
            headers=headers
        )
        assert export_response.status_code == 200
        assert export_response.headers["content-type"] == "text/csv; charset=utf-8"
    
    def test_settings_workflow(self, client: TestClient, admin_user: User):
        """Test complete settings management workflow"""
        # Login
        token = create_access_token(data={"sub": admin_user.email})
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. Get current email settings
        email_settings = client.get("/api/settings/email", headers=headers)
        assert email_settings.status_code == 200
        
        # 2. Update email settings
        update_response = client.put(
            "/api/settings/email",
            json={
                "imap": {
                    "server": "imap.newserver.com",
                    "port": 993
                },
                "processing": {
                    "check_interval_minutes": 10
                }
            },
            headers=headers
        )
        assert update_response.status_code == 200
        
        # 3. Test email connections
        test_response = client.post("/api/settings/email/test", headers=headers)
        assert test_response.status_code == 200
        
        # 4. Get API settings
        api_settings = client.get("/api/settings/api", headers=headers)
        assert api_settings.status_code == 200
        
        # 5. Update notification settings
        notif_response = client.put(
            "/api/settings/notifications",
            json={
                "email_notifications": {
                    "enabled": True,
                    "recipients": ["admin@example.com"],
                    "events": ["order_failed", "system_error"]
                }
            },
            headers=headers
        )
        assert notif_response.status_code == 200
        
        # 6. Get system info
        system_info = client.get("/api/settings/system/info", headers=headers)
        assert system_info.status_code == 200
        assert "version" in system_info.json()
        assert "platform" in system_info.json()
    
    def test_permission_enforcement(self, client: TestClient, regular_user: User, admin_user: User):
        """Test that permissions are properly enforced"""
        # Get tokens for both users
        regular_token = create_access_token(data={"sub": regular_user.email})
        admin_token = create_access_token(data={"sub": admin_user.email})
        
        regular_headers = {"Authorization": f"Bearer {regular_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test admin-only endpoints with regular user
        admin_only_endpoints = [
            ("GET", "/api/settings/email"),
            ("PUT", "/api/settings/email"),
            ("POST", "/api/settings/email/test"),
            ("GET", "/api/settings/api"),
            ("PUT", "/api/settings/api"),
            ("POST", "/api/auth/register"),
            ("POST", "/api/orders/bulk-update"),
            ("DELETE", "/api/products/mappings/1"),
            ("POST", "/api/products/mappings/import"),
            ("POST", "/api/settings/backup/create"),
            ("DELETE", "/api/settings/system/logs")
        ]
        
        for method, endpoint in admin_only_endpoints:
            if method == "GET":
                response = client.get(endpoint, headers=regular_headers)
            elif method == "POST":
                response = client.post(endpoint, headers=regular_headers, json={})
            elif method == "PUT":
                response = client.put(endpoint, headers=regular_headers, json={})
            elif method == "DELETE":
                response = client.delete(endpoint, headers=regular_headers)
            
            assert response.status_code == 403, f"Expected 403 for {method} {endpoint}"
            assert response.json()["detail"] == "Not enough permissions"
        
        # Test that admin can access these endpoints
        for method, endpoint in admin_only_endpoints[:3]:  # Test a few
            if method == "GET":
                response = client.get(endpoint, headers=admin_headers)
            elif method == "POST":
                response = client.post(endpoint, headers=admin_headers, json={})
            elif method == "PUT":
                response = client.put(endpoint, headers=admin_headers, json={})
            
            # Should not be 403
            assert response.status_code != 403, f"Admin should access {method} {endpoint}"
    
    def test_concurrent_operations(self, client: TestClient, admin_user: User):
        """Test handling of concurrent operations"""
        # Login
        token = create_access_token(data={"sub": admin_user.email})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create multiple mappings concurrently
        import concurrent.futures
        
        def create_mapping(index):
            return client.post(
                "/api/products/mappings",
                json={
                    "original_name": f"Concurrent Product {index}",
                    "mapped_name": f"Mapped Concurrent {index}",
                    "mapped_sku": f"CONC-{index:03d}",
                    "product_type": "tileware",
                    "confidence_score": 0.9
                },
                headers=headers
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_mapping, i) for i in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        assert all(r.status_code == 201 for r in results)
        
        # Verify all were created
        mappings = client.get("/api/products/mappings", headers=headers)
        assert mappings.json()["total"] == 10
    
    def test_error_recovery(self, client: TestClient, admin_user: User):
        """Test system recovery from various error conditions"""
        token = create_access_token(data={"sub": admin_user.email})
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. Test invalid data handling
        invalid_mapping = client.post(
            "/api/products/mappings",
            json={
                "original_name": "",  # Invalid: empty name
                "mapped_name": "Test",
                "mapped_sku": "TEST",
                "product_type": "invalid_type"  # Invalid type
            },
            headers=headers
        )
        assert invalid_mapping.status_code == 422
        
        # 2. Test duplicate handling
        first_mapping = client.post(
            "/api/products/mappings",
            json={
                "original_name": "Duplicate Test",
                "mapped_name": "Mapped Duplicate",
                "mapped_sku": "DUP-001",
                "product_type": "tileware",
                "confidence_score": 0.9
            },
            headers=headers
        )
        assert first_mapping.status_code == 201
        
        duplicate_mapping = client.post(
            "/api/products/mappings",
            json={
                "original_name": "Duplicate Test",  # Same original name
                "mapped_name": "Different Mapped",
                "mapped_sku": "DUP-002",
                "product_type": "tileware",
                "confidence_score": 0.8
            },
            headers=headers
        )
        assert duplicate_mapping.status_code == 400
        
        # 3. Test non-existent resource handling
        not_found = client.get("/api/orders/NONEXISTENT", headers=headers)
        assert not_found.status_code == 404
        
        # 4. Test malformed request handling
        malformed = client.post(
            "/api/products/mappings",
            data="not json",  # Not JSON
            headers={**headers, "Content-Type": "application/json"}
        )
        assert malformed.status_code == 422
    
    def test_data_consistency(self, client: TestClient, admin_user: User, test_db: Session):
        """Test data consistency across operations"""
        token = create_access_token(data={"sub": admin_user.email})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create initial data
        mapping_response = client.post(
            "/api/products/mappings",
            json={
                "original_name": "Consistency Test Product",
                "mapped_name": "Mapped Consistency Product",
                "mapped_sku": "CONS-001",
                "product_type": "tileware",
                "confidence_score": 0.92
            },
            headers=headers
        )
        assert mapping_response.status_code == 201
        mapping_id = mapping_response.json()["id"]
        
        # Update the mapping
        update_response = client.put(
            f"/api/products/mappings/{mapping_id}",
            json={
                "confidence_score": 0.95,
                "mapped_name": "Updated Consistency Product"
            },
            headers=headers
        )
        assert update_response.status_code == 200
        
        # Verify the update persisted
        get_response = client.get(f"/api/products/mappings/{mapping_id}", headers=headers)
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["confidence_score"] == 0.95
        assert data["mapped_name"] == "Updated Consistency Product"
        assert data["original_name"] == "Consistency Test Product"  # Unchanged
        
        # Verify in listing
        list_response = client.get(
            "/api/products/mappings?search=consistency",
            headers=headers
        )
        assert list_response.status_code == 200
        assert len(list_response.json()["mappings"]) == 1
        assert list_response.json()["mappings"][0]["id"] == mapping_id