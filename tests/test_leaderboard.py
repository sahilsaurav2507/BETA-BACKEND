import pytest
from fastapi import status

class TestLeaderboard:
    def test_leaderboard_success(self, client, auth_headers):
        """Test getting leaderboard."""
        response = client.get("/leaderboard", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "leaderboard" in data
        assert "pagination" in data
        assert "metadata" in data

    def test_leaderboard_with_pagination(self, client, auth_headers):
        """Test leaderboard with pagination parameters."""
        response = client.get("/leaderboard?page=1&limit=10", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 10

    def test_leaderboard_unauthorized(self, client):
        """Test leaderboard without authentication."""
        response = client.get("/leaderboard")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_leaderboard_around_me_success(self, client, auth_headers):
        """Test getting leaderboard around current user."""
        response = client.get("/leaderboard/around-me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "surrounding_users" in data
        assert "your_stats" in data

    def test_leaderboard_around_me_with_range(self, client, auth_headers):
        """Test around-me with custom range."""
        response = client.get("/leaderboard/around-me?range=3", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["surrounding_users"]) <= 7  # 3 above + 3 below + current user

    def test_leaderboard_around_me_unauthorized(self, client):
        """Test around-me without authentication."""
        response = client.get("/leaderboard/around-me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_top_performers_success(self, client):
        """Test getting top performers."""
        response = client.get("/leaderboard/top-performers")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "period" in data
        assert "top_performers" in data
        assert "period_stats" in data

    def test_top_performers_with_parameters(self, client):
        """Test top performers with custom parameters."""
        response = client.get("/leaderboard/top-performers?period=weekly&limit=5")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["period"] == "weekly"
        assert len(data["top_performers"]) <= 5

    def test_leaderboard_with_multiple_users(self, client, auth_headers, db_session):
        """Test leaderboard with multiple users having different points."""
        from app.models.user import User
        from passlib.context import CryptContext
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Create additional users with different point values
        user1 = User(
            name="User 1",
            email="user1@example.com",
            password_hash=pwd_context.hash("password"),
            total_points=100,
            shares_count=5
        )
        user2 = User(
            name="User 2", 
            email="user2@example.com",
            password_hash=pwd_context.hash("password"),
            total_points=50,
            shares_count=3
        )
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()
        
        response = client.get("/leaderboard", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["leaderboard"]) >= 3  # At least 3 users total

    def test_leaderboard_metadata_includes_user_rank(self, client, auth_headers):
        """Test that leaderboard metadata includes current user's rank."""
        response = client.get("/leaderboard", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "your_rank" in data["metadata"]
        assert "your_points" in data["metadata"] 