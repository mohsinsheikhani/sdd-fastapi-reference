"""Password reset service for token generation and password updates."""

import secrets
from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from src.core.exceptions import ResetTokenInvalidError
from src.core.security import hash_password, hash_token
from src.models.token import PasswordResetToken
from src.models.user import User
from src.services.token_service import revoke_all_user_tokens


def generate_password_reset_token(session: Session, email: str) -> str | None:
    """Generate password reset token for user. Returns raw token or None."""
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        return None

    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(UTC) + timedelta(hours=1)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    session.add(reset_token)
    session.commit()

    # Log token to console (learning project - no email)
    print(f"[PASSWORD RESET] Token for {email}: {raw_token}")

    return raw_token


def validate_reset_token(session: Session, raw_token: str) -> PasswordResetToken:
    """Validate password reset token. Returns token record or raises exception."""
    token_hash = hash_token(raw_token)
    token = session.exec(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    ).first()

    if not token:
        raise ResetTokenInvalidError()

    if token.used:
        raise ResetTokenInvalidError()

    # Handle timezone-naive datetimes from SQLite
    expires_at = token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if datetime.now(UTC) > expires_at:
        raise ResetTokenInvalidError()

    return token


def reset_password(session: Session, raw_token: str, new_password: str) -> None:
    """Reset password using token. Revokes all refresh tokens."""
    token = validate_reset_token(session, raw_token)

    # Update password
    user = token.user
    user.password_hash = hash_password(new_password)
    session.add(user)

    # Mark token as used
    token.used = True
    session.add(token)

    # Revoke all refresh tokens
    revoke_all_user_tokens(session, user.id)

    session.commit()
