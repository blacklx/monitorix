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
import pytest
from input_validation import (
    sanitize_string,
    validate_url,
    validate_email,
    validate_username,
    validate_port
)


def test_sanitize_string():
    """Test string sanitization"""
    assert sanitize_string("  test  ") == "test"
    assert sanitize_string("<script>alert('xss')</script>") == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
    assert sanitize_string("normal text") == "normal text"


def test_validate_url_valid():
    """Test valid URL validation"""
    assert validate_url("https://example.com") == (True, None)
    assert validate_url("https://192.168.1.1:8006") == (True, None)


def test_validate_url_invalid():
    """Test invalid URL validation"""
    is_valid, error = validate_url("http://example.com")
    assert not is_valid
    assert "https" in error.lower()
    
    is_valid, error = validate_url("not-a-url")
    assert not is_valid


def test_validate_email_valid():
    """Test valid email validation"""
    assert validate_email("test@example.com") == (True, None)
    assert validate_email("user.name+tag@example.co.uk") == (True, None)


def test_validate_email_invalid():
    """Test invalid email validation"""
    is_valid, error = validate_email("not-an-email")
    assert not is_valid
    
    is_valid, error = validate_email("test@")
    assert not is_valid


def test_validate_username_valid():
    """Test valid username validation"""
    assert validate_username("testuser") == (True, None)
    assert validate_username("user123") == (True, None)


def test_validate_username_invalid():
    """Test invalid username validation"""
    is_valid, error = validate_username("ab")
    assert not is_valid
    
    is_valid, error = validate_username("a" * 51)
    assert not is_valid


def test_validate_port_valid():
    """Test valid port validation"""
    assert validate_port(80) == (True, None)
    assert validate_port(443) == (True, None)
    assert validate_port(8000) == (True, None)


def test_validate_port_invalid():
    """Test invalid port validation"""
    is_valid, error = validate_port(0)
    assert not is_valid
    
    is_valid, error = validate_port(65536)
    assert not is_valid

