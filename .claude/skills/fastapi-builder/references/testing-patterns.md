# FastAPI Testing Patterns

Official testing patterns using TestClient, pytest, and TDD workflow.

## Overview

FastAPI provides `TestClient` for testing APIs without running an actual server. Tests are synchronous even if endpoints are async. Follow Test-Driven Development (TDD) for quality code.

## Installation

```bash
# Using uv (recommended)
uv add --dev pytest pytest-asyncio pytest-cov httpx

# Traditional
# requirements-dev.txt
# pytest
# pytest-asyncio
# httpx         # Required by TestClient
# pytest-cov    # Coverage reporting
```

## TDD Workflow (Red-Green-Refactor)

### The TDD Cycle

**1. Red**: Write a failing test first

```python
# tests/test_users.py
def test_create_user(client):
    """Test creating a new user"""
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "username": "test", "password": "password123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
```

Run: `uv run pytest` - Test fails ❌ (endpoint doesn't exist)

**2. Green**: Write minimal code to make it pass

```python
# app/api/v1/endpoints/users.py
@router.post("/", status_code=201)
def create_user(user: UserCreate, session: SessionDep) -> dict:
    """Create new user"""
    db_user = crud_user.create_user(session, user)
    return {"id": db_user.id, "email": db_user.email, "username": db_user.username}
```

Run: `uv run pytest` - Test passes ✅

**3. Refactor**: Improve code quality

```python
# Refactor: Add error handling, validation, better structure
@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, session: SessionDep) -> dict:
    """Create new user"""
    # Check if user exists
    existing = crud_user.get_user_by_email(session, user.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    db_user = crud_user.create_user(session, user)
    return {"id": db_user.id, "email": db_user.email, "username": db_user.username}
```

Run: `uv run pytest` - Test still passes ✅

### TDD Benefits

- **Confidence**: Tests written before code ensure requirements are met
- **Better design**: Writing tests first leads to cleaner, more testable code
- **Documentation**: Tests serve as living documentation
- **Regression prevention**: Catch bugs early when refactoring

## Basic Testing Setup

### Test Client

```python
# tests/test_main.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_read_item():
    """Test item endpoint with path parameter."""
    response = client.get("/items/42")
    assert response.status_code == 200
    assert response.json() == {"item_id": 42, "q": None}

def test_read_item_with_query():
    """Test with query parameters."""
    response = client.get("/items/42?q=test")
    assert response.status_code == 200
    data = response.json()
    assert data["item_id"] == 42
    assert data["q"] == "test"
```

### POST Requests

```python
def test_create_item():
    """Test POST endpoint."""
    response = client.post(
        "/items/",
        json={"name": "Test Item", "price": 10.99, "description": "A test item"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["price"] == 10.99
    assert "id" in data

def test_create_item_invalid():
    """Test validation error."""
    response = client.post(
        "/items/",
        json={"name": "Test Item"},  # Missing required 'price'
    )
    assert response.status_code == 422  # Validation error
```

### Headers and Authentication

```python
def test_protected_endpoint():
    """Test endpoint requiring authentication."""
    # Without token
    response = client.get("/users/me")
    assert response.status_code == 401

    # With token
    token = "valid-token-here"
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
```

## Pytest Fixtures (conftest.py Organization)

### Reusable Fixtures with SQLModel

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from app.main import app
from app.db.session import get_db

DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="function")
def session():
    """Create test database session with automatic cleanup"""
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    # Create all tables
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    # Drop all tables after test
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def client(session: Session):
    """Create test client with database override"""
    def get_session_override():
        return session

    app.dependency_overrides[get_db] = get_session_override

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(client):
    """Get authentication headers for protected endpoints"""
    # Create test user
    client.post(
        "/users/",
        json={"email": "test@example.com", "username": "test", "password": "password123"}
    )

    # Login
    response = client.post(
        "/token",
        data={"username": "test", "password": "password123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_user(client):
    """Create a test user"""
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "username": "test", "password": "password123"}
    )
    return response.json()
```

### conftest.py Best Practices

1. **Scope**: Use `function` scope for database fixtures to ensure isolation
2. **Cleanup**: Always clean up resources (drop tables, clear overrides)
3. **Reusability**: Create fixtures for common test data (users, auth headers)
4. **Naming**: Use descriptive names (`session`, `client`, `auth_headers`)
5. **Organization**: Keep conftest.py in tests/ directory for all tests to access

### Using Fixtures

```python
# tests/test_users.py
def test_create_user(client):
    """Test user creation."""
    response = client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_get_current_user(client, auth_headers):
    """Test getting current user with authentication."""
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "username" in data
```

## Testing Database Operations

### Test CRUD Operations

```python
# tests/test_crud.py
from app.crud import user as crud_user
from app.schemas.user import UserCreate

def test_create_user_crud(db_session):
    """Test creating user via CRUD."""
    user_in = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123",
    )
    user = crud_user.create_user(db_session, user_in)
    assert user.email == "test@example.com"
    assert user.id is not None

def test_get_user_by_email(db_session):
    """Test retrieving user by email."""
    # Create user
    user_in = UserCreate(email="test@example.com", username="test", password="pass")
    created_user = crud_user.create_user(db_session, user_in)

    # Retrieve user
    retrieved_user = crud_user.get_user_by_email(db_session, "test@example.com")
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id

def test_update_user(db_session):
    """Test updating user."""
    # Create user
    user_in = UserCreate(email="test@example.com", username="test", password="pass")
    user = crud_user.create_user(db_session, user_in)

    # Update user
    user_update = UserUpdate(full_name="Test User")
    updated_user = crud_user.update_user(db_session, user.id, user_update)
    assert updated_user.full_name == "Test User"
```

### Test Data Factories

```python
# tests/factories.py
from app.models.user import User
from app.core.security import get_password_hash

def create_test_user(db_session, **kwargs):
    """Factory for creating test users."""
    defaults = {
        "email": "test@example.com",
        "username": "testuser",
        "hashed_password": get_password_hash("password123"),
        "full_name": "Test User",
        "is_active": True,
    }
    defaults.update(kwargs)
    user = User(**defaults)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

# Use in tests
def test_with_user(db_session):
    user = create_test_user(db_session, email="custom@example.com")
    assert user.email == "custom@example.com"
```

## Testing Authentication

### Login Flow

```python
def test_login_success(client):
    """Test successful login."""
    # Create user first
    client.post(
        "/users/",
        json={"email": "test@example.com", "username": "test", "password": "password123"},
    )

    # Login
    response = client.post(
        "/token",
        data={"username": "test", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    """Test login with wrong password."""
    response = client.post(
        "/token",
        data={"username": "test", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "detail" in response.json()

def test_access_protected_endpoint(client):
    """Test accessing protected endpoint with token."""
    # Get token
    login_response = client.post(
        "/token",
        data={"username": "test", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    # Access protected endpoint
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "test"
```

### OAuth2 Scopes

```python
def test_scopes_required(client, auth_headers):
    """Test endpoint requiring specific scopes."""
    # Token without required scope
    response = client.get("/users/me/items", headers=auth_headers)
    assert response.status_code == 401  # Insufficient permissions

def test_scopes_granted(client):
    """Test with required scopes."""
    # Login with scopes
    response = client.post(
        "/token",
        data={"username": "test", "password": "pass", "scope": "me items"},
    )
    token = response.json()["access_token"]

    # Access with proper scopes
    response = client.get(
        "/users/me/items",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
```

## Testing Error Handling

### Validation Errors

```python
def test_validation_error(client):
    """Test Pydantic validation."""
    response = client.post(
        "/items/",
        json={"name": "x", "price": -10},  # Invalid: name too short, negative price
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert len(errors) >= 2  # At least 2 validation errors

def test_not_found(client):
    """Test 404 error."""
    response = client.get("/items/999999")
    assert response.status_code == 404
    assert "detail" in response.json()
```

### Custom Exceptions

```python
def test_custom_exception(client):
    """Test custom exception handler."""
    response = client.get("/trigger-custom-error")
    assert response.status_code == 418  # Custom status code
    assert response.json()["message"] == "Custom error message"
```

## Testing File Uploads

```python
def test_upload_file(client):
    """Test file upload endpoint."""
    files = {"file": ("test.txt", b"test content", "text/plain")}
    response = client.post("/uploadfile/", files=files)
    assert response.status_code == 200
    assert response.json()["filename"] == "test.txt"

def test_upload_invalid_file_type(client):
    """Test uploading invalid file type."""
    files = {"file": ("test.exe", b"malicious", "application/x-msdownload")}
    response = client.post("/uploadfile/", files=files)
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]
```

## Testing Background Tasks

```python
from unittest.mock import patch

def test_background_task(client):
    """Test that background task is triggered."""
    with patch("app.api.endpoints.send_email") as mock_send:
        response = client.post(
            "/send-notification/",
            json={"email": "test@example.com", "message": "Hello"},
        )
        assert response.status_code == 200
        mock_send.assert_called_once()
```

## Testing WebSockets

```python
def test_websocket():
    """Test WebSocket connection."""
    with client.websocket_connect("/ws") as websocket:
        # Send data
        websocket.send_json({"message": "Hello"})

        # Receive data
        data = websocket.receive_json()
        assert data["message"] == "Hello"
```

## Coverage and Reporting

### Run Tests with Coverage

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Generate HTML coverage report
pytest --cov=app --cov-report=html tests/

# Run specific test file
pytest tests/test_users.py

# Run specific test
pytest tests/test_users.py::test_create_user

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x
```

### pytest.ini Configuration

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
```

## Mocking External Dependencies

### Mock Database

```python
from unittest.mock import MagicMock

def test_with_mock_db():
    """Test with mocked database."""
    mock_db = MagicMock()
    mock_db.query().filter().first.return_value = User(id=1, username="test")

    # Override dependency
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/users/1")
    assert response.status_code == 200
    mock_db.query.assert_called_once()
```

### Mock External API

```python
from unittest.mock import patch
import httpx

@patch("httpx.AsyncClient.get")
def test_external_api_call(mock_get, client):
    """Test endpoint that calls external API."""
    mock_get.return_value.json.return_value = {"data": "external"}
    mock_get.return_value.status_code = 200

    response = client.get("/fetch-external")
    assert response.status_code == 200
    assert response.json()["data"] == "external"
```

## Async Testing

For truly async tests (not common with TestClient):

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_async_endpoint():
    """Test async endpoint with AsyncClient."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
```

## Test Organization

```
tests/
├── conftest.py           # Shared fixtures
├── factories.py          # Test data factories
├── test_api/
│   ├── test_users.py     # User endpoints
│   ├── test_items.py     # Item endpoints
│   └── test_auth.py      # Authentication
├── test_crud/
│   ├── test_user.py      # User CRUD operations
│   └── test_item.py      # Item CRUD operations
├── test_core/
│   ├── test_security.py  # Security utilities
│   └── test_config.py    # Configuration
└── test_services/
    └── test_email.py     # Business logic
```

## Best Practices

### Test Naming

```python
# ✅ Good: Descriptive test names
def test_create_user_with_valid_data_returns_201():
    pass

def test_create_user_with_duplicate_email_returns_400():
    pass

# ❌ Bad: Vague test names
def test_user():
    pass

def test_api():
    pass
```

### Arrange-Act-Assert Pattern

```python
def test_create_user(client):
    # Arrange: Setup test data
    user_data = {
        "email": "test@example.com",
        "username": "test",
        "password": "password123",
    }

    # Act: Perform action
    response = client.post("/users/", json=user_data)

    # Assert: Verify results
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "id" in data
```

### Independent Tests

```python
# ✅ Good: Each test is independent
def test_create_user(client):
    response = client.post("/users/", json={...})
    assert response.status_code == 201

def test_get_user(client):
    # Create user in this test
    client.post("/users/", json={...})
    response = client.get("/users/1")
    assert response.status_code == 200

# ❌ Bad: Tests depend on each other
def test_create_user(client):
    response = client.post("/users/", json={...})
    return response.json()["id"]  # Don't do this

def test_get_user(client):
    user_id = test_create_user(client)  # Depends on other test
    response = client.get(f"/users/{user_id}")
```

### Use Fixtures for Common Setup

```python
# ✅ Good: Fixture for common setup
@pytest.fixture
def sample_user(client):
    response = client.post("/users/", json={...})
    return response.json()

def test_update_user(client, sample_user):
    response = client.put(f"/users/{sample_user['id']}", json={...})
    assert response.status_code == 200
```

## Testing Checklist

- [ ] Test all endpoint methods (GET, POST, PUT, DELETE, PATCH)
- [ ] Test happy path scenarios
- [ ] Test error scenarios (404, 400, 422, 500)
- [ ] Test authentication and authorization
- [ ] Test validation errors
- [ ] Test database operations (CRUD)
- [ ] Test with different user roles/permissions
- [ ] Mock external dependencies
- [ ] Test file uploads (if applicable)
- [ ] Test pagination
- [ ] Achieve >80% code coverage
- [ ] Use descriptive test names
- [ ] Keep tests independent
- [ ] Use fixtures for common setup
- [ ] Test edge cases

## References

- [FastAPI Testing Documentation](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pytest Documentation](https://docs.pytest.org/)
- [TestClient Documentation](https://www.starlette.io/testclient/)
