import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from src.config import settings
from src.core.exceptions import AccountLockedError, TokenInvalidError
from src.database import get_session
from src.models.user import User
from src.services.auth_service import is_account_locked

security = HTTPBearer()
ALGORITHM = "HS256"


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> User:
    """Decode JWT and return current user. Raises 401 if invalid."""
    token = credentials.credentials

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise TokenInvalidError()
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_TOKEN_INVALID", "message": "Invalid token"},
        )

    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_TOKEN_INVALID", "message": "User not found"},
        )

    if is_account_locked(user):
        raise AccountLockedError()

    return user
