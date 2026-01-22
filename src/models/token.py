import uuid
from datetime import UTC, datetime

from sqlmodel import Field, Relationship, SQLModel


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(max_length=64)
    expires_at: datetime
    revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    user: "User" = Relationship(back_populates="refresh_tokens")


class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_tokens"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(max_length=64)
    expires_at: datetime
    used: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    user: "User" = Relationship(back_populates="password_reset_tokens")


from src.models.user import User  # noqa: E402, F401

RefreshToken.model_rebuild()
PasswordResetToken.model_rebuild()
