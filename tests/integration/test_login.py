from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from src.core.security import hash_password
from src.models import User


def create_test_user(
    session: Session,
    email: str = "test@example.com",
    password: str = "securepassword123",
    name: str = "Test User",
) -> User:
    """Helper to create a test user."""
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_login_valid_credentials(client: TestClient, session: Session) -> None:
    """T029: Valid login returns 200 with tokens."""
    create_test_user(session)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"
    assert "expires_in" in data


def test_login_invalid_credentials(client: TestClient, session: Session) -> None:
    """T030: Invalid credentials returns 401."""
    create_test_user(session)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "AUTH_INVALID_CREDENTIALS"


def test_login_account_lockout(client: TestClient, session: Session) -> None:
    """T031: Account locks after 5 failed attempts."""
    from src.middleware.rate_limit import rate_limiter

    create_test_user(session)

    # Make 5 failed attempts (reset rate limiter to test lockout, not rate limit)
    for _ in range(5):
        rate_limiter.reset()
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
        )

    # 6th attempt should return locked
    rate_limiter.reset()
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 403
    data = response.json()
    assert data["code"] == "AUTH_ACCOUNT_LOCKED"


def test_login_auto_unlock_after_15_minutes(
    client: TestClient, session: Session
) -> None:
    """T032: Account unlocks after 15 minutes."""
    user = create_test_user(session)

    # Lock the account by setting locked_until in the past
    user.failed_login_attempts = 5
    user.locked_until = datetime.now(UTC) - timedelta(minutes=1)
    session.add(user)
    session.commit()

    # Should be able to login now
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 200


def test_login_case_insensitive_email(client: TestClient, session: Session) -> None:
    """T033: Email comparison is case-insensitive."""
    create_test_user(session, email="test@example.com")

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "TEST@EXAMPLE.COM",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 200


def test_login_failed_counter_reset_on_success(
    client: TestClient, session: Session
) -> None:
    """T034: Failed counter resets on successful login."""
    user = create_test_user(session)

    # Make 3 failed attempts
    for _ in range(3):
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
        )

    # Successful login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 200

    # Refresh user from DB
    session.refresh(user)
    assert user.failed_login_attempts == 0


def test_login_all_tokens_revoked_on_lockout(
    client: TestClient, session: Session
) -> None:
    """T035: All refresh tokens are revoked when account is locked."""
    from src.models import RefreshToken

    user = create_test_user(session)

    # Create a refresh token
    token = RefreshToken(
        user_id=user.id,
        token_hash="some_hash",
        expires_at=datetime.now(UTC) + timedelta(days=7),
        revoked=False,
    )
    session.add(token)
    session.commit()

    # Make 5 failed login attempts to lock account
    for _ in range(5):
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
        )

    # Check that the token is now revoked
    session.refresh(token)
    assert token.revoked is True


def test_login_nonexistent_user(client: TestClient, session: Session) -> None:
    """Login with nonexistent email returns 401 (not 404 to prevent enumeration)."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "somepassword123",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "AUTH_INVALID_CREDENTIALS"
