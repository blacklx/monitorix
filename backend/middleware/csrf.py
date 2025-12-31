"""
Copyright 2024 Monitorix Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message
import secrets
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

# State-changing HTTP methods that require CSRF protection
PROTECTED_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

# Endpoints that should be exempt from CSRF protection
EXEMPT_PATHS = {
    "/api/auth/login",
    "/api/auth/refresh",
    "/api/auth/logout",
    "/api/auth/forgot-password",
    "/api/auth/reset-password",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}

# Cookie name for CSRF token
CSRF_TOKEN_COOKIE = "csrf_token"
CSRF_TOKEN_HEADER = "X-CSRF-Token"


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware
    
    Generates CSRF tokens and validates them for state-changing requests.
    Tokens are stored in HTTP-only cookies and must be sent in X-CSRF-Token header.
    """
    
    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
    
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF protection if disabled
        if not self.enabled:
            return await call_next(request)
        
        # Skip WebSocket connections
        if request.url.path.startswith("/ws"):
            return await call_next(request)
        
        # Check if path is exempt
        if any(request.url.path.startswith(path) for path in EXEMPT_PATHS):
            return await call_next(request)
        
        # For GET requests, generate and set CSRF token if not present
        if request.method == "GET":
            response = await call_next(request)
            
            # Check if CSRF token cookie exists
            csrf_token = request.cookies.get(CSRF_TOKEN_COOKIE)
            
            if not csrf_token:
                # Generate new CSRF token
                csrf_token = secrets.token_urlsafe(32)
                
                # Set token in cookie (HttpOnly, Secure in production, SameSite=Strict)
                # Check if we're in production (HTTPS) or development
                is_production = getattr(settings, 'environment', 'development').lower() == "production"
                response.set_cookie(
                    key=CSRF_TOKEN_COOKIE,
                    value=csrf_token,
                    httponly=True,
                    secure=is_production,
                    samesite="strict",
                    max_age=86400 * 7,  # 7 days
                    path="/"
                )
            
            return response
        
        # For state-changing methods, validate CSRF token
        if request.method in PROTECTED_METHODS:
            # Get token from cookie
            csrf_token_cookie = request.cookies.get(CSRF_TOKEN_COOKIE)
            
            # Get token from header
            csrf_token_header = request.headers.get(CSRF_TOKEN_HEADER)
            
            # Validate token
            if not csrf_token_cookie:
                logger.warning(f"CSRF token missing in cookie for {request.method} {request.url.path}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token missing. Please refresh the page and try again."
                )
            
            if not csrf_token_header:
                logger.warning(f"CSRF token missing in header for {request.method} {request.url.path}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token missing in request header. Please include X-CSRF-Token header."
                )
            
            if csrf_token_cookie != csrf_token_header:
                logger.warning(f"CSRF token mismatch for {request.method} {request.url.path}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token validation failed. Tokens do not match."
                )
        
        # Process request
        response = await call_next(request)
        
        # Ensure CSRF token cookie is set in response (in case it was missing)
        if not request.cookies.get(CSRF_TOKEN_COOKIE) and request.method == "GET":
            csrf_token = secrets.token_urlsafe(32)
            is_production = getattr(settings, 'environment', 'development').lower() == "production"
            response.set_cookie(
                key=CSRF_TOKEN_COOKIE,
                value=csrf_token,
                httponly=True,
                secure=is_production,
                samesite="strict",
                max_age=86400 * 7,  # 7 days
                path="/"
            )
        
        return response


def get_csrf_token(request: Request) -> Optional[str]:
    """
    Get CSRF token from request cookie.
    Useful for endpoints that need to return the token to frontend.
    """
    return request.cookies.get(CSRF_TOKEN_COOKIE)

