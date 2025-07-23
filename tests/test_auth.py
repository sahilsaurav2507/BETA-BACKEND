import pytest
from fastapi import status

class TestAuth:
    def test_signup_success(self, client):
        """Test successful user signup."""
        response = client.post("/auth/signup", json={
            "name": "New User",
            "email": "newuser@example.com",
            "password": "newpassword123"
        })
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "New User"
        assert data["email"] == "newuser@example.com"
        assert data["total_points"] == 0
        assert data["shares_count"] == 0
        assert data["is_admin"] == False

    def test_signup_duplicate_email(self, client, test_user):
        """Test signup with existing email."""
        response = client.post("/auth/signup", json={
            "name": "Another User",
            "email": test_user.email,
            "password": "password123"
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"]

    def test_signup_invalid_email(self, client):
        """Test signup with invalid email format."""
        response = client.post("/auth/signup", json={
            "name": "Test User",
            "email": "invalid-email",
            "password": "password123"
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_signup_short_password(self, client):
        """Test signup with password too short."""
        response = client.post("/auth/signup", json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "123"
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600

    def test_login_invalid_credentials(self, client, test_user):
        """Test login with wrong password."""
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "password123"
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_me_success(self, client, auth_headers):
        """Test getting current user info."""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Test User"
        assert data["email"] == "test@example.com"

    def test_get_me_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get("/auth/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_me_no_token(self, client):
        """Test getting current user without token."""
        response = client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED 