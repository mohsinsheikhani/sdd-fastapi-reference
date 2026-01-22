import uuid
from datetime import UTC, datetime

from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=254, unique=True, index=True)
    password_hash: str = Field(max_length=255)
    failed_login_attempts: int = Field(default=0, ge=0)
    locked_until: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    refresh_tokens: list["RefreshToken"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    password_reset_tokens: list["PasswordResetToken"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


from src.models.token import PasswordResetToken, RefreshToken  # noqa: E402, F401

User.model_rebuild()
