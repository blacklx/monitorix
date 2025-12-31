"""
API Rate Limiting
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from config import settings
import os

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/hour", "100/minute"]
)

# Get rate limits from environment or use defaults
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))

def get_rate_limit():
    """Get rate limit string from settings"""
    return [f"{RATE_LIMIT_PER_HOUR}/hour", f"{RATE_LIMIT_PER_MINUTE}/minute"]

