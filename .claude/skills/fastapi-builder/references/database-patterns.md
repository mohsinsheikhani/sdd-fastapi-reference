# FastAPI Database Integration with SQLModel

Modern database patterns using SQLModel (combines SQLAlchemy + Pydantic) for FastAPI.

## Overview

SQLModel is the modern approach for FastAPI database operations, combining:
- **SQLAlchemy ORM**: Powerful database toolkit
- **Pydantic validation**: Automatic data validation
- **Type hints**: Full type safety and IDE support
- **Single model definition**: One class for both table and validation

## Installation

```bash
# Using uv (recommended)
uv add sqlmodel

# For PostgreSQL (including Neon)
uv add "psycopg2-binary"  # or psycopg[binary]

# For async support
uv add "sqlmodel[async]"
```

## SQLModel Basics

### Table Definition

```python
# app/models/user.py
from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    """User table model"""
    __tablename__ = "users"  # Optional: customize table name

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    username: str = Field(unique=True, index=True, min_length=3, max_length=50)
    hashed_password: str
    full_name: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
```

### Request/Response Models

SQLModel makes it easy to separate table models from API models:

```python
# app/schemas/user.py
from sqlmodel import SQLModel, Field
from typing import Optional
from pydantic import EmailStr

# Base schema with shared fields
class UserBase(SQLModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    full_name: Optional[str] = None

# For creating users (input)
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=100)

# For updating users (input)
class UserUpdate(SQLModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    full_name: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8)
    is_active: Optional[bool] = None

# For reading users (output)
class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime

# Internal model (includes sensitive data)
class UserInDB(UserRead):
    hashed_password: str
```

## Database Configuration

### For SQLite (Development)

```python
# app/db/session.py
from sqlmodel import Session, create_engine
from typing import Annotated
from fastapi import Depends
from app.core.config import get_settings

settings = get_settings()

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite only
    echo=settings.DEBUG  # Log SQL queries in debug mode
)

def get_db():
    """Dependency for database sessions with automatic cleanup"""
    with Session(engine) as session:
        yield session

# Type annotation for dependency injection
SessionDep = Annotated[Session, Depends(get_db)]
```

### For PostgreSQL / Neon (Production)

```python
# app/db/session.py
from sqlmodel import Session, create_engine
from typing import Annotated
from fastapi import Depends
from app.core.config import get_settings

settings = get_settings()

# Regular PostgreSQL
# DATABASE_URL = "postgresql://user:password@localhost:5432/dbname"

# Neon (serverless PostgreSQL) - recommended for production
# DATABASE_URL = "postgresql://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require"

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # Verify connections before using
    pool_size=10,            # Number of connections in pool
    max_overflow=20,         # Additional connections when pool is full
    pool_recycle=3600,       # Recycle connections after 1 hour
    echo=settings.DEBUG
)

def get_db():
    """Dependency for database sessions with automatic cleanup"""
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_db)]
```

### Configuration with pydantic-settings

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "My API"
    DEBUG: bool = False
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    class Config:
        env_file = ".env"

@lru_cache  # Cache settings to avoid reading .env multiple times
def get_settings() -> Settings:
    return Settings()
```

```bash
# .env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
# Or for Neon:
# DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

## CRUD Operations

### Create Operations

```python
# app/crud/user.py
from sqlmodel import Session, select
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

def create_user(session: Session, user: UserCreate) -> User:
    """Create a new user"""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
```

### Read Operations

```python
# app/crud/user.py
from sqlmodel import Session, select
from typing import Optional

def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return session.get(User, user_id)

def get_user_by_email(session: Session, email: str) -> Optional[User]:
    """Get user by email"""
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()

def get_users(session: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """Get list of users with pagination"""
    statement = select(User).offset(skip).limit(limit)
    return session.exec(statement).all()
```

### Update Operations

```python
# app/crud/user.py
from sqlmodel import Session
from app.schemas.user import UserUpdate
from app.core.security import get_password_hash

def update_user(session: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """Update user"""
    db_user = session.get(User, user_id)
    if not db_user:
        return None

    # Update only provided fields
    update_data = user_update.model_dump(exclude_unset=True)

    # Hash password if provided
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    for key, value in update_data.items():
        setattr(db_user, key, value)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
```

### Delete Operations

```python
# app/crud/user.py
from sqlmodel import Session

def delete_user(session: Session, user_id: int) -> bool:
    """Delete user (hard delete)"""
    db_user = session.get(User, user_id)
    if not db_user:
        return False
    session.delete(db_user)
    session.commit()
    return True

def soft_delete_user(session: Session, user_id: int) -> Optional[User]:
    """Soft delete user (mark as inactive)"""
    db_user = session.get(User, user_id)
    if not db_user:
        return None
    db_user.is_active = False
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
```

## API Endpoints with SQLModel

### CRUD Endpoints

```python
# app/api/v1/endpoints/users.py
from fastapi import APIRouter, HTTPException, status
from sqlmodel import Session
from app.db.session import SessionDep
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.crud import user as crud_user

router = APIRouter()

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, session: SessionDep) -> dict:
    """Create new user"""
    # Check if user already exists
    db_user = crud_user.get_user_by_email(session, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    created_user = crud_user.create_user(session, user)
    # Always return dict, never None
    return {
        "id": created_user.id,
        "email": created_user.email,
        "username": created_user.username,
        "full_name": created_user.full_name,
        "is_active": created_user.is_active,
        "created_at": created_user.created_at,
    }

@router.get("/{user_id}", response_model=UserRead)
def get_user_by_id(user_id: int, session: SessionDep) -> dict:
    """Get user by ID"""
    db_user = crud_user.get_user_by_id(session, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )
    # Always return dict
    return {
        "id": db_user.id,
        "email": db_user.email,
        "username": db_user.username,
        "full_name": db_user.full_name,
        "is_active": db_user.is_active,
        "created_at": db_user.created_at,
    }

@router.get("/", response_model=list[UserRead])
def get_users_list(skip: int = 0, limit: int = 100, session: SessionDep) -> list[dict]:
    """Get paginated list of users"""
    users = crud_user.get_users(session, skip=skip, limit=limit)
    # Always return list of dicts
    return [
        {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "created_at": user.created_at,
        }
        for user in users
    ]

@router.put("/{user_id}", response_model=UserRead)
def update_user_by_id(user_id: int, user_update: UserUpdate, session: SessionDep) -> dict:
    """Update user"""
    db_user = crud_user.update_user(session, user_id, user_update)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )
    # Always return dict
    return {
        "id": db_user.id,
        "email": db_user.email,
        "username": db_user.username,
        "full_name": db_user.full_name,
        "is_active": db_user.is_active,
        "created_at": db_user.created_at,
    }

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_id(user_id: int, session: SessionDep) -> None:
    """Delete user"""
    success = crud_user.delete_user(session, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )
    # 204 returns no content
```

## Relationships

### One-to-Many

```python
# app/models/user.py
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)

    # Relationship to items
    items: List["Item"] = Relationship(back_populates="owner")

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: Optional[str] = None
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")

    # Relationship to user
    owner: Optional[User] = Relationship(back_populates="items")
```

### Many-to-Many

```python
# app/models/course.py
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List

class StudentCourseLink(SQLModel, table=True):
    """Link table for many-to-many relationship"""
    student_id: Optional[int] = Field(default=None, foreign_key="student.id", primary_key=True)
    course_id: Optional[int] = Field(default=None, foreign_key="course.id", primary_key=True)

class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    courses: List["Course"] = Relationship(back_populates="students", link_model=StudentCourseLink)

class Course(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str

    students: List[Student] = Relationship(back_populates="courses", link_model=StudentCourseLink)
```

## Database Initialization

```python
# app/db/init_db.py
from sqlmodel import SQLModel
from app.db.session import engine
from app.models.user import User
from app.models.item import Item

def create_db_and_tables():
    """Create all tables"""
    SQLModel.metadata.create_all(engine)

def init_db():
    """Initialize database with default data"""
    create_db_and_tables()
    # Add any default data here

# app/main.py
from fastapi import FastAPI
from app.db.init_db import create_db_and_tables

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
```

## Best Practices

### Always Use Type Hints

```python
# ✅ Good: Full type hints
def get_user(session: Session, user_id: int) -> Optional[User]:
    return session.get(User, user_id)

# ❌ Bad: No type hints
def get_user(session, user_id):
    return session.get(User, user_id)
```

### Always Return Dictionaries from Endpoints

```python
# ✅ Good: Returns dict
@app.get("/users/{user_id}")
def get_user(user_id: int, session: SessionDep) -> dict:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "username": user.username}

# ❌ Bad: Returns None or model directly
@app.get("/users/{user_id}")
def get_user(user_id: int, session: SessionDep):
    return session.get(User, user_id)  # Could return None!
```

### Use SessionDep for Consistency

```python
from typing import Annotated
from fastapi import Depends
from sqlmodel import Session

# Define once
SessionDep = Annotated[Session, Depends(get_db)]

# Use everywhere
@app.get("/users")
def get_users(session: SessionDep) -> list[dict]:
    ...
```

### Handle Not Found Cases

```python
# ✅ Good: Explicit 404 handling
@app.get("/users/{user_id}")
def get_user(user_id: int, session: SessionDep) -> dict:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    return {"id": user.id, "username": user.username}

# ❌ Bad: No error handling
@app.get("/users/{user_id}")
def get_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    return user  # Will return None if not found
```

### Use Indexes for Performance

```python
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)  # Index for lookups
    username: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)  # Index for sorting
```

### Implement Pagination

```python
@app.get("/users")
def get_users(
    skip: int = 0,
    limit: int = 100,
    session: SessionDep
) -> dict:
    """Get paginated users"""
    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()

    # Get total count
    count_statement = select(func.count()).select_from(User)
    total = session.exec(count_statement).one()

    return {
        "items": [{"id": u.id, "username": u.username} for u in users],
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

## Neon (Serverless PostgreSQL) Setup

Neon is a modern serverless PostgreSQL service with excellent FastAPI integration:

### Connection String

```bash
# .env
DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require
```

### Configuration for Neon

```python
# app/db/session.py
from sqlmodel import create_engine

# Neon-optimized configuration
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,        # Important for serverless
    pool_size=5,               # Smaller pool for serverless
    max_overflow=10,
    pool_recycle=300,          # 5 minutes (shorter for serverless)
    connect_args={
        "sslmode": "require",  # Neon requires SSL
        "connect_timeout": 10,
    }
)
```

### Benefits of Neon

- **Serverless**: Auto-scaling, pay per use
- **Instant branching**: Create database copies instantly
- **Connection pooling**: Built-in pooling
- **Generous free tier**: Perfect for development

## Testing with SQLModel

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from app.main import app
from app.db.session import get_db

DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="function")
def session():
    """Create test database session"""
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def client(session: Session):
    """Create test client with database override"""
    def get_session_override():
        return session

    app.dependency_overrides[get_db] = get_session_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# tests/test_users.py
def test_create_user(client):
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "username": "test", "password": "password123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
```

## Security Checklist

- [ ] Use SQLModel/ORM queries, not raw SQL
- [ ] Never use string formatting in queries
- [ ] Validate all inputs with Pydantic models
- [ ] Use connection pooling
- [ ] Set appropriate pool sizes
- [ ] Implement proper error handling
- [ ] Use yield dependencies for session management
- [ ] Add indexes for frequently queried fields
- [ ] Store database credentials in environment variables
- [ ] Use SSL for database connections (especially Neon)
- [ ] Handle not-found cases explicitly (404 errors)
- [ ] Always return dictionaries from endpoints

## Common Patterns

### Transaction Management

```python
from sqlmodel import Session

def transfer_money(session: Session, from_id: int, to_id: int, amount: float):
    """Transfer money between accounts (atomic transaction)"""
    try:
        from_account = session.get(Account, from_id)
        to_account = session.get(Account, to_id)

        if not from_account or not to_account:
            raise HTTPException(status_code=404, detail="Account not found")

        if from_account.balance < amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")

        from_account.balance -= amount
        to_account.balance += amount

        session.add(from_account)
        session.add(to_account)
        session.commit()  # Both changes committed atomically

        return {"status": "success"}
    except Exception as e:
        session.rollback()
        raise
```

### Soft Deletes

```python
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None

def soft_delete(session: Session, user_id: int):
    user = session.get(User, user_id)
    if user:
        user.is_deleted = True
        user.deleted_at = datetime.utcnow()
        session.add(user)
        session.commit()

# Query only active users
def get_active_users(session: Session):
    statement = select(User).where(User.is_deleted == False)
    return session.exec(statement).all()
```

## References

- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [FastAPI SQL Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [Neon Documentation](https://neon.tech/docs)
- [Pydantic Documentation](https://docs.pydantic.dev/)
