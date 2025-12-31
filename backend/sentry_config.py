"""
Sentry configuration for error tracking and performance monitoring
"""
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

_sentry_initialized = False


def init_sentry():
    """
    Initialize Sentry SDK for error tracking.
    
    This should be called early in the application startup, before any other imports
    that might raise exceptions.
    """
    global _sentry_initialized
    
    if not settings.sentry_enabled:
        logger.info("Sentry error tracking is disabled")
        return
    
    if not settings.sentry_dsn:
        logger.warning("SENTRY_ENABLED is true but SENTRY_DSN is not set. Sentry will not be initialized.")
        return
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.asyncio import AsyncioIntegration
        
        # Configure Sentry
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.sentry_environment,
            traces_sample_rate=settings.sentry_traces_sample_rate,
            profiles_sample_rate=settings.sentry_profiles_sample_rate,
            enable_tracing=True,
            # Integrations
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                LoggingIntegration(
                    level=logging.INFO,  # Capture info and above as breadcrumbs
                    event_level=logging.ERROR  # Send errors as events
                ),
                AsyncioIntegration(),
            ],
            # Release tracking (can be set via environment variable)
            release=settings.sentry_environment,  # Can be overridden with SENTRY_RELEASE
            # Additional options
            send_default_pii=False,  # Don't send personally identifiable information
            max_breadcrumbs=50,  # Maximum number of breadcrumbs
            attach_stacktrace=True,  # Include stack traces
            # Server name for identifying the instance
            server_name=None,  # Can be set via SENTRY_SERVER_NAME
        )
        
        _sentry_initialized = True
        logger.info(
            f"Sentry initialized successfully",
            extra={
                "environment": settings.sentry_environment,
                "traces_sample_rate": settings.sentry_traces_sample_rate,
                "profiles_sample_rate": settings.sentry_profiles_sample_rate
            }
        )
        
    except ImportError:
        logger.error("sentry-sdk is not installed. Install it with: pip install sentry-sdk[fastapi]")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}", exc_info=True)


def capture_exception(exc: Exception, **kwargs):
    """
    Capture an exception in Sentry.
    
    Args:
        exc: Exception to capture
        **kwargs: Additional context (user, tags, extra, etc.)
    """
    if not _sentry_initialized:
        return
    
    try:
        import sentry_sdk
        sentry_sdk.capture_exception(exc, **kwargs)
    except Exception as e:
        logger.error(f"Failed to capture exception in Sentry: {e}")


def capture_message(message: str, level: str = "error", **kwargs):
    """
    Capture a message in Sentry.
    
    Args:
        message: Message to capture
        level: Log level (debug, info, warning, error, fatal)
        **kwargs: Additional context (user, tags, extra, etc.)
    """
    if not _sentry_initialized:
        return
    
    try:
        import sentry_sdk
        sentry_sdk.capture_message(message, level=level, **kwargs)
    except Exception as e:
        logger.error(f"Failed to capture message in Sentry: {e}")


def set_user_context(user_id: Optional[int] = None, username: Optional[str] = None, email: Optional[str] = None):
    """
    Set user context for Sentry events.
    
    Args:
        user_id: User ID
        username: Username
        email: User email
    """
    if not _sentry_initialized:
        return
    
    try:
        import sentry_sdk
        sentry_sdk.set_user({
            "id": str(user_id) if user_id else None,
            "username": username,
            "email": email
        })
    except Exception as e:
        logger.error(f"Failed to set user context in Sentry: {e}")


def clear_user_context():
    """Clear user context from Sentry."""
    if not _sentry_initialized:
        return
    
    try:
        import sentry_sdk
        sentry_sdk.set_user(None)
    except Exception as e:
        logger.error(f"Failed to clear user context in Sentry: {e}")

