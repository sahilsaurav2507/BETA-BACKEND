import pytest
from fastapi import status

class TestAdmin:
    def test_admin_login_success(self, client, test_admin_user):
        """Test successful admin login."""
        response = client.post("/admin/login", json={
            "email": "admin@example.com",
            "password": "adminpassword"
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_admin_login_non_admin_user(self, client, test_user):
        """Test admin login with non-admin user."""
        response = client.post("/admin/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin credentials required" in response.json()["detail"]

    def test_admin_login_invalid_credentials(self, client, test_admin_user):
        """Test admin login with wrong password."""
        response = client.post("/admin/login", json={
            "email": "admin@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_dashboard_success(self, client, admin_headers):
        """Test admin dashboard access."""
        response = client.get("/admin/dashboard", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "overview" in data
        assert "platform_breakdown" in data
        assert "growth_metrics" in data

    def test_admin_dashboard_unauthorized(self, client, auth_headers):
        """Test admin dashboard with non-admin user."""
        response = client.get("/admin/dashboard", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_users_success(self, client, admin_headers, test_user):
        """Test admin users list."""
        response = client.get("/admin/users", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["users"]) >= 1
        assert "pagination" in data

    def test_admin_users_with_search(self, client, admin_headers, test_user):
        """Test admin users list with search."""
        response = client.get("/admin/users?search=Test", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["users"]) >= 1

    def test_admin_users_unauthorized(self, client, auth_headers):
        """Test admin users with non-admin user."""
        response = client.get("/admin/users", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_promote_user_success(self, client, admin_headers, test_user):
        """Test promoting a user to admin."""
        response = client.post("/admin/promote", 
            json={"user_id": test_user.id}, 
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert "promoted to admin" in response.json()["message"]

    def test_promote_user_already_admin(self, client, admin_headers, test_admin_user):
        """Test promoting a user who is already admin."""
        response = client.post("/admin/promote", 
            json={"user_id": test_admin_user.id}, 
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already an admin" in response.json()["detail"]

    def test_promote_nonexistent_user(self, client, admin_headers):
        """Test promoting a non-existent user."""
        response = client.post("/admin/promote", 
            json={"user_id": 99999}, 
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_promote_user_unauthorized(self, client, auth_headers, test_user):
        """Test promoting user with non-admin user."""
        response = client.post("/admin/promote", 
            json={"user_id": test_user.id}, 
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_send_bulk_email_success(self, client, admin_headers, test_user):
        """Test sending bulk email."""
        response = client.post("/admin/send-bulk-email", 
            json={
                "subject": "Test Email",
                "body": "Test body",
                "min_points": 0
            }, 
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert "Bulk email sent" in response.json()["message"]

    def test_send_bulk_email_no_users(self, client, admin_headers):
        """Test sending bulk email with no users matching criteria."""
        response = client.post("/admin/send-bulk-email", 
            json={
                "subject": "Test Email",
                "body": "Test body",
                "min_points": 1000
            }, 
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "No users found" in response.json()["detail"]

    def test_send_bulk_email_unauthorized(self, client, auth_headers):
        """Test sending bulk email with non-admin user."""
        response = client.post("/admin/send-bulk-email", 
            json={
                "subject": "Test Email",
                "body": "Test body"
            }, 
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN 