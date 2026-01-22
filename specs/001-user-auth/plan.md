# Implementation Plan: User Authentication

**Branch**: `001-user-auth` | **Date**: 2026-01-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-user-auth/spec.md`

## Summary

User authentication system for a task management API. Implements email/password registration, JWT-based authentication with refresh token rotation, account lockout protection, password reset (console-logged tokens), and account deletion with cascade. Uses Argon2id for password hashing, opaque database-backed refresh tokens, and rate limiting on auth endpoints.

## Technical Context

**Language/Version**: Python 3.12+ (using `|` union syntax for type hints)
**Primary Dependencies**: FastAPI, SQLModel, Pydantic v2, python-jose (JWT), argon2-cffi, uvicorn
**Storage**: PostgreSQL (Neon-compatible), SQLModel ORM
**Testing**: pytest, pytest-asyncio, httpx (for async test client)
**Target Platform**: Linux server (containerized deployment)
**Project Type**: Single project (backend API only)
**Performance Goals**: Login/token operations < 2 seconds p95, registration < 30 seconds total
**Constraints**: Rate limiting 5 req/min/IP on auth endpoints, account lockout after 5 failures
**Scale/Scope**: Single-tenant, minimal user volume (learning project)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **1. Purpose/Scope** | PASS | Feature aligns with Task API scope (user authentication for task management) |
| **2.I Correctness Over Convenience** | PASS | Spec defines deterministic behavior for all scenarios |
| **2.II Explicit Over Implicit** | PASS | All behaviors documented in spec, no implicit side effects |
| **2.III Strong Typing** | PASS | Will use Pydantic v2 schemas, Python 3.12+ type hints |
| **2.IV Separation of Concerns** | PASS | Will implement service layer, repository layer, route handlers |
| **2.V Explicit Contracts** | PASS | Spec defines all inputs, outputs, error codes |
| **3. Layer Structure** | PASS | Routes call services, services use repositories |
| **4. SDD Workflow** | PASS | Following spec -> plan -> tasks workflow |
| **5. API Design Standards** | PASS | RESTful endpoints under `/api/v1`, versioned |
| **6. Data/Persistence** | PASS | PostgreSQL + SQLModel, UUIDs, timestamps |
| **7. Typing/Validation** | PASS | Pydantic v2 with separate Create/Update/Read schemas |
| **8. Error Handling** | PASS | Structured JSON errors with codes from spec |
| **9. Testing/Quality** | PASS | Unit + integration tests planned, TDD workflow |
| **10. Tooling** | PASS | UV for packages, pytest for tests, mypy for types |

**Gate Status**: PASS - No violations identified

### Post-Design Re-evaluation (Phase 1 Complete)

| Artifact | Compliance Check | Status |
|----------|------------------|--------|
| `data-model.md` | Models have UUID PKs, timestamps, user_id FKs | PASS |
| `data-model.md` | Pydantic schemas separate Create/Read/Update | PASS |
| `data-model.md` | Cascade delete configured for user relationships | PASS |
| `contracts/auth-api.yaml` | OpenAPI 3.1 with explicit schemas | PASS |
| `contracts/auth-api.yaml` | All error codes defined in responses | PASS |
| `contracts/auth-api.yaml` | Versioned under `/api/v1` | PASS |
| `research.md` | All NEEDS CLARIFICATION items resolved | PASS |
| `quickstart.md` | TDD workflow documented | PASS |

**Post-Design Gate Status**: PASS - All artifacts comply with constitution

## Project Structure

### Documentation (this feature)

```text
specs/001-user-auth/
├── plan.md              # This file
├── research.md          # Phase 0 output (technology decisions)
├── data-model.md        # Phase 1 output (entity definitions)
├── quickstart.md        # Phase 1 output (setup guide)
├── contracts/           # Phase 1 output (OpenAPI specs)
│   └── auth-api.yaml    # Authentication API contract
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── main.py                    # FastAPI app entry point
├── config.py                  # Settings and configuration
├── database.py                # Database connection and session
├── models/
│   ├── __init__.py
│   ├── user.py               # User model
│   └── token.py              # RefreshToken, PasswordResetToken models
├── schemas/
│   ├── __init__.py
│   ├── user.py               # UserCreate, UserRead schemas
│   ├── auth.py               # LoginRequest, TokenResponse schemas
│   └── error.py              # ErrorResponse schema
├── services/
│   ├── __init__.py
│   ├── auth_service.py       # Authentication business logic
│   ├── user_service.py       # User management logic
│   ├── token_service.py      # JWT and refresh token logic
│   └── password_service.py   # Password hashing and reset logic
├── api/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── router.py         # Aggregates all v1 routes
│   │   ├── auth.py           # Auth endpoints (login, logout, refresh)
│   │   └── users.py          # User endpoints (register, delete)
│   └── deps.py               # Dependency injection (db session, current_user)
├── middleware/
│   ├── __init__.py
│   └── rate_limit.py         # Rate limiting middleware
└── core/
    ├── __init__.py
    ├── security.py           # Password hashing, token generation
    └── exceptions.py         # Custom exception classes

tests/
├── __init__.py
├── conftest.py               # Shared fixtures (test db, client, users)
├── unit/
│   ├── __init__.py
│   ├── test_auth_service.py
│   ├── test_user_service.py
│   ├── test_token_service.py
│   └── test_password_service.py
└── integration/
    ├── __init__.py
    ├── test_registration.py
    ├── test_login.py
    ├── test_token_refresh.py
    ├── test_logout.py
    ├── test_password_reset.py
    └── test_account_deletion.py
```

**Structure Decision**: Single project structure selected. Backend API only (no frontend). Follows constitution's layer separation: `api/` (routes), `services/` (business logic), `models/` (data access). Tests organized by type (unit/integration) per constitution Section 9.

## Complexity Tracking

No constitution violations requiring justification. The design follows all principles without exceptions.

## Key Architecture Decisions

### 1. Token Storage Strategy

**Decision**: Database-backed refresh tokens with hashed storage

**Options Considered**:
- A) Store refresh tokens in memory (Redis)
- B) Store refresh tokens in database with hashing
- C) Use stateless refresh tokens (JWT)

**Rationale for B**:
- Learning project doesn't need Redis complexity
- Database-backed tokens enable revocation (required for logout, lockout)
- Hashing prevents token theft from database access
- Stateless JWT refresh tokens can't be revoked per spec requirements

### 2. Password Hashing

**Decision**: Argon2id via argon2-cffi library

**Rationale**:
- Spec explicitly requires Argon2id (FR-005)
- argon2-cffi provides OWASP-recommended defaults
- Winner of Password Hashing Competition, memory-hard

### 3. JWT Implementation

**Decision**: python-jose with HS256 signing

**Options Considered**:
- A) python-jose (mature, widely used)
- B) PyJWT (simpler API)
- C) authlib (full OAuth support)

**Rationale for A**:
- Battle-tested in FastAPI ecosystem
- HS256 sufficient for single-service deployment
- Includes all needed claims handling

### 4. Rate Limiting

**Decision**: Custom middleware with in-memory tracking (per spec ownership)

**Rationale**:
- Spec states rate limiting is "shared middleware (not auth-specific logic)"
- Simple in-memory tracking sufficient for learning project
- 5 requests/minute/IP is low enough that memory isn't a concern

### 5. Functional Approach

**Decision**: Service functions over classes where appropriate

**Rationale**:
- User requested "simple, functional approach where it makes sense"
- Services will be modules with pure functions taking explicit dependencies
- Avoids unnecessary OOP ceremony for stateless operations

## Testing Strategy

### Unit Tests

| Service | Test Cases |
|---------|------------|
| `auth_service` | Login success, invalid credentials, locked account, case-insensitive email |
| `user_service` | Create user, duplicate email, name validation, delete user, cascade verification |
| `token_service` | Generate JWT, validate JWT, expired JWT, revoke refresh token, token rotation |
| `password_service` | Hash password, verify password, generate reset token, validate reset token |

### Integration Tests

| Endpoint | Test Cases (from acceptance scenarios) |
|----------|----------------------------------------|
| `POST /auth/register` | Valid registration (201), duplicate email (409), invalid password (422), invalid name (422) |
| `POST /auth/login` | Valid login (200), invalid credentials (401), locked account (403), case-insensitive email |
| `POST /auth/refresh` | Valid refresh (200), expired token (401), revoked token (401), already rotated (401) |
| `POST /auth/logout` | Valid logout (200), verify token revoked |
| `POST /auth/password-reset/request` | Request sent (202), same response for unknown email |
| `POST /auth/password-reset/confirm` | Valid reset (200), expired token (400), used token (400) |
| `DELETE /users/me` | Valid deletion (204), wrong password (401), verify cascade |

### TDD Workflow

1. Write failing test from acceptance scenario
2. Implement minimum code to pass
3. Refactor while keeping tests green
4. Repeat for each acceptance criterion

## Error Handling Strategy

All errors follow the spec's Error Codes table:

```python
# Example error response structure
{
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "Invalid email or password"
}
```

### Exception Mapping

| Exception Type | HTTP Status | Error Code |
|---------------|-------------|------------|
| `ValidationError` (Pydantic) | 422 | `VALIDATION_ERROR` |
| `UserExistsError` | 409 | `USER_EMAIL_EXISTS` |
| `UserNotFoundError` | 404 | `USER_NOT_FOUND` |
| `InvalidCredentialsError` | 401 | `AUTH_INVALID_CREDENTIALS` |
| `AccountLockedError` | 403 | `AUTH_ACCOUNT_LOCKED` |
| `TokenExpiredError` | 401 | `AUTH_TOKEN_EXPIRED` |
| `TokenInvalidError` | 401 | `AUTH_TOKEN_INVALID` |
| `TokenRevokedError` | 401 | `AUTH_TOKEN_REVOKED` |
| `ResetTokenInvalidError` | 400 | `RESET_TOKEN_INVALID` |
| `RateLimitError` | 429 | `RATE_LIMIT_EXCEEDED` |

## Dependencies

```toml
# pyproject.toml dependencies
[project]
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlmodel>=0.0.16",
    "psycopg2-binary>=2.9.9",  # PostgreSQL driver
    "python-jose[cryptography]>=3.3.0",  # JWT
    "argon2-cffi>=23.1.0",  # Password hashing
    "pydantic[email]>=2.5.0",  # Email validation
    "pydantic-settings>=2.1.0",  # Settings management
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.26.0",  # Test client
    "mypy>=1.8.0",
    "ruff>=0.2.0",
    "coverage>=7.4.0",
]
```

## Next Steps

1. Run `/sp.tasks` to generate detailed task breakdown
2. Initialize project with `uv init .`
3. Follow TDD: write tests first for each acceptance scenario
4. Implement services, then routes
5. Run integration tests against test database
