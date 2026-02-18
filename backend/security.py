"""Security related features."""
from jose import JWTError, jwt
from passlib.context import CryptContext
from config import api_config
from datetime import datetime, timedelta, timezone


# password hashing context
password_context = CryptContext(schemes=['bcrypt'])


def create_access_token(data: dict) -> str:
    """Generates a JWT access token with
    
    Uses settings stated in the API config
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + \
        timedelta(minutes=api_config.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(data,
                             key=api_config.JWT_SECRET_KEY,
                             algorithm=api_config.JWT_ALGORITHM)
    return encoded_jwt


def verify_password(password: str, hashed_password: str) -> bool:
    """Checks if password matches hashed password"""
    return password_context.verify_and_update(password, hashed_password)[0]


def get_password_hash(password: str) -> str:
    """Hashes password"""
    return password_context.hash(password)
