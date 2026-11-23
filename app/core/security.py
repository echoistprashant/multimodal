"""Security and Authentication Core Module.

Provides JWT generation, signature verification, and password hashing primitives.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration constants
SECRET_KEY = "mdis-super-secret-development-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


class TokenPayload(BaseModel):
    """Standardized JWT payload schema."""

    sub: str = Field(..., description="User or subject identifier")
    tenant_id: str = Field(..., description="Tenant ID for multi-tenant isolation")
    role: str = Field(default="viewer", description="Role: viewer | editor | reviewer | admin")
    exp: datetime | None = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify raw password against bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Compute bcrypt hash of a password."""
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    tenant_id: str,
    role: str = "viewer",
    expires_delta: timedelta | None = None,
) -> str:
    """Create a cryptographically signed JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": subject,
        "tenant_id": tenant_id,
        "role": role,
        "exp": expire,
        "iat": now,
    }
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> TokenPayload | None:
    """Decode and validate a JWT access token, returning parsed payload or None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        return None
