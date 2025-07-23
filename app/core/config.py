"""
Configuration settings for the Lawvriksh application.

Create a .env file in the backend/ directory with the following content:
# Database Configuration
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
DB_HOST=localhost
DB_PORT=3306

# Or use DATABASE_URL directly (takes precedence over individual DB_* variables)
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/lawvriksh

# Security
JWT_SECRET_KEY=your-super-secret-key-here-make-it-long-and-random

# Message Queue
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Email Configuration
EMAIL_FROM=info@lawvriksh.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Application Settings
CACHE_DIR=./cache
"""

import os
import secrets
from pathlib import Path
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database Configuration
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: Optional[str] = None

    # Alternative: Direct database URL (takes precedence over individual DB_* variables)
    DATABASE_URL: Optional[str] = None

    # Application Settings
    CACHE_DIR: str = "./cache"

    # Security Settings
    JWT_SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT token signing. Should be a long, random string."
    )

    # Message Queue
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    # Email Configuration
    EMAIL_FROM: str = "info@lawvriksh.com"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = "info@lawvriksh.com"
    SMTP_PASSWORD: str = Field(
        default="",
        description="SMTP password - should be set via environment variable"
    )

    # Frontend Configuration
    FRONTEND_URL: str = "http://localhost:3000"

    @validator('JWT_SECRET_KEY')
    def validate_jwt_secret(cls, v):
        """Ensure JWT secret key is sufficiently secure."""
        if len(v) < 32:
            raise ValueError('JWT_SECRET_KEY must be at least 32 characters long')
        if v == "supersecretkey":
            raise ValueError('JWT_SECRET_KEY cannot be the default insecure value')
        return v

    @validator('SMTP_PASSWORD')
    def validate_smtp_password(cls, v):
        """Warn if SMTP password is not set."""
        if not v:
            # Only warn in development, not during import
            import os
            if os.getenv('ENVIRONMENT', 'development') == 'development':
                import logging
                logging.getLogger(__name__).warning("SMTP_PASSWORD is not set. Email functionality may not work.")
        return v

    @property
    def database_url(self) -> str:
        """Get the database URL, preferring DATABASE_URL if set, otherwise constructing from components."""
        if self.DATABASE_URL:
            return self.DATABASE_URL

        if not all([self.DB_USER, self.DB_PASSWORD, self.DB_NAME]):
            # Provide a helpful error message with setup instructions
            error_msg = (
                "Database configuration is incomplete. Please either:\n"
                "1. Set DATABASE_URL environment variable, or\n"
                "2. Set all of: DB_USER, DB_PASSWORD, and DB_NAME\n\n"
                "To fix this:\n"
                "- Copy .env.example to .env: cp .env.example .env\n"
                "- Edit .env with your database credentials\n"
                "- Or set DATABASE_URL directly in your environment"
            )
            raise ValueError(error_msg)

        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    class Config:
        # Find .env file relative to this config file
        _current_dir = Path(__file__).parent.parent.parent  # Go up to backend/ directory
        env_file = str(_current_dir / ".env")
        case_sensitive = True
        # Allow extra fields for forward compatibility
        extra = "ignore"


# Create settings instance
try:
    settings = Settings()
except Exception as e:
    print(f"Error loading configuration: {e}")
    print("Please check your .env file or environment variables.")
    raise