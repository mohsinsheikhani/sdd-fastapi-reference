from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from src.core.security import hash_password, hash_token
from src.models import RefreshToken, User
from src.services.token_service import create_access_token


def create_test_user(session: Session) -> User:
    """Helper to create a test user."""
    user = User(
        name="Test User",
        email="test@example.com",
        password_hash=hash_password("securepassword123"),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_refresh_token(session: Session, user: User, raw_token: str) -> str:
    """Helper to create a refresh token. Returns the raw token."""
    token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(UTC) + timedelta(days=7),
        revoked=False,
    )
    session.add(token)
    session.commit()
    return raw_token


def test_logout_valid(client: TestClient, session: Session) -> None:
    """T056: Valid logout returns 200 with message."""
    user = create_test_user(session)
    access_token, _ = create_access_token(user.id)
    refresh_token = create_refresh_token(session, user, "test_refresh_token")

    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_logout_revoked_token_rejected_on_reuse(
    client: TestClient, session: Session
) -> None:
    """T057: Revoked token is rejected on subsequent refresh attempt."""
    user = create_test_user(session)
    access_token, _ = create_access_token(user.id)
    refresh_token = create_refresh_token(session, user, "test_refresh_token")

    # Logout
    client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token},
    )

    # Try to use the revoked refresh token
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "AUTH_TOKEN_REVOKED"


def test_logout_requires_auth(client: TestClient, session: Session) -> None:
    """Logout without auth token returns 401."""
    user = create_test_user(session)
    refresh_token = create_refresh_token(session, user, "test_refresh_token")

    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 401
