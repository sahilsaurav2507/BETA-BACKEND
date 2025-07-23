"""
Global error handlers and middleware for the Lawvriksh application.
Provides consistent error responses and logging.
"""

import logging
import traceback
from typing import Union
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import time

logger = logging.getLogger(__name__)

class ErrorResponse:
    """Standardized error response format."""
    
    def __init__(self, 
                 error_code: str,
                 message: str,
                 details: Union[str, dict] = None,
                 status_code: int = 500):
        self.error_code = error_code
        self.message = message
        self.details = details
        self.status_code = status_code
        self.timestamp = time.time()
    
    def to_dict(self):
        response = {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "timestamp": self.timestamp
            }
        }
        if self.details:
            response["error"]["details"] = self.details
        return response

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    
    error_response = ErrorResponse(
        error_code=f"HTTP_{exc.status_code}",
        message=exc.detail,
        status_code=exc.status_code
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict(),
        headers=getattr(exc, 'headers', None)
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(f"Validation error: {exc.errors()} - {request.url}")
    
    # Format validation errors for better readability
    formatted_errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    error_response = ErrorResponse(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details={"validation_errors": formatted_errors},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.to_dict()
    )

async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database-related errors."""
    logger.error(f"Database error: {str(exc)} - {request.url}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Handle specific database errors
    if isinstance(exc, IntegrityError):
        error_response = ErrorResponse(
            error_code="DATABASE_INTEGRITY_ERROR",
            message="Data integrity constraint violation",
            details="The operation violates database constraints",
            status_code=status.HTTP_409_CONFLICT
        )
        status_code = status.HTTP_409_CONFLICT
    else:
        error_response = ErrorResponse(
            error_code="DATABASE_ERROR",
            message="Database operation failed",
            details="An error occurred while processing your request",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.to_dict()
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)} - {request.url}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    error_response = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        details="Please try again later or contact support if the problem persists",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.to_dict()
    )

# Custom exception classes
class BusinessLogicError(Exception):
    """Raised when business logic validation fails."""
    
    def __init__(self, message: str, error_code: str = "BUSINESS_LOGIC_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class AuthenticationError(Exception):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(self.message)

class AuthorizationError(Exception):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Access denied"):
        self.message = message
        super().__init__(self.message)

class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        self.message = message
        super().__init__(self.message)

async def business_logic_exception_handler(request: Request, exc: BusinessLogicError):
    """Handle business logic errors."""
    logger.warning(f"Business logic error: {exc.message} - {request.url}")
    
    error_response = ErrorResponse(
        error_code=exc.error_code,
        message=exc.message,
        status_code=status.HTTP_400_BAD_REQUEST
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response.to_dict()
    )

async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors."""
    logger.warning(f"Authentication error: {exc.message} - {request.url}")
    
    error_response = ErrorResponse(
        error_code="AUTHENTICATION_ERROR",
        message=exc.message,
        status_code=status.HTTP_401_UNAUTHORIZED
    )
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=error_response.to_dict(),
        headers={"WWW-Authenticate": "Bearer"}
    )

async def authorization_exception_handler(request: Request, exc: AuthorizationError):
    """Handle authorization errors."""
    logger.warning(f"Authorization error: {exc.message} - {request.url}")
    
    error_response = ErrorResponse(
        error_code="AUTHORIZATION_ERROR",
        message=exc.message,
        status_code=status.HTTP_403_FORBIDDEN
    )
    
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=error_response.to_dict()
    )

async def rate_limit_exception_handler(request: Request, exc: RateLimitError):
    """Handle rate limit errors."""
    logger.warning(f"Rate limit error: {exc.message} - {request.url}")
    
    error_response = ErrorResponse(
        error_code="RATE_LIMIT_ERROR",
        message=exc.message,
        status_code=status.HTTP_429_TOO_MANY_REQUESTS
    )
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error_response.to_dict(),
        headers={"Retry-After": "60"}
    )

def setup_error_handlers(app):
    """Set up all error handlers for the FastAPI application."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(BusinessLogicError, business_logic_exception_handler)
    app.add_exception_handler(AuthenticationError, authentication_exception_handler)
    app.add_exception_handler(AuthorizationError, authorization_exception_handler)
    app.add_exception_handler(RateLimitError, rate_limit_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Error handlers configured successfully")
