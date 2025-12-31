"""
Input validation and sanitization utilities
"""
import re
from typing import Optional
from urllib.parse import urlparse
import html


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize a string input by:
    - Stripping whitespace
    - Escaping HTML entities
    - Limiting length
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length (None for no limit)
    
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return ""
    
    # Strip whitespace
    sanitized = value.strip()
    
    # Escape HTML entities to prevent XSS
    sanitized = html.escape(sanitized)
    
    # Limit length
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_url(url: str, require_https: bool = False) -> tuple[bool, Optional[str]]:
    """
    Validate URL format and optionally require HTTPS.
    
    Args:
        url: URL to validate
        require_https: If True, only allow HTTPS URLs
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "URL is required"
    
    try:
        parsed = urlparse(url)
        
        # Check scheme
        if not parsed.scheme:
            return False, "URL must include a scheme (http:// or https://)"
        
        if parsed.scheme not in ["http", "https"]:
            return False, "URL scheme must be http:// or https://"
        
        if require_https and parsed.scheme != "https":
            return False, "HTTPS is required for this URL"
        
        # Check netloc (domain)
        if not parsed.netloc:
            return False, "URL must include a valid domain"
        
        # Check for valid domain format
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(domain_pattern, parsed.netloc.split(':')[0]):
            return False, "Invalid domain format"
        
        return True, None
    
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"


def validate_email(email: str) -> tuple[bool, Optional[str]]:
    """
    Validate email format.
    
    Args:
        email: Email to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Email is required"
    
    # Basic email regex (Pydantic's EmailStr does more thorough validation)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return False, "Invalid email format"
    
    # Check length
    if len(email) > 254:  # RFC 5321 limit
        return False, "Email address is too long"
    
    # Check local part length
    local_part = email.split('@')[0]
    if len(local_part) > 64:  # RFC 5321 limit
        return False, "Email local part is too long"
    
    return True, None


def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """
    Validate username format.
    
    Args:
        username: Username to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username or not isinstance(username, str):
        return False, "Username is required"
    
    # Check length
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 50:
        return False, "Username must be no more than 50 characters long"
    
    # Check format (alphanumeric, underscore, hyphen)
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    
    # Cannot start or end with underscore or hyphen
    if username.startswith(('_', '-')) or username.endswith(('_', '-')):
        return False, "Username cannot start or end with underscore or hyphen"
    
    return True, None


def validate_port(port: int) -> tuple[bool, Optional[str]]:
    """
    Validate port number.
    
    Args:
        port: Port number to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(port, int):
        return False, "Port must be a number"
    
    if port < 1 or port > 65535:
        return False, "Port must be between 1 and 65535"
    
    return True, None


def sanitize_html(html_content: str) -> str:
    """
    Sanitize HTML content by escaping special characters.
    This is a basic implementation. For production, consider using
    a library like bleach for more comprehensive sanitization.
    
    Args:
        html_content: HTML content to sanitize
    
    Returns:
        Sanitized HTML string
    """
    if not isinstance(html_content, str):
        return ""
    
    # Escape HTML entities
    return html.escape(html_content)


def validate_no_sql_injection(value: str) -> tuple[bool, Optional[str]]:
    """
    Basic check for SQL injection patterns.
    Note: This is a basic check. SQLAlchemy's parameterized queries
    provide the real protection, but this adds an extra layer.
    
    Args:
        value: String to check
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, str):
        return True, None
    
    # Common SQL injection patterns
    sql_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|\/\*|\*\/)",
        r"(\b(UNION|OR|AND)\s+\d+)",
        r"('|;|\\)",
    ]
    
    value_upper = value.upper()
    for pattern in sql_patterns:
        if re.search(pattern, value_upper, re.IGNORECASE):
            return False, "Invalid characters detected in input"
    
    return True, None


def validate_no_xss(value: str) -> tuple[bool, Optional[str]]:
    """
    Basic check for XSS patterns.
    Note: HTML escaping in sanitize_string provides the real protection,
    but this adds an extra validation layer.
    
    Args:
        value: String to check
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, str):
        return True, None
    
    # Common XSS patterns
    xss_patterns = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    for pattern in xss_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            return False, "Potentially dangerous content detected"
    
    return True, None


def validate_positive_number(value: float, max_value: Optional[float] = None) -> tuple[bool, Optional[str]]:
    """
    Validate that a number is positive and optionally within a maximum.
    
    Args:
        value: Number to validate
        max_value: Maximum allowed value (None for no limit)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, (int, float)):
        return False, "Value must be a number"
    
    if value < 0:
        return False, "Value must be positive"
    
    if max_value is not None and value > max_value:
        return False, f"Value must be no more than {max_value}"
    
    return True, None

