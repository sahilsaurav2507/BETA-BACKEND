import pytest
from fastapi import status
from app.models.share import PlatformEnum

class TestShares:
    def test_share_first_time_success(self, client, auth_headers):
        """Test successful first share on a platform."""
        response = client.post("/shares/twitter", headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["platform"] == "twitter"
        assert data["points_earned"] == 1
        assert data["total_points"] == 1
        assert "earned 1 points" in data["message"]

    def test_share_duplicate_platform_no_points(self, client, auth_headers):
        """Test sharing on same platform again - should not award points."""
        # First share
        response1 = client.post("/shares/facebook", headers=auth_headers)
        assert response1.status_code == status.HTTP_201_CREATED
        assert response1.json()["points_earned"] == 3
        
        # Second share on same platform
        response2 = client.post("/shares/facebook", headers=auth_headers)
        assert response2.status_code == status.HTTP_201_CREATED
        assert response2.json()["points_earned"] == 0
        assert "No additional points awarded" in response2.json()["message"]

    def test_share_different_platforms(self, client, auth_headers):
        """Test sharing on different platforms awards correct points."""
        # Twitter = 1 point
        response1 = client.post("/shares/twitter", headers=auth_headers)
        assert response1.json()["points_earned"] == 1
        
        # Instagram = 2 points
        response2 = client.post("/shares/instagram", headers=auth_headers)
        assert response2.json()["points_earned"] == 2
        
        # LinkedIn = 5 points
        response3 = client.post("/shares/linkedin", headers=auth_headers)
        assert response3.json()["points_earned"] == 5
        
        # Facebook = 3 points
        response4 = client.post("/shares/facebook", headers=auth_headers)
        assert response4.json()["points_earned"] == 3

    def test_share_invalid_platform(self, client, auth_headers):
        """Test sharing on invalid platform."""
        response = client.post("/shares/invalid_platform", headers=auth_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid platform" in response.json()["detail"]

    def test_share_unauthorized(self, client):
        """Test sharing without authentication."""
        response = client.post("/shares/twitter")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_share_history_success(self, client, auth_headers):
        """Test getting share history."""
        # Create some shares first
        client.post("/shares/twitter", headers=auth_headers)
        client.post("/shares/facebook", headers=auth_headers)
        
        response = client.get("/shares/history", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["shares"]) == 2
        assert data["pagination"]["total"] == 2

    def test_share_history_filtered_by_platform(self, client, auth_headers):
        """Test getting share history filtered by platform."""
        # Create shares on different platforms
        client.post("/shares/twitter", headers=auth_headers)
        client.post("/shares/facebook", headers=auth_headers)
        
        response = client.get("/shares/history?platform=twitter", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["shares"]) == 1
        assert data["shares"][0]["platform"] == "twitter"

    def test_share_analytics_success(self, client, auth_headers):
        """Test getting share analytics."""
        # Create shares on different platforms
        client.post("/shares/twitter", headers=auth_headers)
        client.post("/shares/facebook", headers=auth_headers)
        client.post("/shares/linkedin", headers=auth_headers)
        
        response = client.get("/shares/analytics", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_shares"] == 3
        assert "twitter" in data["points_breakdown"]
        assert "facebook" in data["points_breakdown"]
        assert "linkedin" in data["points_breakdown"]
        assert data["points_breakdown"]["twitter"]["points"] == 1
        assert data["points_breakdown"]["facebook"]["points"] == 3
        assert data["points_breakdown"]["linkedin"]["points"] == 5

    def test_share_analytics_no_shares(self, client, auth_headers):
        """Test analytics when user has no shares."""
        response = client.get("/shares/analytics", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_shares"] == 0
        assert len(data["recent_activity"]) == 0

    def test_share_history_unauthorized(self, client):
        """Test share history without authentication."""
        response = client.get("/shares/history")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_share_analytics_unauthorized(self, client):
        """Test share analytics without authentication."""
        response = client.get("/shares/analytics")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED 