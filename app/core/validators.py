"""
Input validation utilities for the Lawvriksh application.
Provides comprehensive validation for user inputs and business logic.
"""

import re
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator, EmailStr
from app.core.error_handlers import BusinessLogicError

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error with detailed information."""
    
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"Validation failed for {field}: {message}")

class PasswordValidator:
    """Password validation utility."""
    
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    
    @staticmethod
    def validate_password(password: str) -> List[str]:
        """
        Validate password strength and return list of errors.
        
        Args:
            password: Password to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not password:
            errors.append("Password is required")
            return errors
        
        if len(password) < PasswordValidator.MIN_LENGTH:
            errors.append(f"Password must be at least {PasswordValidator.MIN_LENGTH} characters long")
        
        if len(password) > PasswordValidator.MAX_LENGTH:
            errors.append(f"Password must not exceed {PasswordValidator.MAX_LENGTH} characters")
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for common weak passwords
        weak_passwords = [
            'password', '123456', 'password123', 'admin', 'qwerty',
            'letmein', 'welcome', 'monkey', '1234567890'
        ]
        if password.lower() in weak_passwords:
            errors.append("Password is too common and easily guessable")
        
        return errors
    
    @staticmethod
    def is_valid_password(password: str) -> bool:
        """Check if password is valid."""
        return len(PasswordValidator.validate_password(password)) == 0

class EmailValidator:
    """Email validation utility."""
    
    @staticmethod
    def validate_email(email: str) -> List[str]:
        """
        Validate email format and domain.
        
        Args:
            email: Email to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not email:
            errors.append("Email is required")
            return errors
        
        # Basic format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            errors.append("Invalid email format")
        
        # Check email length
        if len(email) > 254:
            errors.append("Email address is too long")
        
        # Check for disposable email domains (basic list)
        disposable_domains = [
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'throwaway.email'
        ]
        domain = email.split('@')[-1].lower() if '@' in email else ''
        if domain in disposable_domains:
            errors.append("Disposable email addresses are not allowed")
        
        return errors
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Check if email is valid."""
        return len(EmailValidator.validate_email(email)) == 0

class NameValidator:
    """Name validation utility."""
    
    MIN_LENGTH = 2
    MAX_LENGTH = 100
    
    @staticmethod
    def validate_name(name: str) -> List[str]:
        """
        Validate user name.
        
        Args:
            name: Name to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not name:
            errors.append("Name is required")
            return errors
        
        # Remove extra whitespace
        name = name.strip()
        
        if len(name) < NameValidator.MIN_LENGTH:
            errors.append(f"Name must be at least {NameValidator.MIN_LENGTH} characters long")
        
        if len(name) > NameValidator.MAX_LENGTH:
            errors.append(f"Name must not exceed {NameValidator.MAX_LENGTH} characters")
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
            errors.append("Name can only contain letters, spaces, hyphens, apostrophes, and periods")
        
        # Check for reasonable format (not all spaces or special chars)
        if not re.search(r'[a-zA-Z]', name):
            errors.append("Name must contain at least one letter")
        
        return errors
    
    @staticmethod
    def is_valid_name(name: str) -> bool:
        """Check if name is valid."""
        return len(NameValidator.validate_name(name)) == 0

class BusinessRuleValidator:
    """Business logic validation utility."""
    
    @staticmethod
    def validate_share_platform(platform: str) -> List[str]:
        """Validate social media platform."""
        errors = []
        
        valid_platforms = ['facebook', 'twitter', 'linkedin', 'instagram', 'whatsapp']
        if platform.lower() not in valid_platforms:
            errors.append(f"Invalid platform. Must be one of: {', '.join(valid_platforms)}")
        
        return errors
    
    @staticmethod
    def validate_pagination(page: int, limit: int) -> List[str]:
        """Validate pagination parameters."""
        errors = []
        
        if page < 1:
            errors.append("Page number must be greater than 0")
        
        if limit < 1:
            errors.append("Limit must be greater than 0")
        
        if limit > 100:
            errors.append("Limit cannot exceed 100 items per page")
        
        return errors
    
    @staticmethod
    def validate_points_range(points: int) -> List[str]:
        """Validate points value."""
        errors = []
        
        if points < 0:
            errors.append("Points cannot be negative")
        
        if points > 1000000:  # 1 million points max
            errors.append("Points value is too large")
        
        return errors

def validate_user_input(name: str, email: str, password: str) -> Dict[str, List[str]]:
    """
    Comprehensive user input validation.
    
    Args:
        name: User's name
        email: User's email
        password: User's password
        
    Returns:
        Dictionary with field names as keys and error lists as values
    """
    validation_errors = {}
    
    # Validate name
    name_errors = NameValidator.validate_name(name)
    if name_errors:
        validation_errors['name'] = name_errors
    
    # Validate email
    email_errors = EmailValidator.validate_email(email)
    if email_errors:
        validation_errors['email'] = email_errors
    
    # Validate password
    password_errors = PasswordValidator.validate_password(password)
    if password_errors:
        validation_errors['password'] = password_errors
    
    return validation_errors

def raise_validation_error_if_any(validation_errors: Dict[str, List[str]]):
    """
    Raise BusinessLogicError if there are any validation errors.
    
    Args:
        validation_errors: Dictionary of validation errors
        
    Raises:
        BusinessLogicError: If validation errors exist
    """
    if validation_errors:
        error_messages = []
        for field, errors in validation_errors.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")
        
        raise BusinessLogicError(
            message="Validation failed: " + "; ".join(error_messages),
            error_code="VALIDATION_ERROR"
        )

# Pydantic validators for use in schemas
def validate_strong_password(cls, v):
    """Pydantic validator for strong passwords."""
    errors = PasswordValidator.validate_password(v)
    if errors:
        raise ValueError("; ".join(errors))
    return v

def validate_clean_name(cls, v):
    """Pydantic validator for names."""
    errors = NameValidator.validate_name(v)
    if errors:
        raise ValueError("; ".join(errors))
    return v.strip()

def validate_platform(cls, v):
    """Pydantic validator for social media platforms."""
    errors = BusinessRuleValidator.validate_share_platform(v)
    if errors:
        raise ValueError("; ".join(errors))
    return v.lower()
