"""Authentication service for user login and account lockout handling."""

from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from src.core.exceptions import AccountLockedError, InvalidCredentialsError
from src.core.security import verify_password
from src.models.user import User
from src.services.token_service import revoke_all_user_tokens

LOCKOUT_DURATION = timedelta(minutes=15)
MAX_FAILED_ATTEMPTS = 5


def authenticate_user(session: Session, email: str, password: str) -> User:
    """Authenticate user with email and password. Handles lockout logic."""
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise InvalidCredentialsError()

    # Check if account is locked
    if is_account_locked(user):
        raise AccountLockedError()

    # Verify password
    if not verify_password(password, user.password_hash):
        record_failed_attempt(session, user)
        raise InvalidCredentialsError()

    # Successful login - reset failed attempts
    reset_failed_attempts(session, user)
    return user


def is_account_locked(user: User) -> bool:
    """Check if account is currently locked."""
    if user.failed_login_attempts < MAX_FAILED_ATTEMPTS:
        return False
    if user.locked_until is None:
        return False
    # Handle both timezone-aware and naive datetimes (SQLite stores naive)
    now = datetime.now(UTC)
    locked_until = user.locked_until
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=UTC)
    return now < locked_until


def record_failed_attempt(session: Session, user: User) -> None:
    """Record a failed login attempt and lock if threshold reached."""
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
        user.locked_until = datetime.now(UTC) + LOCKOUT_DURATION
        # Revoke all refresh tokens on lockout
        revoke_all_user_tokens(session, user.id)
    session.add(user)
    session.commit()


def reset_failed_attempts(session: Session, user: User) -> None:
    """Reset failed login attempts after successful login."""
    user.failed_login_attempts = 0
    user.locked_until = None
    session.add(user)
    session.commit()
