from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_active_user
import httpx
import re
from typing import Optional

router = APIRouter(prefix="/api/version", tags=["version"])

# Current version - should match VERSION file
CURRENT_VERSION = "1.2.0"
GITHUB_REPO = "blacklx/monitorix"


@router.get("")
async def get_version():
    """
    Get current application version.
    
    Returns the current version of Monitorix running on this server.
    """
    return {
        "version": CURRENT_VERSION,
        "backend_version": CURRENT_VERSION,
        "frontend_version": CURRENT_VERSION
    }


@router.get("/check")
async def check_version(
    current_user = Depends(get_current_active_user)
):
    """
    Check if a newer version is available.
    
    Compares the current version with the latest release on GitHub.
    Returns information about available updates.
    
    **Note**: Requires authentication (admin recommended).
    """
    try:
        # Fetch latest release from GitHub API
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            
            if response.status_code == 404:
                # Repository not found or no releases
                return {
                    "current_version": CURRENT_VERSION,
                    "latest_version": None,
                    "update_available": False,
                    "error": "No releases found or repository not accessible"
                }
            
            response.raise_for_status()
            release_data = response.json()
            
            # Extract version from tag (remove 'v' prefix if present)
            latest_tag = release_data.get("tag_name", "")
            latest_version = re.sub(r'^v', '', latest_tag) if latest_tag else None
            
            if not latest_version:
                return {
                    "current_version": CURRENT_VERSION,
                    "latest_version": None,
                    "update_available": False,
                    "error": "Could not parse version from release tag"
                }
            
            # Compare versions
            update_available = _compare_versions(CURRENT_VERSION, latest_version) < 0
            
            return {
                "current_version": CURRENT_VERSION,
                "latest_version": latest_version,
                "update_available": update_available,
                "release_url": release_data.get("html_url"),
                "release_notes": release_data.get("body", ""),
                "published_at": release_data.get("published_at")
            }
            
    except httpx.TimeoutException:
        return {
            "current_version": CURRENT_VERSION,
            "latest_version": None,
            "update_available": False,
            "error": "Timeout while checking for updates"
        }
    except httpx.RequestError as e:
        return {
            "current_version": CURRENT_VERSION,
            "latest_version": None,
            "update_available": False,
            "error": f"Failed to check for updates: {str(e)}"
        }
    except Exception as e:
        return {
            "current_version": CURRENT_VERSION,
            "latest_version": None,
            "update_available": False,
            "error": f"Unexpected error: {str(e)}"
        }


def _compare_versions(v1: str, v2: str) -> int:
    """
    Compare two version strings.
    
    Returns:
    - Negative if v1 < v2
    - Zero if v1 == v2
    - Positive if v1 > v2
    """
    def version_tuple(v):
        # Split version string and convert to integers
        parts = []
        for part in v.split('.'):
            try:
                parts.append(int(part))
            except ValueError:
                # Handle non-numeric parts (e.g., "1.2.0-beta")
                parts.append(0)
        return tuple(parts)
    
    v1_tuple = version_tuple(v1)
    v2_tuple = version_tuple(v2)
    
    # Pad with zeros to same length
    max_len = max(len(v1_tuple), len(v2_tuple))
    v1_tuple = v1_tuple + (0,) * (max_len - len(v1_tuple))
    v2_tuple = v2_tuple + (0,) * (max_len - len(v2_tuple))
    
    if v1_tuple < v2_tuple:
        return -1
    elif v1_tuple > v2_tuple:
        return 1
    else:
        return 0

