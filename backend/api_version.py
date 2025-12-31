"""
API versioning utilities
"""
from typing import Optional
from fastapi import Header, HTTPException, status
import re


# Current API version
CURRENT_API_VERSION = "v1"

# Supported API versions
SUPPORTED_VERSIONS = ["v1"]


def parse_api_version(version_str: Optional[str]) -> Optional[str]:
    """
    Parse API version from string.
    
    Args:
        version_str: Version string (e.g., "v1", "1", "v1.0")
    
    Returns:
        Normalized version string (e.g., "v1") or None if invalid
    """
    if not version_str:
        return None
    
    # Remove whitespace
    version_str = version_str.strip()
    
    # Handle different formats: "v1", "1", "v1.0", "1.0"
    # Normalize to "v1" format
    match = re.match(r'^v?(\d+)(?:\.\d+)?$', version_str, re.IGNORECASE)
    if match:
        major_version = match.group(1)
        return f"v{major_version}"
    
    return None


def get_api_version(
    accept: Optional[str] = Header(None, alias="Accept"),
    api_version: Optional[str] = Header(None, alias="X-API-Version")
) -> str:
    """
    Extract API version from request headers.
    
    Checks:
    1. X-API-Version header (e.g., "v1")
    2. Accept header (e.g., "application/json; version=v1")
    3. Defaults to current version if not specified
    
    Args:
        accept: Accept header value
        api_version: X-API-Version header value
    
    Returns:
        API version string (e.g., "v1")
    """
    # Check X-API-Version header first
    if api_version:
        parsed = parse_api_version(api_version)
        if parsed and parsed in SUPPORTED_VERSIONS:
            return parsed
        elif parsed:
            # Version specified but not supported
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported API version: {api_version}. Supported versions: {', '.join(SUPPORTED_VERSIONS)}"
            )
    
    # Check Accept header for version parameter
    if accept:
        # Look for version parameter in Accept header
        # Format: "application/json; version=v1"
        version_match = re.search(r'version\s*=\s*([^;,\s]+)', accept, re.IGNORECASE)
        if version_match:
            parsed = parse_api_version(version_match.group(1))
            if parsed and parsed in SUPPORTED_VERSIONS:
                return parsed
            elif parsed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported API version in Accept header. Supported versions: {', '.join(SUPPORTED_VERSIONS)}"
                )
    
    # Default to current version
    return CURRENT_API_VERSION


def validate_api_version(version: str) -> bool:
    """
    Validate that an API version is supported.
    
    Args:
        version: API version to validate
    
    Returns:
        True if version is supported, False otherwise
    """
    return version in SUPPORTED_VERSIONS


def get_versioned_prefix(version: str) -> str:
    """
    Get versioned API prefix for a given version.
    
    Args:
        version: API version (e.g., "v1")
    
    Returns:
        Versioned prefix (e.g., "/api/v1")
    """
    return f"/api/{version}"

