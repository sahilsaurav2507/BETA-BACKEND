import pytest
from fastapi import status

class TestUsers:
    def test_get_profile_success(self, client, test_user):
        """Test getting user profile by ID."""
        response = client.get(f"/users/{test_user.id}/profile")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == test_user.id
        assert data["name"] == test_user.name
        assert data["email"] == test_user.email

    def test_get_profile_nonexistent_user(self, client):
        """Test getting profile for non-existent user."""
        response = client.get("/users/99999/profile")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_profile_success(self, client, auth_headers):
        """Test updating user profile."""
        response = client.put("/users/profile", 
            json={"name": "Updated Name"}, 
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_update_profile_unauthorized(self, client):
        """Test updating profile without authentication."""
        response = client.put("/users/profile", json={"name": "Updated Name"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_view_all_users_admin_success(self, client, admin_headers, test_user):
        """Test admin viewing all users."""
        response = client.get("/users/view", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any(user["email"] == test_user.email for user in data)

    def test_view_all_users_unauthorized(self, client, auth_headers):
        """Test viewing all users with non-admin user."""
        response = client.get("/users/view", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_export_users_csv_admin_success(self, client, admin_headers, test_user):
        """Test admin exporting users as CSV."""
        response = client.get("/users/export", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/csv"
        assert "attachment; filename=users.csv" in response.headers["content-disposition"]

    def test_export_users_json_admin_success(self, client, admin_headers, test_user):
        """Test admin exporting users as JSON."""
        response = client.get("/users/export?format=json", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any(user["email"] == test_user.email for user in data)

    def test_export_users_with_filter(self, client, admin_headers, test_user):
        """Test exporting users with minimum points filter."""
        response = client.get("/users/export?min_points=0", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_export_users_unauthorized(self, client, auth_headers):
        """Test exporting users with non-admin user."""
        response = client.get("/users/export", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_export_users_no_users_matching_filter(self, client, admin_headers):
        """Test exporting users with filter that matches no users."""
        response = client.get("/users/export?min_points=1000", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        # Should return empty CSV/JSON, not error

    def test_profile_includes_admin_status(self, client, test_admin_user):
        """Test that profile includes admin status."""
        response = client.get(f"/users/{test_admin_user.id}/profile")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_admin"] == True

    def test_profile_includes_points_and_shares(self, client, test_user):
        """Test that profile includes points and shares count."""
        response = client.get(f"/users/{test_user.id}/profile")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_points" in data
        assert "shares_count" in data 