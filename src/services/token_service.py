"""Token service for JWT access tokens and refresh token management."""

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from jose import jwt
from sqlmodel import Session, select

from src.config import settings
from src.core.security import hash_token
from src.models.token import RefreshToken

ALGORITHM = "HS256"


def create_access_token(user_id: uuid.UUID) -> tuple[str, int]:
    """Create JWT access token. Returns (token, expires_in_seconds)."""
    expires_in = settings.access_token_expire_minutes * 60
    expire = datetime.now(UTC) + timedelta(seconds=expires_in)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    return token, expires_in


def generate_refresh_token(session: Session, user_id: uuid.UUID) -> str:
    """Generate opaque refresh token, store hashed in DB. Returns raw token."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)

    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    session.add(refresh_token)
    session.commit()

    return raw_token


def revoke_all_user_tokens(session: Session, user_id: uuid.UUID) -> None:
    """Revoke all refresh tokens for a user."""
    tokens = session.exec(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,  # noqa: E712
        )
    ).all()
    for token in tokens:
        token.revoked = True
        session.add(token)
    session.commit()


def validate_refresh_token(session: Session, raw_token: str) -> RefreshToken:
    """Validate refresh token. Returns the token record or raises exception."""
    from src.core.exceptions import (
        TokenExpiredError,
        TokenInvalidError,
        TokenRevokedError,
    )

    token_hash = hash_token(raw_token)
    token = session.exec(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    ).first()

    if not token:
        raise TokenInvalidError()

    if token.revoked:
        raise TokenRevokedError()

    # Handle timezone-naive datetimes from SQLite
    expires_at = token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if datetime.now(UTC) > expires_at:
        raise TokenExpiredError()

    return token


def rotate_refresh_token(session: Session, old_token: RefreshToken) -> str:
    """Invalidate old token and create new one. Returns new raw token."""
    old_token.revoked = True
    session.add(old_token)

    new_raw_token = generate_refresh_token(session, old_token.user_id)
    return new_raw_token


def revoke_refresh_token(session: Session, raw_token: str) -> None:
    """Revoke a specific refresh token."""
    from src.core.exceptions import TokenInvalidError

    token_hash = hash_token(raw_token)
    token = session.exec(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    ).first()

    if not token:
        raise TokenInvalidError()

    token.revoked = True
    session.add(token)
    session.commit()
