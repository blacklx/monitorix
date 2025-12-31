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
import pyotp
import qrcode
import io
import base64
import logging
from typing import Optional, Tuple
from config import settings

logger = logging.getLogger(__name__)


def generate_totp_secret() -> str:
    """
    Generate a new TOTP secret for a user.
    
    Returns:
        str: Base32-encoded TOTP secret
    """
    return pyotp.random_base32()


def get_totp_uri(secret: str, username: str, issuer: str = "Monitorix") -> str:
    """
    Generate TOTP URI for QR code generation.
    
    Args:
        secret: TOTP secret (base32)
        username: Username for the account
        issuer: Service name (default: "Monitorix")
    
    Returns:
        str: TOTP URI (otpauth://totp/...)
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=username,
        issuer_name=issuer
    )


def generate_qr_code(uri: str) -> str:
    """
    Generate QR code image as base64-encoded string.
    
    Args:
        uri: TOTP URI to encode in QR code
    
    Returns:
        str: Base64-encoded PNG image data (data:image/png;base64,...)
    """
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        raise


def verify_totp(secret: str, token: str) -> bool:
    """
    Verify a TOTP token against a secret.
    
    Args:
        secret: TOTP secret (base32)
        token: 6-digit TOTP token to verify
    
    Returns:
        bool: True if token is valid, False otherwise
    """
    try:
        totp = pyotp.TOTP(secret)
        # Allow a small window for clock skew (default is 1 interval = 30 seconds)
        return totp.verify(token, valid_window=1)
    except Exception as e:
        logger.error(f"Error verifying TOTP: {e}")
        return False


def setup_2fa(username: str) -> Tuple[str, str, str]:
    """
    Set up 2FA for a user.
    
    Args:
        username: Username for the account
    
    Returns:
        tuple: (secret, uri, qr_code_base64)
    """
    secret = generate_totp_secret()
    uri = get_totp_uri(secret, username)
    qr_code = generate_qr_code(uri)
    
    return secret, uri, qr_code

