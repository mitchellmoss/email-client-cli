"""
Authentication endpoint tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models.user import User
from auth import verify_password, get_password_hash


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == test_user.email
        assert data["user"]["username"] == test_user.username
        assert "id" in data["user"]
        assert "hashed_password" not in data["user"]
    
    def test_login_invalid_credentials(self, client: TestClient, test_user: User):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "anypassword"
            }
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"
    
    def test_login_inactive_user(self, client: TestClient, test_db_session: Session):
        """Test login with inactive user"""
        # Create inactive user
        inactive_user = User(
            email="inactive@example.com",
            username="inactive",
            hashed_password=get_password_hash("password123"),
            is_active=False
        )
        test_db_session.add(inactive_user)
        test_db_session.commit()
        
        response = client.post(
            "/api/auth/login",
            data={
                "username": "inactive@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Inactive user"
    
    def test_get_current_user(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test getting current user info"""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert data["is_active"] == True
        assert "hashed_password" not in data
    
    def test_get_current_user_no_auth(self, client: TestClient):
        """Test getting current user without authentication"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
    
    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"
    
    def test_refresh_token(self, client: TestClient, auth_headers: dict):
        """Test token refresh"""
        response = client.post("/api/auth/refresh", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_logout(self, client: TestClient, auth_headers: dict):
        """Test logout"""
        response = client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
    
    def test_register_new_user(self, client: TestClient, superuser_auth_headers: dict):
        """Test registering a new user (admin only)"""
        new_user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpassword123",
            "is_active": True,
            "is_superuser": False
        }
        
        response = client.post(
            "/api/auth/register",
            json=new_user_data,
            headers=superuser_auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == new_user_data["email"]
        assert data["username"] == new_user_data["username"]
        assert "hashed_password" not in data
    
    def test_register_duplicate_email(self, client: TestClient, test_user: User, superuser_auth_headers: dict):
        """Test registering user with duplicate email"""
        new_user_data = {
            "email": test_user.email,  # Duplicate email
            "username": "another_user",
            "password": "password123",
            "is_active": True,
            "is_superuser": False
        }
        
        response = client.post(
            "/api/auth/register",
            json=new_user_data,
            headers=superuser_auth_headers
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_register_non_admin(self, client: TestClient, auth_headers: dict):
        """Test that non-admin cannot register users"""
        new_user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123",
            "is_active": True,
            "is_superuser": False
        }
        
        response = client.post(
            "/api/auth/register",
            json=new_user_data,
            headers=auth_headers
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Not enough permissions"
    
    def test_change_password(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test changing user password"""
        password_data = {
            "current_password": "testpassword123",
            "new_password": "newpassword456"
        }
        
        response = client.post(
            "/api/auth/change-password",
            json=password_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"
        
        # Test login with new password
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,
                "password": "newpassword456"
            }
        )
        assert login_response.status_code == 200
    
    def test_change_password_wrong_current(self, client: TestClient, auth_headers: dict):
        """Test changing password with wrong current password"""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword456"
        }
        
        response = client.post(
            "/api/auth/change-password",
            json=password_data,
            headers=auth_headers
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Incorrect password"


class TestPasswordUtils:
    """Test password utility functions"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)
    
    def test_password_hash_uniqueness(self):
        """Test that same password generates different hashes"""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)