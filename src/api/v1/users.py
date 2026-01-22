"""User management endpoints for registration and account deletion."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlmodel import Session

from src.api.deps import get_current_user
from src.database import get_session
from src.middleware.rate_limit import rate_limiter
from src.models.user import User
from src.schemas.auth import DeleteAccountRequest
from src.schemas.user import UserCreate, UserRead
from src.services.user_service import create_user, delete_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    request: Request,
    user_data: UserCreate,
    session: Session = Depends(get_session),
) -> UserRead:
    """Register a new user account."""
    rate_limiter.check(request)
    user = create_user(session, user_data)
    return UserRead.model_validate(user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    delete_data: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Response:
    """Delete the authenticated user's account after password verification."""
    delete_user(session, current_user, delete_data.password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
