# Research: User Authentication

**Feature**: 001-user-auth | **Date**: 2026-01-22

This document resolves all "NEEDS CLARIFICATION" items from the Technical Context and documents technology research findings.

## Technology Decisions

### 1. Password Hashing: Argon2id

**Decision**: Use `argon2-cffi` library with OWASP-recommended parameters

**Research Findings**:
- Argon2id is the winner of the Password Hashing Competition (2015)
- Combines Argon2i (side-channel resistant) and Argon2d (GPU-resistant)
- OWASP recommends: memory=19 MiB, iterations=2, parallelism=1
- `argon2-cffi` uses these defaults automatically

**Alternatives Considered**:
| Algorithm | Pros | Cons | Decision |
|-----------|------|------|----------|
| Argon2id | Memory-hard, PHC winner, OWASP recommended | Newer (less battle-tested than bcrypt) | **SELECTED** (spec mandates) |
| bcrypt | Battle-tested, widely supported | Not memory-hard, limited to 72 bytes | Rejected |
| scrypt | Memory-hard | Less flexible parameters | Rejected |

**Implementation Pattern**:
```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()  # Uses OWASP defaults

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(password: str, hash: str) -> bool:
    try:
        ph.verify(hash, password)
        return True
    except VerifyMismatchError:
        return False
```

---

### 2. JWT Library: python-jose

**Decision**: Use `python-jose[cryptography]` for JWT handling

**Research Findings**:
- Mature library, actively maintained
- Used in FastAPI official documentation and tutorials
- Supports all standard algorithms (HS256, RS256, ES256)
- `cryptography` backend is more secure than `pycryptodome`

**Alternatives Considered**:
| Library | Pros | Cons | Decision |
|---------|------|------|----------|
| python-jose | FastAPI ecosystem standard, full feature set | Larger dependency footprint | **SELECTED** |
| PyJWT | Simpler API, lighter | Less comprehensive | Rejected |
| authlib | Full OAuth support | Overkill for simple JWT | Rejected |

**Implementation Pattern**:
```python
from jose import jwt, JWTError
from datetime import datetime, timedelta, UTC

SECRET_KEY = "..."  # From environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

def create_access_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "exp": expire, "iat": datetime.now(UTC)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
```

---

### 3. Refresh Token Generation

**Decision**: Use `secrets.token_urlsafe(32)` for opaque refresh tokens

**Research Findings**:
- `secrets` module is cryptographically secure (uses OS entropy)
- 32 bytes = 256 bits of entropy (sufficient for token security)
- URL-safe encoding avoids issues in headers/URLs
- Token is hashed before storage using SHA-256

**Implementation Pattern**:
```python
import secrets
import hashlib

def generate_refresh_token() -> tuple[str, str]:
    """Returns (raw_token, hashed_token)."""
    raw_token = secrets.token_urlsafe(32)
    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, hashed_token

def hash_token(token: str) -> str:
    """Hash token for storage/lookup."""
    return hashlib.sha256(token.encode()).hexdigest()
```

---

### 4. Email Validation

**Decision**: Use Pydantic's `EmailStr` type with RFC 5322 validation

**Research Findings**:
- Pydantic v2's `EmailStr` requires `pydantic[email]` (includes `email-validator`)
- Validates against RFC 5322 specification
- Automatically normalizes to lowercase

**Implementation Pattern**:
```python
from pydantic import BaseModel, EmailStr, field_validator

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower()
```

---

### 5. Rate Limiting Strategy

**Decision**: Simple in-memory rate limiter with IP-based tracking

**Research Findings**:
- Spec requires 5 requests/minute/IP on auth endpoints only
- For learning project, in-memory is sufficient (no Redis needed)
- Sliding window algorithm provides smooth limiting
- Must handle `X-Forwarded-For` for proxied requests

**Alternatives Considered**:
| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| In-memory dict | Simple, no dependencies | Not distributed, lost on restart | **SELECTED** (learning project) |
| Redis | Distributed, persistent | Additional infrastructure | Rejected for scope |
| slowapi library | Ready-made FastAPI integration | Additional dependency | Rejected (simple enough to implement) |

**Implementation Pattern**:
```python
from collections import defaultdict
from time import time
from fastapi import Request, HTTPException

class RateLimiter:
    def __init__(self, requests: int = 5, window: int = 60):
        self.requests = requests
        self.window = window
        self.clients: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time()
        # Remove old timestamps
        self.clients[client_ip] = [
            t for t in self.clients[client_ip]
            if now - t < self.window
        ]
        if len(self.clients[client_ip]) >= self.requests:
            return False
        self.clients[client_ip].append(now)
        return True
```

---

### 6. Database Session Management

**Decision**: Use SQLModel's session with FastAPI dependency injection

**Research Findings**:
- SQLModel wraps SQLAlchemy's session management
- `yield` pattern ensures proper cleanup
- Constitution requires dependency injection for `Session`

**Implementation Pattern**:
```python
from collections.abc import Generator
from sqlmodel import Session, create_engine

engine = create_engine(DATABASE_URL)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
```

---

### 7. Account Lockout Implementation

**Decision**: Track failed attempts and lock timestamp in User model

**Research Findings**:
- Spec requires 5 consecutive failures → 15-minute lockout
- Counter resets on successful login
- Lockout blocks login and token refresh only
- All refresh tokens revoked on lockout

**Implementation Pattern**:
```python
from datetime import datetime, timedelta, UTC

LOCKOUT_DURATION = timedelta(minutes=15)
MAX_FAILED_ATTEMPTS = 5

def is_account_locked(user: User) -> bool:
    if user.failed_login_attempts < MAX_FAILED_ATTEMPTS:
        return False
    if user.locked_until is None:
        return False
    return datetime.now(UTC) < user.locked_until

def record_failed_attempt(user: User, session: Session) -> None:
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
        user.locked_until = datetime.now(UTC) + LOCKOUT_DURATION
        # Revoke all refresh tokens
        revoke_all_user_tokens(user.id, session)
    session.add(user)
    session.commit()

def reset_failed_attempts(user: User, session: Session) -> None:
    user.failed_login_attempts = 0
    user.locked_until = None
    session.add(user)
    session.commit()
```

---

### 8. Cascade Deletion Strategy

**Decision**: Use SQLModel relationship with `cascade="all, delete-orphan"`

**Research Findings**:
- Spec requires deleting User + all RefreshTokens + all Tasks
- SQLAlchemy/SQLModel supports cascade delete via relationship config
- Constitution Section 6 requires user-scoped data isolation

**Implementation Pattern**:
```python
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # ... other fields
    refresh_tokens: list["RefreshToken"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    tasks: list["Task"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
```

---

### 9. Testing Database Strategy

**Decision**: Use SQLite in-memory for unit tests, PostgreSQL container for integration

**Research Findings**:
- Unit tests should be fast and isolated
- SQLite works for most SQLModel operations
- Integration tests need PostgreSQL for full compatibility
- pytest fixtures handle setup/teardown

**Implementation Pattern**:
```python
# conftest.py
import pytest
from sqlmodel import SQLModel, Session, create_engine

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
```

---

## Best Practices Applied

### Security Best Practices

1. **Never log passwords or tokens** - Use structured logging that excludes sensitive fields
2. **Hash tokens before storage** - Prevents token theft from database access
3. **Use constant-time comparison** - Prevents timing attacks on token validation
4. **Validate JWT signature** - Prevents token tampering
5. **Separate access and refresh tokens** - Limits blast radius of token compromise

### FastAPI Best Practices

1. **Use Pydantic v2 syntax** - `model_config`, `field_validator`, `ConfigDict`
2. **Separate schemas from models** - Different concerns, different classes
3. **Use dependency injection** - For database sessions, current user
4. **Return explicit response models** - Never expose ORM models directly

### Testing Best Practices

1. **Test each acceptance scenario** - Direct mapping from spec to tests
2. **Use fixtures for common setup** - Test users, tokens, sessions
3. **Test error paths explicitly** - Each error code has a test
4. **Isolate tests** - No shared state between test functions

---

## Resolved Clarifications

| Item | Resolution |
|------|------------|
| Python version | 3.12+ with `\|` union syntax |
| Package manager | UV for dependency management |
| JWT library | python-jose with cryptography backend |
| Password hasher | argon2-cffi with OWASP defaults |
| Rate limiter | In-memory sliding window (not Redis) |
| Test database | SQLite in-memory for unit, PostgreSQL for integration |
| Token storage | SHA-256 hashed in database |
