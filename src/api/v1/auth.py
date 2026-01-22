"""Authentication endpoints for login, logout, token refresh, and password reset."""

from fastapi import APIRouter, Depends, Request, status
from sqlmodel import Session

from src.api.deps import get_current_user
from src.core.exceptions import AccountLockedError
from src.database import get_session
from src.middleware.rate_limit import rate_limiter
from src.models.user import User
from src.schemas.auth import (
    LoginRequest,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    TokenResponse,
)
from src.services.auth_service import authenticate_user, is_account_locked
from src.services.password_service import (
    generate_password_reset_token,
    reset_password,
)
from src.services.token_service import (
    create_access_token,
    generate_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
    validate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    login_data: LoginRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """Authenticate user and return access and refresh tokens."""
    rate_limiter.check(request)

    user = authenticate_user(session, login_data.email, login_data.password)

    access_token, expires_in = create_access_token(user.id)
    refresh_token = generate_refresh_token(session, user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(
    refresh_data: RefreshRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """Exchange a valid refresh token for new access and refresh tokens."""
    token = validate_refresh_token(session, refresh_data.refresh_token)

    # Check if user account is locked
    user = token.user
    if is_account_locked(user):
        raise AccountLockedError()

    # Rotate token
    new_refresh_token = rotate_refresh_token(session, token)
    access_token, expires_in = create_access_token(token.user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=expires_in,
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    refresh_data: RefreshRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> MessageResponse:
    """Revoke the provided refresh token to log out the user."""
    revoke_refresh_token(session, refresh_data.refresh_token)
    return MessageResponse(message="Successfully logged out")


@router.post(
    "/password-reset/request",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def request_password_reset(
    request: Request,
    reset_data: PasswordResetRequest,
    session: Session = Depends(get_session),
) -> MessageResponse:
    """Request a password reset token. Same response regardless of email existence."""
    rate_limiter.check(request)
    # Always return same response to prevent email enumeration
    generate_password_reset_token(session, reset_data.email)
    return MessageResponse(
        message="If an account exists with this email, a reset token has been generated"
    )


@router.post("/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    session: Session = Depends(get_session),
) -> MessageResponse:
    """Complete password reset by validating token and setting new password."""
    reset_password(session, reset_data.token, reset_data.new_password)
    return MessageResponse(message="Password has been reset successfully")
