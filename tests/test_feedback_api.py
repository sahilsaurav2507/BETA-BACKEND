import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.dependencies import get_db
from app.models.base import Base
import tempfile
import os

# Create a temporary database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    # Clean up
    Base.metadata.drop_all(bind=engine)

def test_submit_feedback_with_required_fields_only(client):
    """Test submitting feedback with only required fields"""
    feedback_data = {
        "email": "test@example.com",
        "name": "Test User",
        "biggest_hurdle": "A",
        "professional_fear": "A",
        "platform_impact": "This platform would revolutionize my career by providing easy access to share insights."
    }
    
    response = client.post("/feedback/submit", json=feedback_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "feedback_id" in data
    assert "Thank you for your valuable insights" in data["message"]

def test_submit_feedback_with_all_fields(client):
    """Test submitting feedback with all fields filled"""
    feedback_data = {
        "email": "complete@example.com",
        "name": "Complete User",
        "biggest_hurdle": "B",
        "biggest_hurdle_other": None,
        "primary_motivation": "A",
        "time_consuming_part": "C",
        "professional_fear": "B",
        "monetization_considerations": "I have concerns about ethical implications and time investment required.",
        "professional_legacy": "I want to be remembered as someone who made legal knowledge accessible to everyone.",
        "platform_impact": "Such a platform would allow me to reach thousands of people and establish thought leadership."
    }
    
    response = client.post("/feedback/submit", json=feedback_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "feedback_id" in data

def test_submit_feedback_missing_required_fields(client):
    """Test submitting feedback with missing required fields"""
    feedback_data = {
        "email": "test@example.com",
        # Missing name, biggest_hurdle, professional_fear, platform_impact
    }
    
    response = client.post("/feedback/submit", json=feedback_data)
    assert response.status_code == 422  # Validation error

def test_submit_feedback_invalid_email(client):
    """Test submitting feedback with invalid email"""
    feedback_data = {
        "email": "invalid-email",
        "name": "Test User",
        "biggest_hurdle": "A",
        "professional_fear": "A",
        "platform_impact": "This platform would be amazing for my career growth and development."
    }
    
    response = client.post("/feedback/submit", json=feedback_data)
    assert response.status_code == 422  # Validation error

def test_submit_feedback_short_text_fields(client):
    """Test submitting feedback with text fields that are too short"""
    feedback_data = {
        "email": "test@example.com",
        "name": "Test User",
        "biggest_hurdle": "A",
        "professional_fear": "A",
        "platform_impact": "Short",  # Less than 10 characters
        "monetization_considerations": "Brief"  # Less than 10 characters
    }
    
    response = client.post("/feedback/submit", json=feedback_data)
    assert response.status_code == 422  # Validation error

def test_multiple_submissions_allowed(client):
    """Test that multiple submissions are now allowed (24-hour restriction removed)"""
    feedback_data = {
        "email": "repeat@example.com",
        "name": "Repeat User",
        "biggest_hurdle": "A",
        "professional_fear": "A",
        "platform_impact": "This platform would significantly impact my professional development and growth."
    }
    
    # First submission
    response1 = client.post("/feedback/submit", json=feedback_data)
    assert response1.status_code == 200
    
    # Second submission (should be allowed now)
    feedback_data["email"] = "repeat2@example.com"
    response2 = client.post("/feedback/submit", json=feedback_data)
    assert response2.status_code == 200

def test_submit_feedback_with_other_option(client):
    """Test submitting feedback with 'Other' option selected"""
    feedback_data = {
        "email": "other@example.com",
        "name": "Other User",
        "biggest_hurdle": "E",
        "biggest_hurdle_other": "Custom hurdle explanation that is specific to my situation",
        "professional_fear": "A",
        "platform_impact": "This would completely transform how I share knowledge and build my reputation."
    }
    
    response = client.post("/feedback/submit", json=feedback_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
