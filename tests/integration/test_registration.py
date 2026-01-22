from fastapi.testclient import TestClient


def test_register_valid_user(client: TestClient) -> None:
    """T017: Valid registration returns 201 with user data."""
    response = client.post(
        "/api/v1/users",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email(client: TestClient) -> None:
    """T018: Duplicate email returns 409 USER_EMAIL_EXISTS."""
    client.post(
        "/api/v1/users",
        json={
            "name": "John Doe",
            "email": "duplicate@example.com",
            "password": "securepassword123",
        },
    )
    response = client.post(
        "/api/v1/users",
        json={
            "name": "Jane Doe",
            "email": "duplicate@example.com",
            "password": "anotherpassword123",
        },
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "USER_EMAIL_EXISTS"


def test_register_short_password(client: TestClient) -> None:
    """T019: Short password returns 422 VALIDATION_ERROR."""
    response = client.post(
        "/api/v1/users",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "short",
        },
    )
    assert response.status_code == 422


def test_register_invalid_name_empty(client: TestClient) -> None:
    """T020: Empty name returns 422."""
    response = client.post(
        "/api/v1/users",
        json={
            "name": "",
            "email": "john@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 422


def test_register_invalid_name_too_long(client: TestClient) -> None:
    """T020: Name over 100 chars returns 422."""
    response = client.post(
        "/api/v1/users",
        json={
            "name": "A" * 101,
            "email": "john@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 422


def test_register_invalid_name_special_chars(client: TestClient) -> None:
    """T020: Name with special characters returns 422."""
    response = client.post(
        "/api/v1/users",
        json={
            "name": "John123",
            "email": "john@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 422


def test_register_rate_limiting(client: TestClient) -> None:
    """T021: Rate limiting returns 429 after 5 requests/minute."""
    for i in range(5):
        client.post(
            "/api/v1/users",
            json={
                "name": "Test User",
                "email": f"test{i}@example.com",
                "password": "securepassword123",
            },
        )

    response = client.post(
        "/api/v1/users",
        json={
            "name": "Test User",
            "email": "test5@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 429
    data = response.json()
    assert data["code"] == "RATE_LIMIT_EXCEEDED"


def test_register_email_normalized_to_lowercase(client: TestClient) -> None:
    """Email should be normalized to lowercase."""
    response = client.post(
        "/api/v1/users",
        json={
            "name": "John Doe",
            "email": "JOHN@EXAMPLE.COM",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "john@example.com"
