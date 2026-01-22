from datetime import UTC, datetime, timedelta
from io import StringIO
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from src.core.security import hash_password, hash_token
from src.models import PasswordResetToken, RefreshToken, User


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


def create_password_reset_token(
    session: Session,
    user: User,
    raw_token: str = "reset_token_123",
    expired: bool = False,
    used: bool = False,
) -> str:
    """Helper to create a password reset token."""
    expires_at = datetime.now(UTC) + timedelta(hours=1)
    if expired:
        expires_at = datetime.now(UTC) - timedelta(hours=1)

    token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=expires_at,
        used=used,
    )
    session.add(token)
    session.commit()
    return raw_token


def test_password_reset_request_success(client: TestClient, session: Session) -> None:
    """T063: Password reset request returns 202."""
    create_test_user(session)

    with patch("sys.stdout", new_callable=StringIO):
        response = client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "test@example.com"},
        )
    assert response.status_code == 202
    data = response.json()
    assert "message" in data


def test_password_reset_request_unknown_email(
    client: TestClient, session: Session
) -> None:
    """T064: Same response for unknown email to prevent enumeration."""
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "nonexistent@example.com"},
    )
    assert response.status_code == 202
    data = response.json()
    assert "message" in data


def test_password_reset_confirm_success(client: TestClient, session: Session) -> None:
    """T065: Valid reset confirmation returns 200."""
    user = create_test_user(session)
    raw_token = create_password_reset_token(session, user)

    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "newpassword456"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

    # Verify can login with new password
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "newpassword456"},
    )
    assert login_response.status_code == 200


def test_password_reset_confirm_expired_token(
    client: TestClient, session: Session
) -> None:
    """T066: Expired reset token returns 400."""
    user = create_test_user(session)
    raw_token = create_password_reset_token(session, user, expired=True)

    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "newpassword456"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "RESET_TOKEN_INVALID"


def test_password_reset_confirm_used_token(
    client: TestClient, session: Session
) -> None:
    """T067: Already-used reset token returns 400."""
    user = create_test_user(session)
    raw_token = create_password_reset_token(session, user, used=True)

    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "newpassword456"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "RESET_TOKEN_INVALID"


def test_password_reset_revokes_all_refresh_tokens(
    client: TestClient, session: Session
) -> None:
    """T068: All refresh tokens are revoked on password change."""
    user = create_test_user(session)
    raw_reset_token = create_password_reset_token(session, user)

    # Create a refresh token
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token("refresh_token_123"),
        expires_at=datetime.now(UTC) + timedelta(days=7),
        revoked=False,
    )
    session.add(refresh_token)
    session.commit()

    # Reset password
    client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_reset_token, "new_password": "newpassword456"},
    )

    # Check refresh token is revoked
    session.refresh(refresh_token)
    assert refresh_token.revoked is True


def test_password_reset_confirm_invalid_token(
    client: TestClient, session: Session
) -> None:
    """Invalid reset token returns 400."""
    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": "nonexistent_token", "new_password": "newpassword456"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "RESET_TOKEN_INVALID"
