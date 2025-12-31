"""
Custom exceptions and error handling utilities
"""
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import logging
import traceback

logger = logging.getLogger(__name__)

# Try to import Sentry (will be None if not initialized)
try:
    from sentry_config import capture_exception, set_user_context
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    capture_exception = None
    set_user_context = None


class MonitorixException(Exception):
    """Base exception for Monitorix-specific errors"""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(MonitorixException):
    """Raised when validation fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, details)


class NotFoundError(MonitorixException):
    """Raised when a resource is not found"""
    def __init__(self, resource_type: str, resource_id: Optional[Any] = None):
        message = f"{resource_type} not found"
        if resource_id is not None:
            message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class UnauthorizedError(MonitorixException):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(MonitorixException):
    """Raised when access is forbidden"""
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class ConflictError(MonitorixException):
    """Raised when a resource conflict occurs"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_409_CONFLICT, details)


class ServiceUnavailableError(MonitorixException):
    """Raised when a service is unavailable"""
    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE)


def create_error_response(
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    details: Optional[Dict[str, Any]] = None,
    error_code: Optional[str] = None
) -> JSONResponse:
    """
    Create a standardized error response
    
    Args:
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details
        error_code: Machine-readable error code
    
    Returns:
        JSONResponse with standardized error format
    """
    error_data = {
        "error": {
            "message": message,
            "status_code": status_code
        }
    }
    
    if error_code:
        error_data["error"]["code"] = error_code
    
    if details:
        error_data["error"]["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=error_data
    )


async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled exceptions
    
    Args:
        request: FastAPI request object
        exc: Exception that was raised
    
    Returns:
        JSONResponse with error details
    """
    # Log the full exception with traceback
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else "unknown"
        }
    )
    
    # Capture exception in Sentry (only for non-MonitorixException errors)
    # MonitorixException are expected errors, don't send to Sentry
    if SENTRY_AVAILABLE and capture_exception and not isinstance(exc, MonitorixException):
        try:
            # Extract user info from request if available
            user_id = None
            username = None
            if hasattr(request.state, "user"):
                user = request.state.user
                if hasattr(user, "id"):
                    user_id = user.id
                if hasattr(user, "username"):
                    username = user.username
            
            # Set user context
            if user_id or username:
                set_user_context(user_id=user_id, username=username)
            
            # Capture exception with additional context
            capture_exception(
                exc,
                tags={
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": getattr(exc, "status_code", None)
                },
                extra={
                    "url": str(request.url),
                    "client": request.client.host if request.client else "unknown",
                    "headers": dict(request.headers) if hasattr(request, "headers") else None
                }
            )
        except Exception as sentry_error:
            logger.warning(f"Failed to send exception to Sentry: {sentry_error}")
    
    # If it's a MonitorixException, use its status code and message
    if isinstance(exc, MonitorixException):
        return create_error_response(
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details
        )
    
    # If it's an HTTPException from FastAPI, preserve it
    if isinstance(exc, HTTPException):
        return create_error_response(
            message=exc.detail,
            status_code=exc.status_code
        )
    
    # For all other exceptions, return a generic error
    # In production, don't expose internal error details
    error_message = "An internal server error occurred"
    error_details = None
    
    # In development, include more details
    import os
    if os.getenv("ENVIRONMENT", "production").lower() == "development":
        error_message = f"Internal server error: {str(exc)}"
        error_details = {
            "type": type(exc).__name__,
            "traceback": traceback.format_exc()
        }
    
    return create_error_response(
        message=error_message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=error_details,
        error_code="INTERNAL_SERVER_ERROR"
    )


async def validation_exception_handler(request, exc) -> JSONResponse:
    """
    Handler for Pydantic validation errors
    
    Args:
        request: FastAPI request object
        exc: ValidationError from Pydantic
    
    Returns:
        JSONResponse with validation error details
    """
    errors = []
    if hasattr(exc, "errors"):
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error.get("loc", [])),
                "message": error.get("msg", "Validation error"),
                "type": error.get("type", "validation_error")
            })
    
    logger.warning(
        f"Validation error: {errors}",
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return create_error_response(
        message="Validation error",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": errors},
        error_code="VALIDATION_ERROR"
    )

