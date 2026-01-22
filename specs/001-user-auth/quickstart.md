# Quickstart: User Authentication

**Feature**: 001-user-auth | **Date**: 2026-01-22

This guide provides step-by-step instructions to set up, run, and test the user authentication feature.

## Prerequisites

- Python 3.12+
- UV package manager
- PostgreSQL 14+ (or Neon serverless)
- Git

## Project Setup

### 1. Initialize Project with UV

```bash
# Initialize UV project (if not already done)
uv init .

# Or if project exists, sync dependencies
uv sync
```

### 2. Install Dependencies

The project uses these core dependencies:

```bash
# Add production dependencies
uv add fastapi uvicorn sqlmodel psycopg2-binary python-jose argon2-cffi pydantic-settings

# Add development dependencies
uv add --dev pytest pytest-asyncio httpx mypy ruff coverage
```

### 3. Configure Environment

Create a `.env` file in the project root:

```bash
# .env
DATABASE_URL=postgresql://user:password@localhost:5432/taskapi
SECRET_KEY=your-super-secret-key-min-32-chars-long
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Security Notes**:
- Generate `SECRET_KEY` with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Never commit `.env` to version control
- Add `.env` to `.gitignore`

### 4. Database Setup

#### Option A: Local PostgreSQL

```bash
# Create database
createdb taskapi

# Run migrations (using SQLModel's create_all for initial setup)
uv run python -c "from src.database import init_db; init_db()"
```

#### Option B: Neon Serverless

1. Create a project at [neon.tech](https://neon.tech)
2. Copy the connection string to `.env`
3. Run migrations as above

### 5. Run Development Server

```bash
# Start the server
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Server will be available at:
# - API: http://localhost:8000/api/v1
# - Docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

---

## API Usage Examples

### Register a New User

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepassword123"
  }'
```

**Response (201 Created)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2026-01-22T12:00:00Z"
}
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepassword123"
  }'
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

### Refresh Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4..."
  }'
```

### Logout

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4..."
  }'
```

### Request Password Reset

```bash
curl -X POST http://localhost:8000/api/v1/auth/password-reset/request \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com"
  }'
```

**Note**: The reset token is logged to the console (check server output).

### Confirm Password Reset

```bash
curl -X POST http://localhost:8000/api/v1/auth/password-reset/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "token": "<token-from-console>",
    "new_password": "newsecurepassword456"
  }'
```

### Delete Account

```bash
curl -X DELETE http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "securepassword123"
  }'
```

---

## Running Tests

### Run All Tests

```bash
# Run all tests with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run only unit tests
uv run pytest tests/unit/

# Run only integration tests
uv run pytest tests/integration/

# Run with verbose output
uv run pytest -v
```

### Test Configuration

Tests use an isolated SQLite database by default. For PostgreSQL integration tests:

```bash
# Set test database URL
export TEST_DATABASE_URL=postgresql://user:password@localhost:5432/taskapi_test

# Run integration tests
uv run pytest tests/integration/ -v
```

### Code Quality Checks

```bash
# Type checking
uv run mypy src/

# Linting and formatting
uv run ruff check src/
uv run ruff format src/

# Run all checks
uv run mypy src/ && uv run ruff check src/ && uv run pytest
```

---

## Project Structure

After implementation, the project should look like:

```
sdd-fastapi-reference/
├── .env                          # Environment variables (not in git)
├── .gitignore
├── pyproject.toml                # UV project configuration
├── uv.lock                       # UV lock file
├── src/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Settings from environment
│   ├── database.py               # Database connection
│   ├── models/                   # SQLModel database models
│   ├── schemas/                  # Pydantic request/response schemas
│   ├── services/                 # Business logic
│   ├── api/                      # Route handlers
│   ├── middleware/               # Rate limiting
│   └── core/                     # Security utilities, exceptions
├── tests/
│   ├── conftest.py               # Shared test fixtures
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
└── specs/
    └── 001-user-auth/            # Feature documentation
        ├── spec.md
        ├── plan.md
        ├── research.md
        ├── data-model.md
        ├── quickstart.md
        └── contracts/
            └── auth-api.yaml
```

---

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
```
sqlalchemy.exc.OperationalError: could not connect to server
```
- Check PostgreSQL is running
- Verify `DATABASE_URL` in `.env`
- Ensure database exists: `createdb taskapi`

**2. Module Not Found**
```
ModuleNotFoundError: No module named 'src'
```
- Run from project root directory
- Ensure `__init__.py` files exist in all packages

**3. JWT Secret Key Error**
```
JWTError: Invalid signature
```
- Ensure `SECRET_KEY` is set in `.env`
- Use the same key across restarts

**4. Rate Limit Errors in Tests**
```
429 Too Many Requests
```
- Tests may trigger rate limiting
- Reset rate limiter between tests in fixtures

---

## TDD Workflow

Follow this process for each feature task:

1. **Read acceptance scenario** from `spec.md`
2. **Write failing test** based on scenario
3. **Run test** to confirm it fails: `uv run pytest tests/integration/test_<feature>.py -v`
4. **Implement minimum code** to pass the test
5. **Run test again** to confirm it passes
6. **Refactor** if needed while keeping tests green
7. **Repeat** for next acceptance scenario

Example for registration:

```python
# tests/integration/test_registration.py
def test_register_valid_user(client):
    """Acceptance scenario 1.1: Valid registration returns 201 with user data."""
    response = client.post("/api/v1/users", json={
        "name": "John Doe",
        "email": "john@example.com",
        "password": "securepassword123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert "id" in data
    assert "created_at" in data
```

---

## Next Steps

After setup, proceed with:

1. Run `/sp.tasks` to generate implementation tasks
2. Start with infrastructure tasks (config, database)
3. Implement models and schemas
4. Implement services with unit tests
5. Implement routes with integration tests
6. Verify all acceptance criteria pass
