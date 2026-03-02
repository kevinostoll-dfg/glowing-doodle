"""Authentication utilities and FastAPI dependencies."""

import hashlib
import secrets

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.models.user import User


def hash_api_key(api_key: str) -> str:
    """Hash an API key using SHA-256."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a new random API key."""
    return f"ciq_{secrets.token_urlsafe(32)}"


def get_current_user(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency that validates the API key and returns the current user."""
    hashed = hash_api_key(x_api_key)
    user = db.query(User).filter(User.api_key == hashed).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return user
