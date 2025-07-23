import os
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.main import app
from app.core.dependencies import get_db
from app.models.user import User
from app.models.share import ShareEvent, PlatformEnum
from passlib.context import CryptContext

# Set testing environment variable
os.environ["TESTING"] = "true"

# Mock Celery tasks for testing
mock_celery_task = Mock()
mock_celery_task.delay = Mock(return_value=Mock(id="test-task-id"))

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    # Drop all tables first to ensure clean state
    Base.metadata.drop_all(bind=engine)
    # Create all tables
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()  # Rollback any uncommitted changes
        session.close()
        # Clean up after test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Mock Celery tasks during testing
    with patch('app.api.auth.send_welcome_email_task', mock_celery_task), \
         patch('app.api.admin.send_bulk_email_task', mock_celery_task):
        yield TestClient(app)

    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    import uuid
    unique_email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        name="Test User",
        email=unique_email,
        password_hash=pwd_context.hash("testpassword"),
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_admin_user(db_session):
    """Create a test admin user."""
    import uuid
    unique_email = f"admin-{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        name="Admin User",
        email=unique_email,
        password_hash=pwd_context.hash("adminpassword"),
        is_admin=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for a test user."""
    response = client.post("/auth/login", json={
        "email": test_user.email,
        "password": "testpassword"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(client, test_admin_user):
    """Get authentication headers for a test admin user."""
    response = client.post("/auth/login", json={
        "email": test_admin_user.email,
        "password": "adminpassword"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}