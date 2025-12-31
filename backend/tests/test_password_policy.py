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
from password_policy import validate_password


def test_password_too_short():
    """Test password that is too short"""
    is_valid, error = validate_password("short", "testuser", "test@example.com")
    assert not is_valid
    assert "minimum length" in error.lower() or "too short" in error.lower()


def test_password_too_long():
    """Test password that is too long"""
    long_password = "a" * 129
    is_valid, error = validate_password(long_password, "testuser", "test@example.com")
    assert not is_valid
    assert "maximum length" in error.lower() or "too long" in error.lower()


def test_password_contains_username():
    """Test password that contains username"""
    is_valid, error = validate_password("testuser123!", "testuser", "test@example.com")
    assert not is_valid
    assert "username" in error.lower()


def test_password_contains_email():
    """Test password that contains email"""
    is_valid, error = validate_password("test@example.com123!", "testuser", "test@example.com")
    assert not is_valid
    assert "email" in error.lower()


def test_password_valid():
    """Test valid password"""
    is_valid, error = validate_password("ValidPassword123!@#", "testuser", "test@example.com")
    assert is_valid
    assert error is None

