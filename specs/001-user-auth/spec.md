# Feature Specification: User Authentication

**Feature Branch**: `001-user-auth`
**Created**: 2026-01-15
**Status**: Clarified
**Last Updated**: 2026-01-17
**Input**: User authentication system with email/password, JWT tokens, and password reset for a task management API

## User Scenarios & Testing *(mandatory)*

### User Story 1 - New User Registration (Priority: P1)

A new user wants to create an account to start managing their tasks. They provide their name, email address and a password, and the system creates their account so they can begin using the task management features.

**Why this priority**: Without registration, no users can access the system. This is the entry point for all functionality.

**Independent Test**: Can be fully tested by submitting registration form with valid name, email and password and verifying account creation. Delivers the ability to create a user identity in the system.

**Acceptance Scenarios**:

1. **Given** a visitor with no account, **When** they submit a valid name, email and password (min 8 characters), **Then** their account is created and they receive HTTP 201 with their user ID, name, email, and created timestamp
2. **Given** a visitor, **When** they submit an email that already exists, **Then** they receive an error indicating the email is taken
3. **Given** a visitor, **When** they submit a password shorter than 8 characters, **Then** they receive a validation error
4. **Given** a visitor, **When** they submit an empty name or name exceeding 100 characters, **Then** they receive a validation error
5. **Given** a visitor, **When** they submit a name with invalid characters (numbers, special symbols), **Then** they receive a validation error

---

### User Story 2 - User Login (Priority: P1)

A registered user wants to authenticate to access their tasks. They provide their credentials and receive access tokens that allow them to make authenticated requests.

**Why this priority**: Login is essential for accessing any protected functionality. Without it, registered users cannot use the system.

**Independent Test**: Can be fully tested by logging in with valid credentials and verifying tokens are returned. Delivers authenticated access to the system.

**Acceptance Scenarios**:

1. **Given** a registered user with valid credentials, **When** they submit correct email and password, **Then** they receive access and refresh tokens and failed attempt counter is reset
2. **Given** a user, **When** they submit incorrect password, **Then** they receive an authentication error and failed attempt is recorded
3. **Given** a user with 5 consecutive failed login attempts, **When** they attempt to login again, **Then** their account is temporarily locked for 15 minutes and all refresh tokens are revoked
4. **Given** a locked account, **When** 15 minutes have passed, **Then** the user can attempt to login again
5. **Given** a user with email in different casing, **When** they submit correct credentials, **Then** login succeeds (email comparison is case-insensitive)

---

### User Story 3 - Token Refresh (Priority: P2)

An authenticated user's access token expires during their session. They use their refresh token to obtain a new access token without re-entering credentials.

**Why this priority**: Enables seamless user experience during extended sessions. Required for practical usability but login must work first.

**Independent Test**: Can be fully tested by using a valid refresh token to obtain new access token. Delivers uninterrupted access during sessions.

**Acceptance Scenarios**:

1. **Given** a user with a valid refresh token, **When** they request a new access token, **Then** they receive a fresh access token and a new refresh token (old refresh token is invalidated)
2. **Given** a user with an expired refresh token, **When** they attempt to refresh, **Then** they receive an error and must login again
3. **Given** a user with a revoked refresh token, **When** they attempt to refresh, **Then** they receive an error and must login again
4. **Given** a user who just refreshed their token, **When** they attempt to use the old refresh token, **Then** they receive an error (token already rotated)

---

### User Story 4 - User Logout (Priority: P2)

An authenticated user wants to end their session securely. When they logout, their refresh token is invalidated so it cannot be used again.

**Why this priority**: Security feature that allows users to end sessions. Important but not blocking for basic functionality.

**Independent Test**: Can be fully tested by logging out and verifying refresh token is invalidated. Delivers secure session termination.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they request logout, **Then** their current refresh token is revoked
2. **Given** a logged-out user, **When** they attempt to use the old refresh token, **Then** they receive an error

---

### User Story 5 - Password Reset (Priority: P3)

A user has forgotten their password and needs to regain access to their account. They request a password reset, receive a reset token (logged to console for this learning project), and use it to set a new password.

**Why this priority**: Recovery mechanism for lost access. Important for user experience but users can still register new accounts as fallback.

**Independent Test**: Can be fully tested by requesting reset, using logged token to set new password, and logging in with new password. Delivers account recovery capability.

**Acceptance Scenarios**:

1. **Given** a registered user who forgot their password, **When** they request a password reset with their email, **Then** a reset token is generated and logged to console
2. **Given** a user with a valid reset token, **When** they submit a new password, **Then** their password is updated and all existing refresh tokens are revoked
3. **Given** a user with an expired or invalid reset token, **When** they attempt to reset password, **Then** they receive an error
4. **Given** any request to password reset endpoint, **When** an unregistered email is submitted, **Then** the system responds identically to prevent email enumeration

---

### User Story 6 - Account Deletion (Priority: P3)

A user wants to permanently delete their account and all associated data. When they delete their account, all their information including tasks is permanently removed.

**Why this priority**: User control over their data. Lower priority as it's not needed for core task management functionality.

**Independent Test**: Can be fully tested by deleting account and verifying user cannot login and tasks are removed. Delivers data sovereignty to users.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they request account deletion with correct password confirmation, **Then** their account and all associated data are permanently deleted
2. **Given** an authenticated user, **When** they request account deletion with incorrect password, **Then** they receive an authentication error and account is not deleted
3. **Given** a deleted account, **When** someone attempts to login with those credentials, **Then** they receive an authentication error (account not found)

---

### Edge Cases

- What happens when a user attempts rapid repeated login attempts? Rate limiting kicks in after 5 attempts per minute per IP
- How does the system handle concurrent login from multiple devices? Each login generates independent tokens; no session limit enforced
- What happens when a user changes their password while logged in elsewhere? All existing refresh tokens are revoked, forcing re-authentication
- How does the system respond when an access token expires mid-request? Request fails with authentication error; client must refresh and retry
- What happens if the password reset token is used after user has already reset? Token is single-use and invalidated after first use
- What happens when an account is locked due to failed attempts? All active refresh tokens are revoked; login and token refresh endpoints blocked for 15 minutes
- What happens when a refresh token is used twice (replay attack)? Second attempt fails; token was already rotated on first use
- What happens when user registers with different email casing? Emails are normalized to lowercase; `User@Email.com` and `user@email.com` are treated as the same
- What happens to failed attempt counter on successful login? Counter resets to zero

## Constraints

| Field | Constraint |
|-------|------------|
| Name | 1-100 characters, letters, spaces, hyphens, apostrophes allowed |
| Email | Max 254 characters |
| Password | 8-128 characters |
| Access token | 15-minute expiry |
| Refresh token | 7-day expiry |
| Reset token | Single-use, 1-hour expiry |
| Account lockout | After 5 consecutive failures, 15-minute duration |
| Rate limiting | 5 requests per minute per IP on auth endpoints |

## Requirements *(mandatory)*

### Functional Requirements

**Registration**
- **FR-001**: System MUST allow users to create accounts with name, email and password
- **FR-002**: System MUST validate email format (RFC 5322 compliant) before account creation
- **FR-003**: System MUST enforce minimum password length of 8 characters
- **FR-004**: System MUST reject registration if email already exists (case-insensitive comparison)
- **FR-005**: System MUST store passwords using Argon2id hashing with OWASP-recommended parameters
- **FR-029**: System MUST normalize email addresses to lowercase before storage

**Authentication**
- **FR-006**: System MUST authenticate users via email and password
- **FR-007**: System MUST issue access tokens with 15-minute expiration
- **FR-008**: System MUST issue refresh tokens with 7-day expiration
- **FR-009**: System MUST record failed login attempts per user
- **FR-010**: System MUST lock accounts after 5 consecutive failed login attempts
- **FR-011**: System MUST automatically unlock accounts after 15 minutes
- **FR-028**: System MUST revoke all active refresh tokens when account is locked
- **FR-030**: System MUST reset failed login attempt counter on successful login

**Token Management**
- **FR-012**: System MUST allow users to exchange valid refresh tokens for new access tokens and new refresh tokens (rotation)
- **FR-013**: System MUST reject expired or revoked refresh tokens
- **FR-014**: System MUST allow users to revoke their refresh token (logout)
- **FR-026**: System MUST invalidate the old refresh token when a new one is issued (rotation)

**Password Reset**
- **FR-015**: System MUST generate password reset tokens on request
- **FR-016**: System MUST output reset tokens to a configured channel (for this learning project, no email delivery required)
- **FR-017**: System MUST expire reset tokens after 1 hour
- **FR-018**: System MUST invalidate reset tokens after single use
- **FR-019**: System MUST revoke all refresh tokens when password is changed
- **FR-020**: System MUST respond identically for registered and unregistered emails to prevent enumeration

**Account Management**
- **FR-021**: System MUST allow authenticated users to permanently delete their account after password confirmation
- **FR-022**: System MUST cascade delete all user data (including tasks) on account deletion
- **FR-027**: System MUST reject account deletion requests with incorrect password

**Security**
- **FR-023**: System MUST rate limit login and registration endpoints (5 requests per minute per IP)
- **FR-024**: System MUST not expose sensitive information in error messages
- **FR-025**: System MUST not log passwords or tokens in plain text

### Error Codes

All error responses MUST include a machine-readable code and human-readable message.

| Code | HTTP Status | Condition |
|------|-------------|-----------|
| `VALIDATION_ERROR` | 422 | Invalid input format (name, email, password constraints) |
| `USER_EMAIL_EXISTS` | 409 | Registration with existing email |
| `USER_NOT_FOUND` | 404 | Account does not exist |
| `AUTH_INVALID_CREDENTIALS` | 401 | Wrong email or password |
| `AUTH_ACCOUNT_LOCKED` | 403 | Account locked due to failed attempts |
| `AUTH_TOKEN_EXPIRED` | 401 | Access or refresh token has expired |
| `AUTH_TOKEN_INVALID` | 401 | Token is malformed or tampered |
| `AUTH_TOKEN_REVOKED` | 401 | Token was explicitly revoked |
| `RESET_TOKEN_INVALID` | 400 | Reset token is invalid, expired, or already used |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests from this IP |

### Key Entities

- **User**: Represents a registered account holder. Key attributes: name, unique email, hashed password, account lock status, failed attempt count, lock expiry time, created timestamp, updated timestamp
- **RefreshToken**: Represents an active session token. Key attributes: associated user, hashed token value, expiration time, revocation status, created timestamp
- **PasswordResetToken**: Represents a password reset request. Key attributes: associated user, hashed token value, expiration time, used flag, created timestamp

### API Response Shapes

**Registration Success** (HTTP 201):
- User ID
- User name
- User email
- Created timestamp

**Login Success** (HTTP 200):
- Access token (contains: user ID, expiration)
- Refresh token (opaque string)
- Token type ("Bearer")
- Access token expiry (seconds)

**Token Refresh Success** (HTTP 200):
- Access token
- Refresh token (new, rotated)
- Token type ("Bearer")
- Access token expiry (seconds)

**Password Reset Request** (HTTP 202):
- Acknowledgment message (identical for existing and non-existing emails)

**Password Reset Confirm** (HTTP 200):
- Success message

**Account Deletion Request** (HTTP DELETE):
- Password (required for confirmation)

**Account Deletion Success** (HTTP 204):
- No content

**Error Response** (HTTP 4xx):
- Error code (from Error Codes table)
- Error message (human-readable)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete registration from form submission to confirmation response in under 30 seconds (excluding client-side form filling time)
- **SC-002**: Users can login and receive tokens in under 2 seconds
- **SC-003**: 100% of stored passwords use industry-standard secure hashing resistant to brute-force attacks (verifiable via database audit showing no plaintext or reversible formats)
- **SC-004**: Account lockout activates after exactly 5 failed attempts
- **SC-005**: Locked accounts automatically unlock after 15 minutes
- **SC-006**: Password reset confirmation (submitting new password with valid token) completes in under 5 seconds; full flow (request + user action + confirmation) completes in under 1 minute excluding user think-time
- **SC-007**: All refresh tokens are invalidated within 1 second of password change
- **SC-008**: Account deletion removes User record, all associated RefreshTokens, and all user-owned Tasks with zero orphaned references (verifiable via data integrity check confirming no records reference deleted user)
- **SC-009**: Rate limiting blocks the 6th+ request within 60 seconds from the same IP; legitimate usage pattern (1 login attempt per session) never triggers rate limiting

## Assumptions

- This is a learning project; production-grade email delivery is out of scope
- Single-tenant deployment; no organization or team features needed
- User volume is minimal (personal use); no horizontal scaling requirements
- A relational database is available for persistence
- No MFA/2FA required for this phase
- No concurrent session limits; users can be logged in from multiple devices
- Email addresses are the unique user identifier (case-insensitive, stored lowercase)
- User IDs are UUID v4 format
- All timestamps are stored and returned in UTC
- Failed login attempt counters reset on successful login
- Token storage on the client side is out of scope for this API

## Technical Decisions

### Password Security
- **Algorithm**: Argon2id with OWASP-recommended default parameters
- **Complexity**: Minimum 8 characters only; no additional complexity rules enforced

### Token Architecture
- **Access Tokens**: JWT format, signed with HS256
  - Claims: `sub` (user UUID), `exp` (expiration timestamp), `iat` (issued at timestamp)
  - Expiry: 15 minutes
- **Refresh Tokens**: Opaque, database-backed tokens
  - Expiry: 7 days
  - Rotation: New refresh token issued on every token refresh (old token invalidated)
- **Password Reset Tokens**: Opaque, database-backed, single-use
  - Expiry: 1 hour
  - Delivery: Console logging only (no email integration)

### Account Lockout Behavior
- **Scope**: Lockout blocks login (`/auth/login`) and token refresh (`/auth/refresh`) endpoints only
- **Duration**: 15 minutes from last failed attempt
- **Token Revocation**: All active refresh tokens are revoked when account is locked
- **Error Response**: Does not include remaining lockout time (security consideration)

### Email Handling
- **Validation**: Basic RFC 5322 compliant format validation
- **Uniqueness**: Case-insensitive comparison; stored in lowercase
- **Enumeration Protection**: Identical responses for existing and non-existing emails on password reset

### Account Deletion
- **Confirmation**: Requires password confirmation in request body
- **Cascade**: Deletes user record, all refresh tokens, and all associated tasks

### Rate Limiting
- **Ownership**: Implemented as shared middleware (not auth-specific logic)
- **Scope**: Applied per-endpoint on authentication routes
- **Limit**: 5 requests per minute per IP address

### Registration Flow
- **Post-Registration**: Registration does NOT automatically authenticate the user
- **Login Required**: User must explicitly call `/auth/login` after registration to obtain tokens

## Non-Goals

- This specification does not define task creation, modification, or management behavior
- Authorization rules related to task ownership are handled by the Task API specification
- Role-based access control, permissions, and organizations are out of scope
- OAuth, social login, and third-party identity providers are not included
- Multi-factor authentication is not included
- Email verification flow (accounts are active immediately upon registration)
- Account recovery without email access (no security questions, backup codes)
- User profile editing (name change, email change) beyond account deletion
- Session listing or management UI (users cannot see/revoke individual sessions)
- Audit logging of authentication events (login history, security alerts)
