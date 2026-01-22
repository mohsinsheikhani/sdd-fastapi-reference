# Data Model: User Authentication

**Feature**: 001-user-auth | **Date**: 2026-01-22

This document defines all database entities, their fields, relationships, validation rules, and state transitions for the user authentication feature.

## Entity Diagram

```
┌─────────────────────────────────────────────┐
│                    User                      │
├─────────────────────────────────────────────┤
│ id: UUID (PK)                               │
│ name: str [1-100 chars]                     │
│ email: str [unique, lowercase, max 254]     │
│ password_hash: str                          │
│ failed_login_attempts: int [default 0]      │
│ locked_until: datetime | None               │
│ created_at: datetime                        │
│ updated_at: datetime                        │
├─────────────────────────────────────────────┤
│ refresh_tokens: list[RefreshToken] (1:N)    │
│ password_reset_tokens: list[PasswordReset]  │
│ tasks: list[Task] (1:N) [future]            │
└─────────────────────────────────────────────┘
           │
           │ 1:N (cascade delete)
           ▼
┌─────────────────────────────────────────────┐
│              RefreshToken                    │
├─────────────────────────────────────────────┤
│ id: UUID (PK)                               │
│ user_id: UUID (FK → User.id)                │
│ token_hash: str [SHA-256 hash]              │
│ expires_at: datetime                        │
│ revoked: bool [default False]               │
│ created_at: datetime                        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│           PasswordResetToken                 │
├─────────────────────────────────────────────┤
│ id: UUID (PK)                               │
│ user_id: UUID (FK → User.id)                │
│ token_hash: str [SHA-256 hash]              │
│ expires_at: datetime                        │
│ used: bool [default False]                  │
│ created_at: datetime                        │
└─────────────────────────────────────────────┘
```

## Entity Definitions

### User

Primary entity representing a registered account holder.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `UUID` | PK, default uuid4 | Unique user identifier |
| `name` | `str` | 1-100 chars, letters and spaces only | User display name |
| `email` | `str` | unique, max 254 chars, lowercase | User email (login identifier) |
| `password_hash` | `str` | Argon2id hash | Hashed password |
| `failed_login_attempts` | `int` | default 0, >= 0 | Consecutive failed login count |
| `locked_until` | `datetime \| None` | nullable | Account unlock time (if locked) |
| `created_at` | `datetime` | auto-set UTC | Account creation timestamp |
| `updated_at` | `datetime` | auto-update UTC | Last modification timestamp |

**SQLModel Definition**:
```python
import uuid
from datetime import datetime, UTC
from sqlmodel import SQLModel, Field, Relationship
import re

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=254, unique=True, index=True)
    password_hash: str = Field(max_length=255)
    failed_login_attempts: int = Field(default=0, ge=0)
    locked_until: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)}
    )

    # Relationships
    refresh_tokens: list["RefreshToken"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    password_reset_tokens: list["PasswordResetToken"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
```

**Validation Rules**:
- Name: Must match pattern `^[a-zA-Z\s]+$` (letters and spaces only)
- Email: Must be valid RFC 5322 format, stored lowercase
- Password: Validated at schema level (8-128 chars), stored as Argon2id hash

---

### RefreshToken

Represents an active session token for token refresh operations.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `UUID` | PK, default uuid4 | Token record identifier |
| `user_id` | `UUID` | FK → User.id, indexed | Owner of the token |
| `token_hash` | `str` | SHA-256 hex digest | Hashed token value |
| `expires_at` | `datetime` | required | Token expiration time |
| `revoked` | `bool` | default False | Whether token is revoked |
| `created_at` | `datetime` | auto-set UTC | Token creation timestamp |

**SQLModel Definition**:
```python
class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(max_length=64)  # SHA-256 = 64 hex chars
    expires_at: datetime
    revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationship
    user: User = Relationship(back_populates="refresh_tokens")
```

**Token Lifecycle**:
1. Created on successful login
2. Rotated on token refresh (old invalidated, new created)
3. Revoked on logout, password change, or account lockout
4. Expired tokens rejected (7-day lifetime)
5. Cascade deleted when user is deleted

---

### PasswordResetToken

Represents a password reset request token.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `UUID` | PK, default uuid4 | Reset token record identifier |
| `user_id` | `UUID` | FK → User.id, indexed | User requesting reset |
| `token_hash` | `str` | SHA-256 hex digest | Hashed token value |
| `expires_at` | `datetime` | required | Token expiration (1 hour) |
| `used` | `bool` | default False | Whether token has been used |
| `created_at` | `datetime` | auto-set UTC | Request timestamp |

**SQLModel Definition**:
```python
class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_tokens"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(max_length=64)  # SHA-256 = 64 hex chars
    expires_at: datetime
    used: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationship
    user: User = Relationship(back_populates="password_reset_tokens")
```

**Token Lifecycle**:
1. Created on password reset request
2. Logged to console (no email in learning project)
3. Marked `used=True` after successful password change
4. Rejected if expired (1-hour lifetime) or already used
5. Cascade deleted when user is deleted

---

## State Transitions

### User Account States

```
                    ┌──────────────────┐
                    │     Created      │
                    │ (can login)      │
                    └────────┬─────────┘
                             │
            ┌────────────────┴────────────────┐
            │                                 │
            ▼                                 ▼
    ┌───────────────┐               ┌─────────────────┐
    │   Active      │◄──────────────│  Failed Login   │
    │ (successful   │   success     │  (1-4 attempts) │
    │  login)       │               └────────┬────────┘
    └───────────────┘                        │
            │                                │ 5th failure
            │                                ▼
            │                       ┌─────────────────┐
            │                       │     Locked      │
            │                       │  (15 minutes)   │
            │                       │  - all tokens   │
            │                       │    revoked      │
            │                       └────────┬────────┘
            │                                │
            │                                │ 15 min elapsed
            │                                ▼
            │                       ┌─────────────────┐
            │                       │    Unlocked     │
            │                       │ (can retry)     │
            └───────────────────────►────────────────┘

                                            │
                                            │ deletion request
                                            ▼
                                   ┌─────────────────┐
                                   │    Deleted      │
                                   │ (cascade: all   │
                                   │  tokens, tasks) │
                                   └─────────────────┘
```

### Refresh Token States

```
    ┌──────────────────┐
    │     Created      │───────► Valid (can refresh)
    │  (on login)      │
    └────────┬─────────┘
             │
    ┌────────┴─────────────────────────────┐
    │                │                     │
    ▼                ▼                     ▼
┌─────────┐   ┌──────────────┐     ┌──────────────┐
│ Rotated │   │   Revoked    │     │   Expired    │
│ (new    │   │ (logout,     │     │ (7 days)     │
│  issued)│   │  password    │     │              │
│         │   │  change,     │     │              │
└─────────┘   │  lockout)    │     └──────────────┘
              └──────────────┘
```

---

## Indexes

| Table | Index | Columns | Purpose |
|-------|-------|---------|---------|
| `users` | `ix_users_email` | `email` | Email lookup for login |
| `refresh_tokens` | `ix_refresh_tokens_user_id` | `user_id` | Find user's tokens |
| `refresh_tokens` | `ix_refresh_tokens_token_hash` | `token_hash` | Token lookup for refresh |
| `password_reset_tokens` | `ix_password_reset_tokens_user_id` | `user_id` | Find user's reset tokens |
| `password_reset_tokens` | `ix_password_reset_tokens_token_hash` | `token_hash` | Token lookup for reset |

---

## Pydantic Schemas

### User Schemas

```python
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
import re

class UserCreate(BaseModel):
    """Schema for user registration."""
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z\s]+$", v):
            raise ValueError("Name can only contain letters and spaces")
        return v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower()

class UserRead(BaseModel):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    created_at: datetime
```

### Authentication Schemas

```python
class LoginRequest(BaseModel):
    """Schema for login request."""
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower()

class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(description="Access token expiry in seconds")

class RefreshRequest(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str

class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower()

class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str
    new_password: str = Field(min_length=8, max_length=128)

class DeleteAccountRequest(BaseModel):
    """Schema for account deletion."""
    password: str
```

### Error Schemas

```python
class ErrorResponse(BaseModel):
    """Standard error response."""
    code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error message")
```

---

## Database Migrations

Initial migration creates all tables:

```sql
-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_users_email ON users(email);

-- Create refresh_tokens table
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX ix_refresh_tokens_token_hash ON refresh_tokens(token_hash);

-- Create password_reset_tokens table
CREATE TABLE password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX ix_password_reset_tokens_token_hash ON password_reset_tokens(token_hash);
```

---

## Constraints Summary

| Entity | Field | Constraint | Source |
|--------|-------|------------|--------|
| User | name | 1-100 chars | Spec constraints |
| User | name | Pattern: letters and spaces only | Acceptance scenario 1.5 |
| User | email | Max 254 chars | Spec constraints |
| User | email | Unique (case-insensitive) | FR-004 |
| User | password | 8-128 chars (at creation) | Spec constraints |
| RefreshToken | expires_at | 7 days from creation | Spec constraints |
| PasswordResetToken | expires_at | 1 hour from creation | Spec constraints |
| PasswordResetToken | used | Single-use | FR-018 |
