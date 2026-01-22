"""User service for registration and account management."""

from sqlmodel import Session, select

from src.core.exceptions import InvalidCredentialsError, UserExistsError
from src.core.security import hash_password, verify_password
from src.models.user import User
from src.schemas.user import UserCreate


def create_user(session: Session, user_data: UserCreate) -> User:
    existing = session.exec(
        select(User).where(User.email == user_data.email)
    ).first()
    if existing:
        raise UserExistsError()

    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(session: Session, user: User, password: str) -> None:
    """Delete user after verifying password. Cascade deletes all related tokens."""
    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()

    session.delete(user)
    session.commit()
