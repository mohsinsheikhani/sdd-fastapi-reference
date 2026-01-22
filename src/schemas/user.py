import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
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
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    created_at: datetime
