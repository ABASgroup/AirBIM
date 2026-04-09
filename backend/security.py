"""Security related features."""
import uuid
import hashlib
import base64
from secrets import token_urlsafe
from jose import jwt
from pwdlib import PasswordHash
from configs import api_config
from datetime import datetime, timedelta, timezone


# password hashing context
password_context = PasswordHash.recommended()


def create_access_token(user_id: uuid.UUID, data: dict | None = None) -> str:
    """
    Generates a JWT access token.

    Uses user ID for sub claim.

    Uses settings stated in the API config.
    """
    to_encode = data.copy() if data else {}
    expire = datetime.now(timezone.utc) + \
        timedelta(minutes=api_config.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "sub": str(user_id)})
    encoded_jwt = jwt.encode(to_encode,
                             key=api_config.JWT_SECRET_KEY,
                             algorithm=api_config.JWT_ALGORITHM)
    return encoded_jwt


def verify_password(password: str, hashed_password: str) -> bool:
    """Checks if password matches hashed password."""
    return password_context.verify_and_update(password, hashed_password)[0]


def get_password_hash(password: str) -> str:
    """Hashes password."""
    return password_context.hash(password)


def generate_link_token(byte_length: int = 32) -> str:
    """Generates URL-friendly token for link."""
    return token_urlsafe(byte_length)


def hash_link_token(token: str) -> str:
    """Hashes link token"""
    hash_object = hashlib.sha256(token.encode())
    token_hash = base64.urlsafe_b64encode(hash_object.digest()).decode()
    return token_hash
