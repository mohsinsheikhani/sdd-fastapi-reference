# Tasks: User Authentication

**Input**: Design documents from `/specs/001-user-auth/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/auth-api.yaml ✓

**Tests**: Tests are included per TDD workflow specified in plan.md and quickstart.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US6)
- Include exact file paths in descriptions

## Path Conventions

- **Structure**: `src/`, `tests/` at repository root (single project)
- Based on plan.md project structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Initialize UV project with pyproject.toml and core dependencies
- [ ] T002 [P] Create src/ directory structure per plan.md (models/, schemas/, services/, api/, middleware/, core/)
- [ ] T003 [P] Create tests/ directory structure (conftest.py, unit/, integration/)
- [ ] T004 [P] Configure .gitignore with Python, .env, and IDE patterns
- [ ] T005 [P] Create .env.example with required environment variables (DATABASE_URL, SECRET_KEY, etc.)

### ✅ Checkpoint 1: Setup Complete

**Verification**:
```bash
# All must pass:
uv sync                              # Dependencies install without errors
ls src/models src/schemas src/services src/api src/middleware src/core  # All directories exist
ls tests/unit tests/integration      # Test directories exist
cat .gitignore | grep -q ".env"      # .env is in gitignore
test -f .env.example                 # .env.example exists
```

**Exit Criteria**:
- [ ] Project structure matches plan.md
- [ ] UV can resolve and install all dependencies
- [ ] .env.example contains all required variables from quickstart.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Implement Settings class with pydantic-settings in src/config.py
- [ ] T007 Implement database engine and session dependency in src/database.py
- [ ] T008 [P] Create base exception classes in src/core/exceptions.py (UserExistsError, InvalidCredentialsError, AccountLockedError, TokenExpiredError, TokenInvalidError, TokenRevokedError, ResetTokenInvalidError, RateLimitError)
- [ ] T009 [P] Create ErrorResponse schema in src/schemas/error.py
- [ ] T010 Implement global exception handlers for custom exceptions in src/main.py
- [ ] T011 [P] Implement password hashing functions (hash_password, verify_password) using Argon2id in src/core/security.py
- [ ] T012 [P] Implement token hashing function (hash_token) using SHA-256 in src/core/security.py
- [ ] T013 Implement RateLimiter class (5 req/min/IP sliding window) in src/middleware/rate_limit.py
- [ ] T014 Create FastAPI app skeleton with versioned router in src/main.py
- [ ] T015 Create v1 router aggregator in src/api/v1/router.py
- [ ] T016 Setup test fixtures (session, client) in tests/conftest.py

### ✅ Checkpoint 2: Foundation Ready

**Verification**:
```bash
# All must pass:
uv run python -c "from src.config import settings; print(settings)"     # Settings load from env
uv run python -c "from src.database import get_session; print('OK')"    # Database session works
uv run python -c "from src.core.exceptions import UserExistsError"      # Exceptions importable
uv run python -c "from src.core.security import hash_password; hash_password('test')"  # Argon2 works
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 &                # Server starts
curl http://localhost:8000/docs                                          # OpenAPI docs accessible
pkill -f uvicorn                                                         # Cleanup
```

**Exit Criteria**:
- [ ] FastAPI server starts without errors
- [ ] `/docs` endpoint shows OpenAPI documentation
- [ ] Settings load from environment variables
- [ ] Database session can be created
- [ ] All custom exceptions are defined and importable
- [ ] Password hashing returns valid Argon2id hashes
- [ ] Test fixtures work with pytest

**Gate**: User story implementation may now begin

---

## Phase 3: User Story 1 - New User Registration (Priority: P1) 🎯 MVP

**Goal**: Allow visitors to create accounts with name, email, and password

**Independent Test**: Submit registration form with valid name, email, password → verify HTTP 201 with user ID, name, email, created_at

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T017 [P] [US1] Integration test for valid registration (201) in tests/integration/test_registration.py
- [ ] T018 [P] [US1] Integration test for duplicate email (409) in tests/integration/test_registration.py
- [ ] T019 [P] [US1] Integration test for short password (422) in tests/integration/test_registration.py
- [ ] T020 [P] [US1] Integration test for invalid name (empty, >100 chars, invalid chars) (422) in tests/integration/test_registration.py
- [ ] T021 [P] [US1] Integration test for rate limiting (429) in tests/integration/test_registration.py

### Implementation for User Story 1

- [ ] T022 [P] [US1] Create User model with all fields per data-model.md in src/models/user.py
- [ ] T023 [P] [US1] Create UserCreate schema (name, email, password validation) in src/schemas/user.py
- [ ] T024 [P] [US1] Create UserRead schema (id, name, email, created_at) in src/schemas/user.py
- [ ] T025 [US1] Implement create_user function in src/services/user_service.py (hash password, normalize email, check duplicate)
- [ ] T026 [US1] Implement POST /users endpoint in src/api/v1/users.py (rate limited)
- [ ] T027 [US1] Wire users router to v1 router in src/api/v1/router.py
- [ ] T028 [US1] Run registration tests to verify all scenarios pass

### ✅ Checkpoint 3: Registration Functional

**Verification**:
```bash
# Run registration tests:
uv run pytest tests/integration/test_registration.py -v

# Manual API test:
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "email": "test@example.com", "password": "securepass123"}'
# Expected: HTTP 201 with user data

# Verify duplicate email rejected:
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "email": "test@example.com", "password": "securepass123"}'
# Expected: HTTP 409 USER_EMAIL_EXISTS
```

**Exit Criteria**:
- [ ] All 5 registration tests pass (T017-T021)
- [ ] POST /api/v1/users returns 201 with valid input
- [ ] Duplicate email returns 409 USER_EMAIL_EXISTS
- [ ] Invalid password returns 422 VALIDATION_ERROR
- [ ] Invalid name returns 422 VALIDATION_ERROR
- [ ] Rate limiting returns 429 after 5 requests/minute

**Deliverable**: Users can create accounts (MVP v0.1)

---

## Phase 4: User Story 2 - User Login (Priority: P1) 🎯 MVP

**Goal**: Allow registered users to authenticate and receive access/refresh tokens

**Independent Test**: Login with valid credentials → verify tokens returned, failed attempt counter reset

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T029 [P] [US2] Integration test for valid login (200) with tokens in tests/integration/test_login.py
- [ ] T030 [P] [US2] Integration test for invalid credentials (401) in tests/integration/test_login.py
- [ ] T031 [P] [US2] Integration test for account lockout after 5 failures (403) in tests/integration/test_login.py
- [ ] T032 [P] [US2] Integration test for auto-unlock after 15 minutes in tests/integration/test_login.py
- [ ] T033 [P] [US2] Integration test for case-insensitive email in tests/integration/test_login.py
- [ ] T034 [P] [US2] Integration test for failed counter reset on success in tests/integration/test_login.py
- [ ] T035 [P] [US2] Integration test for all tokens revoked on lockout in tests/integration/test_login.py

### Implementation for User Story 2

- [ ] T036 [P] [US2] Create RefreshToken model with all fields per data-model.md in src/models/token.py
- [ ] T037 [P] [US2] Create LoginRequest schema in src/schemas/auth.py
- [ ] T038 [P] [US2] Create TokenResponse schema in src/schemas/auth.py
- [ ] T039 [US2] Implement JWT access token creation (create_access_token) in src/services/token_service.py
- [ ] T040 [US2] Implement refresh token generation (generate_refresh_token, store hashed) in src/services/token_service.py
- [ ] T041 [US2] Implement revoke_all_user_tokens function in src/services/token_service.py
- [ ] T042 [US2] Implement authenticate_user function in src/services/auth_service.py (check lockout, verify password, track failures, reset counter)
- [ ] T043 [US2] Implement POST /auth/login endpoint in src/api/v1/auth.py (rate limited)
- [ ] T044 [US2] Wire auth router to v1 router in src/api/v1/router.py
- [ ] T045 [US2] Run login tests to verify all scenarios pass

### ✅ Checkpoint 4: Login Functional (MVP Complete)

**Verification**:
```bash
# Run login tests:
uv run pytest tests/integration/test_login.py -v

# Manual API test - full registration + login flow:
# 1. Register user
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"name": "MVP User", "email": "mvp@example.com", "password": "securepass123"}'

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "mvp@example.com", "password": "securepass123"}'
# Expected: HTTP 200 with access_token, refresh_token, token_type, expires_in

# 3. Verify JWT
uv run python -c "from jose import jwt; print(jwt.get_unverified_claims('ACCESS_TOKEN_HERE'))"
# Expected: Claims with sub (user_id), exp, iat
```

**Exit Criteria**:
- [ ] All 7 login tests pass (T029-T035)
- [ ] POST /api/v1/auth/login returns 200 with tokens on valid credentials
- [ ] Invalid credentials return 401 AUTH_INVALID_CREDENTIALS
- [ ] Account locks after 5 failed attempts with 403 AUTH_ACCOUNT_LOCKED
- [ ] Locked account unlocks after 15 minutes
- [ ] Email comparison is case-insensitive
- [ ] Failed counter resets on successful login

**Deliverable**: Users can register AND login (MVP v0.2 - Core Auth Complete)

**🎯 MVP MILESTONE**: System is now usable - users can create accounts and authenticate

---

## Phase 5: User Story 3 - Token Refresh (Priority: P2)

**Goal**: Allow users to exchange valid refresh tokens for new access tokens with rotation

**Independent Test**: Submit valid refresh token → verify new access token and new refresh token returned, old token invalidated

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T046 [P] [US3] Integration test for valid refresh (200) with rotation in tests/integration/test_token_refresh.py
- [ ] T047 [P] [US3] Integration test for expired refresh token (401) in tests/integration/test_token_refresh.py
- [ ] T048 [P] [US3] Integration test for revoked refresh token (401) in tests/integration/test_token_refresh.py
- [ ] T049 [P] [US3] Integration test for already-rotated token (401) in tests/integration/test_token_refresh.py
- [ ] T050 [P] [US3] Integration test for locked account blocking refresh (403) in tests/integration/test_token_refresh.py

### Implementation for User Story 3

- [ ] T051 [P] [US3] Create RefreshRequest schema in src/schemas/auth.py
- [ ] T052 [US3] Implement validate_refresh_token function in src/services/token_service.py (check expired, revoked, lookup by hash)
- [ ] T053 [US3] Implement rotate_refresh_token function in src/services/token_service.py (invalidate old, create new)
- [ ] T054 [US3] Implement POST /auth/refresh endpoint in src/api/v1/auth.py
- [ ] T055 [US3] Run token refresh tests to verify all scenarios pass

### ✅ Checkpoint 5: Token Refresh Functional

**Verification**:
```bash
# Run token refresh tests:
uv run pytest tests/integration/test_token_refresh.py -v

# Manual API test:
# 1. Login to get tokens
TOKENS=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "mvp@example.com", "password": "securepass123"}')
REFRESH_TOKEN=$(echo $TOKENS | jq -r '.refresh_token')

# 2. Refresh tokens
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"
# Expected: HTTP 200 with new access_token and new refresh_token

# 3. Verify old refresh token is rejected (rotation)
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"
# Expected: HTTP 401 AUTH_TOKEN_REVOKED (already rotated)
```

**Exit Criteria**:
- [ ] All 5 token refresh tests pass (T046-T050)
- [ ] POST /api/v1/auth/refresh returns 200 with new tokens
- [ ] Old refresh token is invalidated after use (rotation)
- [ ] Expired tokens return 401 AUTH_TOKEN_EXPIRED
- [ ] Revoked tokens return 401 AUTH_TOKEN_REVOKED
- [ ] Locked accounts cannot refresh (403 AUTH_ACCOUNT_LOCKED)

**Deliverable**: Users can extend sessions without re-login (v0.3 partial)

---

## Phase 6: User Story 4 - User Logout (Priority: P2)

**Goal**: Allow authenticated users to end their session by revoking refresh token

**Independent Test**: Submit logout request → verify refresh token is revoked, subsequent use fails

### Tests for User Story 4 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T056 [P] [US4] Integration test for valid logout (200) in tests/integration/test_logout.py
- [ ] T057 [P] [US4] Integration test for revoked token rejected on reuse (401) in tests/integration/test_logout.py

### Implementation for User Story 4

- [ ] T058 [P] [US4] Create MessageResponse schema in src/schemas/auth.py
- [ ] T059 [US4] Implement get_current_user dependency in src/api/deps.py (decode JWT, verify user exists, check lockout)
- [ ] T060 [US4] Implement revoke_refresh_token function in src/services/token_service.py
- [ ] T061 [US4] Implement POST /auth/logout endpoint in src/api/v1/auth.py (requires auth)
- [ ] T062 [US4] Run logout tests to verify all scenarios pass

### ✅ Checkpoint 6: Logout Functional (Session Management Complete)

**Verification**:
```bash
# Run logout tests:
uv run pytest tests/integration/test_logout.py -v

# Manual API test:
# 1. Login to get tokens
TOKENS=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "mvp@example.com", "password": "securepass123"}')
ACCESS_TOKEN=$(echo $TOKENS | jq -r '.access_token')
REFRESH_TOKEN=$(echo $TOKENS | jq -r '.refresh_token')

# 2. Logout
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"
# Expected: HTTP 200 with message "Successfully logged out"

# 3. Verify refresh token is now revoked
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"
# Expected: HTTP 401 AUTH_TOKEN_REVOKED
```

**Exit Criteria**:
- [ ] All 2 logout tests pass (T056-T057)
- [ ] POST /api/v1/auth/logout returns 200 with success message
- [ ] Refresh token is revoked after logout
- [ ] Revoked token cannot be used to refresh

**Deliverable**: Full session management (v0.3 - Register, Login, Refresh, Logout)

---

## Phase 7: User Story 5 - Password Reset (Priority: P3)

**Goal**: Allow users to reset forgotten passwords via console-logged reset token

**Independent Test**: Request reset → retrieve token from console → submit new password → login with new password succeeds

### Tests for User Story 5 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T063 [P] [US5] Integration test for password reset request (202) in tests/integration/test_password_reset.py
- [ ] T064 [P] [US5] Integration test for identical response on unknown email (202) in tests/integration/test_password_reset.py
- [ ] T065 [P] [US5] Integration test for valid reset confirmation (200) in tests/integration/test_password_reset.py
- [ ] T066 [P] [US5] Integration test for expired reset token (400) in tests/integration/test_password_reset.py
- [ ] T067 [P] [US5] Integration test for already-used reset token (400) in tests/integration/test_password_reset.py
- [ ] T068 [P] [US5] Integration test for all refresh tokens revoked on password change in tests/integration/test_password_reset.py

### Implementation for User Story 5

- [ ] T069 [P] [US5] Create PasswordResetToken model with all fields per data-model.md in src/models/token.py
- [ ] T070 [P] [US5] Create PasswordResetRequest schema in src/schemas/auth.py
- [ ] T071 [P] [US5] Create PasswordResetConfirm schema in src/schemas/auth.py
- [ ] T072 [US5] Implement generate_password_reset_token function in src/services/password_service.py (create token, hash, store, log to console)
- [ ] T073 [US5] Implement validate_reset_token function in src/services/password_service.py (check expired, used)
- [ ] T074 [US5] Implement reset_password function in src/services/password_service.py (update hash, mark token used, revoke all refresh tokens)
- [ ] T075 [US5] Implement POST /auth/password-reset/request endpoint in src/api/v1/auth.py (rate limited)
- [ ] T076 [US5] Implement POST /auth/password-reset/confirm endpoint in src/api/v1/auth.py
- [ ] T077 [US5] Run password reset tests to verify all scenarios pass

### ✅ Checkpoint 7: Password Reset Functional

**Verification**:
```bash
# Run password reset tests:
uv run pytest tests/integration/test_password_reset.py -v

# Manual API test:
# 1. Request password reset (check server console for token)
curl -X POST http://localhost:8000/api/v1/auth/password-reset/request \
  -H "Content-Type: application/json" \
  -d '{"email": "mvp@example.com"}'
# Expected: HTTP 202 with message (check console for reset token)

# 2. Confirm password reset (use token from console)
curl -X POST http://localhost:8000/api/v1/auth/password-reset/confirm \
  -H "Content-Type: application/json" \
  -d '{"token": "RESET_TOKEN_FROM_CONSOLE", "new_password": "newpassword456"}'
# Expected: HTTP 200 with success message

# 3. Login with new password
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "mvp@example.com", "password": "newpassword456"}'
# Expected: HTTP 200 with tokens

# 4. Verify old password no longer works
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "mvp@example.com", "password": "securepass123"}'
# Expected: HTTP 401 AUTH_INVALID_CREDENTIALS
```

**Exit Criteria**:
- [ ] All 6 password reset tests pass (T063-T068)
- [ ] POST /api/v1/auth/password-reset/request returns 202 (always, to prevent enumeration)
- [ ] Reset token is logged to console
- [ ] POST /api/v1/auth/password-reset/confirm returns 200 with valid token
- [ ] Password is updated and user can login with new password
- [ ] All existing refresh tokens are revoked on password change
- [ ] Expired/used tokens return 400 RESET_TOKEN_INVALID

**Deliverable**: Account recovery capability (v0.4)

---

## Phase 8: User Story 6 - Account Deletion (Priority: P3)

**Goal**: Allow authenticated users to permanently delete their account with password confirmation

**Independent Test**: Submit deletion with correct password → verify account and all data removed, login fails

### Tests for User Story 6 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T078 [P] [US6] Integration test for valid account deletion (204) in tests/integration/test_account_deletion.py
- [ ] T079 [P] [US6] Integration test for wrong password (401) in tests/integration/test_account_deletion.py
- [ ] T080 [P] [US6] Integration test for cascade deletion (tokens removed) in tests/integration/test_account_deletion.py
- [ ] T081 [P] [US6] Integration test for deleted account cannot login in tests/integration/test_account_deletion.py

### Implementation for User Story 6

- [ ] T082 [P] [US6] Create DeleteAccountRequest schema in src/schemas/auth.py
- [ ] T083 [US6] Implement delete_user function in src/services/user_service.py (verify password, cascade delete via relationship)
- [ ] T084 [US6] Implement DELETE /users/me endpoint in src/api/v1/users.py (requires auth)
- [ ] T085 [US6] Run account deletion tests to verify all scenarios pass

### ✅ Checkpoint 8: Account Deletion Functional (Feature Complete)

**Verification**:
```bash
# Run account deletion tests:
uv run pytest tests/integration/test_account_deletion.py -v

# Manual API test:
# 1. Register a test user for deletion
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Delete Me", "email": "deleteme@example.com", "password": "securepass123"}'

# 2. Login to get token
TOKENS=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "deleteme@example.com", "password": "securepass123"}')
ACCESS_TOKEN=$(echo $TOKENS | jq -r '.access_token')

# 3. Delete account
curl -X DELETE http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password": "securepass123"}'
# Expected: HTTP 204 No Content

# 4. Verify login fails
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "deleteme@example.com", "password": "securepass123"}'
# Expected: HTTP 401 AUTH_INVALID_CREDENTIALS (user not found)
```

**Exit Criteria**:
- [ ] All 4 account deletion tests pass (T078-T081)
- [ ] DELETE /api/v1/users/me returns 204 with correct password
- [ ] Wrong password returns 401 AUTH_INVALID_CREDENTIALS
- [ ] User record and all related tokens are cascade deleted
- [ ] Deleted user cannot login

**Deliverable**: Complete user data control (v1.0 - All User Stories Complete)

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and improvements

- [ ] T086 [P] Add docstrings to all public functions in src/services/
- [ ] T087 [P] Add docstrings to all endpoint functions in src/api/v1/
- [ ] T088 Run mypy type checking on src/ and fix any errors
- [ ] T089 Run ruff linting on src/ and fix any issues
- [ ] T090 Run full test suite with coverage: uv run pytest --cov=src --cov-report=term-missing
- [ ] T091 Validate against quickstart.md examples (manual API testing)
- [ ] T092 Verify all acceptance criteria from spec.md are covered by tests

### ✅ Checkpoint 9: Production Ready

**Verification**:
```bash
# Type checking
uv run mypy src/
# Expected: No errors

# Linting
uv run ruff check src/
# Expected: No issues (or all fixed)

# Full test suite with coverage
uv run pytest --cov=src --cov-report=term-missing -v
# Expected: All tests pass, coverage report shows >80%

# Verify all quickstart.md examples work
# (Run through each example in quickstart.md manually)

# Final acceptance criteria check
# (Verify each scenario from spec.md has a corresponding test)
```

**Exit Criteria**:
- [ ] mypy reports no type errors
- [ ] ruff reports no linting issues
- [ ] All 37 integration tests pass
- [ ] Code coverage is adequate (target >80%)
- [ ] All quickstart.md examples work as documented
- [ ] All acceptance scenarios from spec.md are covered

**Deliverable**: Production-ready authentication system (v1.0 GA)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2)
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) + requires User model from US1
- **User Story 3 (Phase 5)**: Depends on User Story 2 (needs login to get tokens)
- **User Story 4 (Phase 6)**: Depends on User Story 2 (needs login to get tokens)
- **User Story 5 (Phase 7)**: Depends on Foundational (Phase 2) + requires User model from US1
- **User Story 6 (Phase 8)**: Depends on User Story 2 (needs auth dependency)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

```
                  ┌─────────────┐
                  │   Setup     │
                  │  (Phase 1)  │
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │ Foundational │
                  │  (Phase 2)   │
                  └──────┬──────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
   ┌──────▼──────┐       │       ┌──────▼──────┐
   │    US1      │       │       │    US5      │
   │ Registration │       │       │ Pwd Reset   │
   │   (P1) MVP  │       │       │    (P3)     │
   └──────┬──────┘       │       └─────────────┘
          │              │
   ┌──────▼──────┐       │
   │    US2      ├───────┘
   │   Login     │
   │   (P1) MVP  │
   └──────┬──────┘
          │
   ┌──────┼──────────────┐
   │      │              │
┌──▼───┐ ┌▼────┐   ┌─────▼────┐
│ US3  │ │ US4 │   │   US6    │
│Refresh│ │Logout│   │ Deletion │
│ (P2) │ │ (P2)│   │   (P3)   │
└──────┘ └─────┘   └──────────┘
```

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
- T002, T003, T004, T005 can run in parallel

**Phase 2 (Foundational)**:
- T008, T009 can run in parallel
- T011, T012 can run in parallel

**Each User Story**:
- All tests marked [P] can run in parallel
- Models and schemas marked [P] can run in parallel

---

## Parallel Examples

### Setup Phase Parallel Tasks

```bash
# Launch together:
Task: "Create src/ directory structure per plan.md"
Task: "Create tests/ directory structure"
Task: "Configure .gitignore"
Task: "Create .env.example"
```

### User Story 1 Parallel Tests

```bash
# Launch all registration tests together:
Task: "Integration test for valid registration (201)"
Task: "Integration test for duplicate email (409)"
Task: "Integration test for short password (422)"
Task: "Integration test for invalid name (422)"
Task: "Integration test for rate limiting (429)"
```

### User Story 1 Parallel Models/Schemas

```bash
# Launch together:
Task: "Create User model in src/models/user.py"
Task: "Create UserCreate schema in src/schemas/user.py"
Task: "Create UserRead schema in src/schemas/user.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup → **Checkpoint 1**
2. Complete Phase 2: Foundational → **Checkpoint 2** (CRITICAL)
3. Complete Phase 3: User Story 1 → **Checkpoint 3**
4. Complete Phase 4: User Story 2 → **Checkpoint 4** 🎯
5. **STOP and VALIDATE**: Test registration + login flow end-to-end
6. Deploy/demo if ready - **users can now sign up and login**

### Incremental Delivery

1. Setup + Foundational → **Checkpoints 1 & 2**: Foundation ready
2. Add US1 (Registration) → **Checkpoint 3**: **MVP v0.1**: Users can register
3. Add US2 (Login) → **Checkpoint 4**: **MVP v0.2**: Users can register + login 🎯
4. Add US3 + US4 (Refresh + Logout) → **Checkpoints 5 & 6**: **v0.3**: Full session management
5. Add US5 (Password Reset) → **Checkpoint 7**: **v0.4**: Account recovery
6. Add US6 (Deletion) → **Checkpoint 8**: **v1.0**: Complete auth system
7. Polish → **Checkpoint 9**: **v1.0 GA**: Production ready

---

## Summary

| Phase | Task Count | Parallelizable | User Story | Checkpoint |
|-------|------------|----------------|------------|------------|
| Setup | 5 | 4 | - | ✅ 1 |
| Foundational | 11 | 4 | - | ✅ 2 |
| US1: Registration | 12 | 9 | P1 MVP | ✅ 3 |
| US2: Login | 17 | 11 | P1 MVP | ✅ 4 🎯 |
| US3: Token Refresh | 10 | 6 | P2 | ✅ 5 |
| US4: Logout | 7 | 3 | P2 | ✅ 6 |
| US5: Password Reset | 15 | 10 | P3 | ✅ 7 |
| US6: Deletion | 8 | 5 | P3 | ✅ 8 |
| Polish | 7 | 2 | - | ✅ 9 |
| **Total** | **92** | **54** | - | **9 checkpoints** |

**MVP Scope**: Phases 1-4 (US1 + US2) = 45 tasks → Users can register and login

**Independent Test Criteria per Story**:
- US1: Register with valid name/email/password → 201 with user data
- US2: Login with valid credentials → 200 with tokens
- US3: Refresh with valid token → 200 with new tokens
- US4: Logout → token invalidated
- US5: Request reset + confirm → login with new password succeeds
- US6: Delete with password → 204, subsequent login fails
