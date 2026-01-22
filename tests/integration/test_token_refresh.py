from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from src.core.security import hash_password, hash_token
from src.models import RefreshToken, User


def create_test_user(
    session: Session,
    email: str = "test@example.com",
    password: str = "securepassword123",
) -> User:
    """Helper to create a test user."""
    user = User(
        name="Test User",
        email=email,
        password_hash=hash_password(password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_refresh_token(
    session: Session,
    user: User,
    raw_token: str = "test_refresh_token",
    expired: bool = False,
    revoked: bool = False,
) -> str:
    """Helper to create a refresh token. Returns the raw token."""
    expires_at = datetime.now(UTC) + timedelta(days=7)
    if expired:
        expires_at = datetime.now(UTC) - timedelta(hours=1)

    token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=expires_at,
        revoked=revoked,
    )
    session.add(token)
    session.commit()
    return raw_token


def test_refresh_valid_token(client: TestClient, session: Session) -> None:
    """T046: Valid refresh returns 200 with new tokens and rotation."""
    user = create_test_user(session)
    raw_token = create_refresh_token(session, user)

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": raw_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"
    assert "expires_in" in data
    # New refresh token should be different
    assert data["refresh_token"] != raw_token


def test_refresh_expired_token(client: TestClient, session: Session) -> None:
    """T047: Expired refresh token returns 401."""
    user = create_test_user(session)
    raw_token = create_refresh_token(session, user, expired=True)

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": raw_token},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "AUTH_TOKEN_EXPIRED"


def test_refresh_revoked_token(client: TestClient, session: Session) -> None:
    """T048: Revoked refresh token returns 401."""
    user = create_test_user(session)
    raw_token = create_refresh_token(session, user, revoked=True)

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": raw_token},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "AUTH_TOKEN_REVOKED"


def test_refresh_already_rotated_token(client: TestClient, session: Session) -> None:
    """T049: Already-rotated token returns 401."""
    user = create_test_user(session)
    raw_token = create_refresh_token(session, user)

    # First refresh should succeed
    response1 = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": raw_token},
    )
    assert response1.status_code == 200

    # Second refresh with same token should fail (already rotated/revoked)
    response2 = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": raw_token},
    )
    assert response2.status_code == 401
    data = response2.json()
    assert data["code"] == "AUTH_TOKEN_REVOKED"


def test_refresh_locked_account(client: TestClient, session: Session) -> None:
    """T050: Locked account cannot refresh tokens."""
    user = create_test_user(session)
    raw_token = create_refresh_token(session, user)

    # Lock the account
    user.failed_login_attempts = 5
    user.locked_until = datetime.now(UTC) + timedelta(minutes=10)
    session.add(user)
    session.commit()

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": raw_token},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["code"] == "AUTH_ACCOUNT_LOCKED"


def test_refresh_invalid_token(client: TestClient, session: Session) -> None:
    """Invalid token that doesn't exist returns 401."""
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "nonexistent_token"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "AUTH_TOKEN_INVALID"
