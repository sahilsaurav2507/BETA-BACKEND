from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.token import Token
from app.services.user_service import create_user, authenticate_user, create_jwt_for_user, get_user_by_email
from app.core.security import verify_access_token
from fastapi.security import OAuth2PasswordBearer
from app.utils.monitoring import inc_user_signup
from app.utils.registration_manager import registration_manager

# Database-driven email queue imports (replaces Celery)
from app.models.email_queue import EmailType
from app.schemas.email_queue import EmailQueueCreate
from app.services.email_queue_service import (
    add_email_to_queue, get_next_schedule_info, add_campaign_emails_for_user
)

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def _process_user_registration(user_data: dict) -> dict:
    """
    Internal function to process user registration.
    Used by the round-robin registration manager.
    """
    from app.core.dependencies import get_db

    # Get database session
    db = next(get_db())

    try:
        # Check if user already exists
        existing_user = get_user_by_email(db, user_data["email"])
        if existing_user:
            raise Exception("Email already registered")

        # Create new user
        user_in = UserCreate(**user_data)
        user = create_user(db, user_in)

        # Add welcome email to database queue (replaces Celery)
        try:
            email_data = EmailQueueCreate(
                user_email=user.email,
                user_name=user.name,
                email_type=EmailType.welcome
            )
            email_queue_entry = add_email_to_queue(db, email_data)

            import logging
            logging.getLogger(__name__).info(
                f"Welcome email queued for {user.email} "
                f"(ID: {email_queue_entry.id}, scheduled: {email_queue_entry.scheduled_time})"
            )
        except Exception as email_error:
            import logging
            logging.getLogger(__name__).warning(f"Failed to queue welcome email: {email_error}")

        # Update metrics
        inc_user_signup()

        return {
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at,
            "total_points": user.total_points,
            "shares_count": user.shares_count,
            "default_rank": user.default_rank,
            "current_rank": user.current_rank,
            "is_admin": user.is_admin
        }

    finally:
        db.close()

@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account with round-robin processing (max 10 concurrent).

    Args:
        user_in: User registration data
        db: Database session

    Returns:
        UserResponse: Created user information

    Raises:
        HTTPException: If email is already registered or creation fails
    """
    # Quick check if user already exists (before queuing)
    existing_user = get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    try:
        # Create new user directly (simplified approach)
        user = create_user(db, user_in)

        # Add welcome email to database queue (replaces Celery system)
        try:
            email_data = EmailQueueCreate(
                user_email=user.email,
                user_name=user.name,
                email_type=EmailType.welcome
            )
            email_queue_entry = add_email_to_queue(db, email_data)

            # Also add future campaign emails for this new user
            campaign_emails = add_campaign_emails_for_user(db, user.email, user.name)

            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f"Welcome email queued for {user.email} "
                f"(Queue ID: {email_queue_entry.id}, scheduled: {email_queue_entry.scheduled_time})"
            )
            logger.info(f"Added {len(campaign_emails)} future campaign emails for {user.email}")

        except Exception as email_error:
            import logging
            logging.getLogger(__name__).warning(f"Failed to queue emails: {email_error}")
            # Note: Emails will be processed by the email_processor.py daemon

        # Update metrics
        inc_user_signup()

        return UserResponse(
            user_id=user.id,
            name=user.name,
            email=user.email,
            created_at=user.created_at,
            total_points=user.total_points,
            shares_count=user.shares_count,
            default_rank=user.default_rank,
            current_rank=user.current_rank,
            is_admin=user.is_admin
        )

    except Exception as e:
        # Log the error and return a generic message
        import logging
        logging.getLogger(__name__).error(f"User creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )

@router.get("/registration-stats")
def get_registration_stats():
    """Get current registration system statistics."""
    return registration_manager.get_system_stats()

@router.get("/registration-status/{request_id}")
def get_registration_status(request_id: str):
    """Get the status of a specific registration request."""
    status_info = registration_manager.get_request_status(request_id)
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration request not found"
        )
    return status_info

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return access token.

    Args:
        user_in: User login credentials
        db: Database session

    Returns:
        Token: JWT access token with expiration info

    Raises:
        HTTPException: If credentials are invalid or user is inactive
    """
    try:
        # Authenticate user
        user = authenticate_user(db, user_in.email, user_in.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )

        # Generate JWT token
        token = create_jwt_for_user(user)

        return Token(
            access_token=token,
            token_type="bearer",
            expires_in=3600
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors
        import logging
        logging.getLogger(__name__).error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable"
        )

@router.get("/me", response_model=UserResponse)
def get_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get current authenticated user information.

    Args:
        token: JWT access token
        db: Database session

    Returns:
        UserResponse: Current user information

    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # Verify and decode token
        payload = verify_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Get user from database
        user = get_user_by_email(db, payload["email"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account not found"
            )

        # Check if user is still active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )

        return UserResponse(
            user_id=user.id,
            name=user.name,
            email=user.email,
            created_at=user.created_at,
            total_points=user.total_points,
            shares_count=user.shares_count,
            default_rank=user.default_rank,
            current_rank=user.current_rank,
            is_admin=user.is_admin
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors
        import logging
        logging.getLogger(__name__).error(f"Get user info failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve user information"
        )