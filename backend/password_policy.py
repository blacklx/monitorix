"""
Password policy validation utilities
"""
import re
from typing import List, Optional, Tuple
from exceptions import ValidationError


class PasswordPolicy:
    """
    Configurable password policy validator.
    
    Requirements:
    - Minimum length (default: 8)
    - Maximum length (default: 128)
    - Require uppercase letters
    - Require lowercase letters
    - Require digits
    - Require special characters (optional)
    - Check against common passwords
    - Check against username/email
    """
    
    # Common weak passwords to reject
    COMMON_PASSWORDS = [
        "password", "12345678", "123456789", "1234567890",
        "qwerty", "abc123", "monkey", "1234567", "letmein",
        "trustno1", "dragon", "baseball", "iloveyou", "master",
        "sunshine", "ashley", "bailey", "passw0rd", "shadow",
        "123123", "654321", "superman", "qazwsx", "michael",
        "football", "welcome", "jesus", "ninja", "mustang",
        "password1", "admin", "root", "monitorix"
    ]
    
    def __init__(
        self,
        min_length: int = 8,
        max_length: int = 128,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digits: bool = True,
        require_special: bool = False,
        check_common: bool = True
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
        self.check_common = check_common
    
    def validate(
        self,
        password: str,
        username: Optional[str] = None,
        email: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate password against policy.
        
        Args:
            password: Password to validate
            username: Username (to check if password contains it)
            email: Email (to check if password contains it)
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check length
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        
        if len(password) > self.max_length:
            errors.append(f"Password must be no more than {self.max_length} characters long")
        
        # Check for uppercase
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check for lowercase
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check for digits
        if self.require_digits and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        # Check for special characters
        if self.require_special and not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>/?]', password):
            errors.append("Password must contain at least one special character")
        
        # Check against common passwords
        if self.check_common:
            password_lower = password.lower()
            for common in self.COMMON_PASSWORDS:
                if common.lower() in password_lower or password_lower in common.lower():
                    errors.append("Password is too common or weak")
                    break
        
        # Check against username
        if username and username.lower() in password.lower():
            errors.append("Password cannot contain your username")
        
        # Check against email (before @)
        if email:
            email_local = email.split('@')[0].lower()
            if email_local and email_local in password.lower():
                errors.append("Password cannot contain your email address")
        
        # Check for repeated characters (e.g., "aaaa" or "1111")
        if re.search(r'(.)\1{3,}', password):
            errors.append("Password cannot contain the same character repeated 4 or more times")
        
        return len(errors) == 0, errors
    
    def get_requirements(self) -> List[str]:
        """Get list of password requirements for display"""
        requirements = []
        
        requirements.append(f"Between {self.min_length} and {self.max_length} characters")
        
        if self.require_uppercase:
            requirements.append("At least one uppercase letter (A-Z)")
        
        if self.require_lowercase:
            requirements.append("At least one lowercase letter (a-z)")
        
        if self.require_digits:
            requirements.append("At least one digit (0-9)")
        
        if self.require_special:
            requirements.append("At least one special character (!@#$%^&*...)")
        
        return requirements


# Default password policy instance
default_policy = PasswordPolicy(
    min_length=8,
    max_length=128,
    require_uppercase=True,
    require_lowercase=True,
    require_digits=True,
    require_special=False,  # Optional for better UX
    check_common=True
)


def validate_password(
    password: str,
    username: Optional[str] = None,
    email: Optional[str] = None,
    policy: Optional[PasswordPolicy] = None
) -> Tuple[bool, List[str]]:
    """
    Validate password using the default or provided policy.
    
    Args:
        password: Password to validate
        username: Username (optional)
        email: Email (optional)
        policy: PasswordPolicy instance (uses default if not provided)
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    if policy is None:
        policy = default_policy
    
    return policy.validate(password, username, email)


def get_password_requirements(policy: Optional[PasswordPolicy] = None) -> List[str]:
    """
    Get list of password requirements for display.
    
    Args:
        policy: PasswordPolicy instance (uses default if not provided)
    
    Returns:
        List of requirement strings
    """
    if policy is None:
        policy = default_policy
    
    return policy.get_requirements()

