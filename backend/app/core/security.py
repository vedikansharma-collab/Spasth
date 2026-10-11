import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import bcrypt
import jwt
from app.core.config import settings

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt with automatic salting (12 rounds).
    Guarantees constant-time hashing and resistance to rainbow table/brute-force attacks.
    """
    if not password:
        raise ValueError("Password cannot be empty")
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a stored bcrypt hash in constant time.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception as e:
        logger.warning(f"Password verification encountered error: {e}")
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Generates a cryptographically signed JWT access token.
    Fails closed if JWT_SECRET_KEY is missing or weak.
    """
    secret = settings.validate_jwt_secret()
    
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({
        "iat": now,
        "exp": expire,
        "sub": str(data.get("sub", data.get("user_id", "")))
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        secret,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT token signature and expiration.
    Fails closed if signature is invalid or token has expired.
    """
    secret = settings.validate_jwt_secret()
    payload = jwt.decode(
        token,
        secret,
        algorithms=[settings.JWT_ALGORITHM]
    )
    return payload
