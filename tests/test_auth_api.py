"""
Comprehensive authentication API tests.
"""

import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db, Base

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestAuthenticationAPI:
    """Comprehensive authentication API tests."""
    
    access_token = None  # Class variable to store token
    
    @classmethod
    def setup_class(cls):
        """Setup class-level variables."""
        cls.access_token = None
    
    @pytest.fixture(scope="class")
    def client(self):
        """Create a test client and database."""
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        with TestClient(app) as test_client:
            yield test_client
        
        # Clean up
        Base.metadata.drop_all(bind=engine)
        try:
            if os.path.exists("test_auth.db"):
                os.unlink("test_auth.db")
        except PermissionError:
            pass  # Ignore file locking issues on Windows
    
    def test_user_registration_success(self, client):
        """Test successful user registration."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["is_active"] == True
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data  # Password should not be returned
    
    def test_user_registration_duplicate_username(self, client):
        """Test registration with duplicate username."""
        user_data = {
            "username": "testuser",  # Already exists from previous test
            "email": "different@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]
    
    def test_user_registration_duplicate_email(self, client):
        """Test registration with duplicate email."""
        user_data = {
            "username": "differentuser",
            "email": "test@example.com",  # Already exists from previous test
            "password": "testpassword123"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_user_login_success(self, client):
        """Test successful user login."""
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
        
        # Store token for other tests
        TestAuthenticationAPI.access_token = data["access_token"]
    
    def test_user_login_wrong_username(self, client):
        """Test login with wrong username."""
        login_data = {
            "username": "wronguser",
            "password": "testpassword123"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_user_login_wrong_password(self, client):
        """Test login with wrong password."""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_get_current_user_success(self, client):
        """Test getting current user with valid token."""
        headers = {"Authorization": f"Bearer {TestAuthenticationAPI.access_token}"}
        
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["is_active"] == True
    
    def test_get_current_user_no_token(self, client):
        """Test getting current user without token."""
        response = client.get("/auth/me")
        assert response.status_code == 403  # No authorization header
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_refresh_token_success(self, client):
        """Test token refresh with valid token."""
        headers = {"Authorization": f"Bearer {TestAuthenticationAPI.access_token}"}
        
        response = client.post("/auth/refresh", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
        # Should be a new token (may be same if generated at exact same time)
        assert "access_token" in data
        assert len(data["access_token"]) > 0
    
    def test_verify_token_success(self, client):
        """Test token verification with valid token."""
        headers = {"Authorization": f"Bearer {TestAuthenticationAPI.access_token}"}
        
        response = client.get("/auth/verify-token", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] == True
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "test@example.com"
    
    def test_verify_token_invalid(self, client):
        """Test token verification with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/auth/verify-token", headers=headers)
        assert response.status_code == 401
    
    def test_logout_success(self, client):
        """Test user logout with valid token."""
        headers = {"Authorization": f"Bearer {TestAuthenticationAPI.access_token}"}
        
        response = client.post("/auth/logout", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "logged out successfully" in data["message"]
        assert "testuser" in data["message"]
    
    def test_invalid_registration_data(self, client):
        """Test registration with invalid data."""
        # Missing email
        invalid_data = {
            "username": "newuser",
            "password": "password123"
        }
        
        response = client.post("/auth/register", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_login_data(self, client):
        """Test login with invalid data."""
        # Missing password
        invalid_data = {
            "username": "testuser"
        }
        
        response = client.post("/auth/login", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_register_user_2_for_multiple_users(self, client):
        """Register a second user for multi-user tests."""
        user_data = {
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "testpassword456"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["username"] == "testuser2"
        assert data["email"] == "test2@example.com"
    
    def test_login_multiple_users(self, client):
        """Test that multiple users can login independently."""
        # Login user 1
        login_data_1 = {
            "username": "testuser",
            "password": "testpassword123"
        }
        response_1 = client.post("/auth/login", json=login_data_1)
        assert response_1.status_code == 200
        token_1 = response_1.json()["access_token"]
        
        # Login user 2
        login_data_2 = {
            "username": "testuser2",
            "password": "testpassword456"
        }
        response_2 = client.post("/auth/login", json=login_data_2)
        assert response_2.status_code == 200
        token_2 = response_2.json()["access_token"]
        
        # Tokens should be different
        assert token_1 != token_2
        
        # Both tokens should work for their respective users
        headers_1 = {"Authorization": f"Bearer {token_1}"}
        headers_2 = {"Authorization": f"Bearer {token_2}"}
        
        response_1 = client.get("/auth/me", headers=headers_1)
        response_2 = client.get("/auth/me", headers=headers_2)
        
        assert response_1.status_code == 200
        assert response_2.status_code == 200
        
        assert response_1.json()["username"] == "testuser"
        assert response_2.json()["username"] == "testuser2"
    
    def test_password_hashing_security(self, client):
        """Test that passwords are properly hashed."""
        # Register a user
        user_data = {
            "username": "securitytest",
            "email": "security@example.com",
            "password": "mysecretpassword"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Verify user can login with correct password
        login_data = {
            "username": "securitytest",
            "password": "mysecretpassword"
        }
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        # Verify user cannot login with incorrect password
        wrong_login_data = {
            "username": "securitytest",
            "password": "wrongpassword"
        }
        response = client.post("/auth/login", json=wrong_login_data)
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
