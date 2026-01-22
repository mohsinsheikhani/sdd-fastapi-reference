import json
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session, select

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


def test_delete_account_valid(client: TestClient, session: Session) -> None:
    """T078: Valid account deletion returns 204."""
    user = create_test_user(session)
    access_token, _ = create_access_token(user.id)

    response = client.request(
        "DELETE",
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        content=json.dumps({"password": "securepassword123"}),
    )
    assert response.status_code == 204

    # Verify user is deleted
    deleted_user = session.exec(select(User).where(User.id == user.id)).first()
    assert deleted_user is None


def test_delete_account_wrong_password(client: TestClient, session: Session) -> None:
    """T079: Wrong password returns 401."""
    user = create_test_user(session)
    access_token, _ = create_access_token(user.id)

    response = client.request(
        "DELETE",
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        content=json.dumps({"password": "wrongpassword"}),
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "AUTH_INVALID_CREDENTIALS"


def test_delete_account_cascade_tokens(client: TestClient, session: Session) -> None:
    """T080: Cascade deletion removes all tokens."""
    user = create_test_user(session)
    access_token, _ = create_access_token(user.id)

    # Create a refresh token
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token("test_token"),
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    session.add(refresh_token)
    session.commit()
    token_id = refresh_token.id

    # Delete account
    response = client.request(
        "DELETE",
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        content=json.dumps({"password": "securepassword123"}),
    )
    assert response.status_code == 204

    # Verify token is deleted (cascade)
    deleted_token = session.exec(
        select(RefreshToken).where(RefreshToken.id == token_id)
    ).first()
    assert deleted_token is None


def test_delete_account_cannot_login(client: TestClient, session: Session) -> None:
    """T081: Deleted account cannot login."""
    user = create_test_user(session)
    access_token, _ = create_access_token(user.id)

    # Delete account
    client.request(
        "DELETE",
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        content=json.dumps({"password": "securepassword123"}),
    )

    # Try to login
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "securepassword123"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "AUTH_INVALID_CREDENTIALS"


def test_delete_account_requires_auth(client: TestClient, session: Session) -> None:
    """Delete without auth returns 401."""
    response = client.request(
        "DELETE",
        "/api/v1/users/me",
        headers={"Content-Type": "application/json"},
        content=json.dumps({"password": "securepassword123"}),
    )
    assert response.status_code == 401
