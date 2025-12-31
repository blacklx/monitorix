"""
API Rate Limiting
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from config import settings

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/hour", "100/minute"]
)

# Get rate limits from settings
RATE_LIMIT_PER_HOUR = settings.rate_limit_per_hour
RATE_LIMIT_PER_MINUTE = settings.rate_limit_per_minute

def get_rate_limit():
    """Get rate limit string from settings"""
    return [f"{RATE_LIMIT_PER_HOUR}/hour", f"{RATE_LIMIT_PER_MINUTE}/minute"]

