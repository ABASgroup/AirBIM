"""Unit tests for core security utilities, including JWT token creation, password hashing, and link token generation."""

import uuid
from datetime import datetime, timezone

from jose import jwt

from core.configs.api import api_config
from core.security import (
    create_access_token,
    generate_link_token,
    get_password_hash,
    hash_link_token,
    verify_password,
)


def test_create_access_token() -> None:
    """Test JWT token creation logic and claims."""
    user_id = uuid.uuid4()
    additional_data = {"role": "admin"}

    token = create_access_token(user_id=user_id, data=additional_data)
    assert isinstance(token, str)

    # decode the token to verify its contents
    decoded = jwt.decode(
        token, key=api_config.TOKEN_SECRET_KEY, algorithms=[api_config.JWT_ALGORITHM]
    )

    assert decoded["sub"] == str(user_id)
    assert decoded["role"] == "admin"
    assert "exp" in decoded

    # Check expiration time is in the future
    exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
    assert exp_time > datetime.now(timezone.utc)


def test_password_hashing() -> None:
    """Test generating a hash and verifying its correctness."""
    password = "super_secure_password"

    hashed_password = get_password_hash(password)
    assert hashed_password != password
    assert isinstance(hashed_password, str)

    # Correct password should pass
    is_valid = verify_password(password, hashed_password)
    assert is_valid is True

    # Incorrect password should fail
    is_invalid = verify_password("wrong_password", hashed_password)
    assert is_invalid is False


def test_generate_link_token() -> None:
    """Test generation of random URL-friendly tokens."""
    token = generate_link_token(byte_length=32)
    assert isinstance(token, str)
    # Safe base64 token length is larger than byte length
    assert len(token) > 32

    # Check uniqueness
    token2 = generate_link_token(byte_length=32)
    assert token != token2


def test_hash_link_token() -> None:
    """Test SHA-256 base64-encoded hashing for link tokens."""
    token = generate_link_token(byte_length=32)
    hashed = hash_link_token(token)

    assert isinstance(hashed, str)
    assert token != hashed
    assert len(hashed) > 0

    assert hashed == hash_link_token(token)
    assert hashed != hash_link_token(generate_link_token(byte_length=32))
