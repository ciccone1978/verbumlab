from datetime import datetime, timedelta, timezone
from typing import Any, Union
import bcrypt
import hashlib
from jose import jwt
from app.core.config import settings

ALGORITHM = settings.ALGORITHM

def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def _get_password_payload(password: str) -> bytes:
    """Pre-hash with SHA-256 to support passwords longer than 72 chars."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    payload = _get_password_payload(plain_password)
    return bcrypt.checkpw(payload, hashed_password.encode("utf-8"))

def get_password_hash(password: str) -> str:
    payload = _get_password_payload(password)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(payload, salt).decode("utf-8")
