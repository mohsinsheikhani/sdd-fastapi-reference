# FastAPI API Examples

Real-world API examples from hello world to production-level complexity.

## Level 1: Hello World

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

# Run: fastapi dev main.py
# Visit: http://127.0.0.1:8000/docs
```

## Level 2: Simple CRUD API

```python
# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Simple Todo API", version="1.0.0")

class Todo(BaseModel):
    id: int
    title: str
    completed: bool = False

# In-memory storage
todos: dict[int, Todo] = {}
next_id = 1

@app.get("/todos", response_model=List[Todo])
async def get_todos():
    """Get all todos."""
    return list(todos.values())

@app.get("/todos/{todo_id}", response_model=Todo)
async def get_todo(todo_id: int):
    """Get todo by ID."""
    if todo_id not in todos:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todos[todo_id]

@app.post("/todos", response_model=Todo, status_code=201)
async def create_todo(todo: Todo):
    """Create new todo."""
    global next_id
    todo.id = next_id
    todos[next_id] = todo
    next_id += 1
    return todo

@app.put("/todos/{todo_id}", response_model=Todo)
async def update_todo(todo_id: int, todo: Todo):
    """Update todo."""
    if todo_id not in todos:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo.id = todo_id
    todos[todo_id] = todo
    return todo

@app.delete("/todos/{todo_id}", status_code=204)
async def delete_todo(todo_id: int):
    """Delete todo."""
    if todo_id not in todos:
        raise HTTPException(status_code=404, detail="Todo not found")
    del todos[todo_id]
```

## Level 3: API with Database (SQLAlchemy)

```python
# Project Structure:
# app/
# ├── main.py
# ├── database.py
# ├── models.py
# ├── schemas.py
# └── crud.py

# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# models.py
from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base

class TodoModel(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# schemas.py
from pydantic import BaseModel, Field
from datetime import datetime

class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    completed: bool = False

class TodoUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    completed: bool | None = None

class Todo(BaseModel):
    id: int
    title: str
    description: str | None
    completed: bool
    created_at: datetime

    class Config:
        from_attributes = True

# crud.py
from sqlalchemy.orm import Session
from models import TodoModel
from schemas import TodoCreate, TodoUpdate

def get_todos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(TodoModel).offset(skip).limit(limit).all()

def get_todo(db: Session, todo_id: int):
    return db.query(TodoModel).filter(TodoModel.id == todo_id).first()

def create_todo(db: Session, todo: TodoCreate):
    db_todo = TodoModel(**todo.model_dump())
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

def update_todo(db: Session, todo_id: int, todo: TodoUpdate):
    db_todo = get_todo(db, todo_id)
    if not db_todo:
        return None
    update_data = todo.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_todo, field, value)
    db.commit()
    db.refresh(db_todo)
    return db_todo

def delete_todo(db: Session, todo_id: int):
    db_todo = get_todo(db, todo_id)
    if db_todo:
        db.delete(db_todo)
        db.commit()
        return True
    return False

# main.py
from typing import Annotated, List
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from schemas import Todo, TodoCreate, TodoUpdate
import crud

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Todo API with Database", version="2.0.0")

@app.get("/todos", response_model=List[Todo])
async def read_todos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_todos(db, skip=skip, limit=limit)

@app.get("/todos/{todo_id}", response_model=Todo)
async def read_todo(todo_id: int, db: Session = Depends(get_db)):
    db_todo = crud.get_todo(db, todo_id=todo_id)
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return db_todo

@app.post("/todos", response_model=Todo, status_code=201)
async def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    return crud.create_todo(db, todo=todo)

@app.put("/todos/{todo_id}", response_model=Todo)
async def update_todo(todo_id: int, todo: TodoUpdate, db: Session = Depends(get_db)):
    db_todo = crud.update_todo(db, todo_id=todo_id, todo=todo)
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return db_todo

@app.delete("/todos/{todo_id}", status_code=204)
async def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    if not crud.delete_todo(db, todo_id=todo_id):
        raise HTTPException(status_code=404, detail="Todo not found")
```

## Level 4: API with Authentication (OAuth2 + JWT)

```python
# Project Structure:
# app/
# ├── main.py
# ├── auth.py
# ├── models.py
# ├── schemas.py
# └── database.py

# auth.py
from datetime import datetime, timedelta, UTC
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

SECRET_KEY = "your-secret-key-here"  # Use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)]
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(UserModel).filter(UserModel.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# main.py
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from auth import (
    Token, get_password_hash, verify_password,
    create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from database import get_db
from models import UserModel, TodoModel
from schemas import UserCreate, User, TodoCreate, Todo

app = FastAPI(title="Secured Todo API", version="3.0.0")

# Authentication endpoints
@app.post("/register", response_model=User)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register new user."""
    # Check if user exists
    if db.query(UserModel).filter(UserModel.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(UserModel).filter(UserModel.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    db_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    """Login and get access token."""
    user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Protected endpoints
@app.get("/users/me", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Get current user."""
    return current_user

@app.get("/todos", response_model=List[Todo])
async def read_todos(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Get todos for current user."""
    return db.query(TodoModel).filter(TodoModel.owner_id == current_user.id).all()

@app.post("/todos", response_model=Todo, status_code=201)
async def create_todo(
    todo: TodoCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Create todo for current user."""
    db_todo = TodoModel(**todo.model_dump(), owner_id=current_user.id)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo
```

## Level 5: Production-Ready API

This example includes:
- Modular structure with routers
- Configuration management
- Error handling
- Logging
- CORS
- Health checks
- Background tasks

```python
# Project Structure:
# app/
# ├── main.py
# ├── core/
# │   ├── config.py
# │   ├── security.py
# │   └── logging.py
# ├── api/
# │   └── v1/
# │       ├── api.py
# │       └── endpoints/
# │           ├── auth.py
# │           ├── users.py
# │           └── todos.py
# ├── crud/
# │   ├── user.py
# │   └── todo.py
# ├── db/
# │   ├── base.py
# │   └── session.py
# ├── models/
# │   ├── user.py
# │   └── todo.py
# └── schemas/
#     ├── user.py
#     └── todo.py

# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Todo API"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"

settings = Settings()

# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import engine
from app.db.base import Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down")

# api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, todos

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(todos.router, prefix="/todos", tags=["todos"])

# api/v1/endpoints/todos.py
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.schemas.user import User
from app.schemas.todo import Todo, TodoCreate, TodoUpdate
from app.crud import todo as crud_todo

router = APIRouter()

@router.get("/", response_model=List[Todo])
async def read_todos(
    skip: int = 0,
    limit: int = 100,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Get todos for current user."""
    return crud_todo.get_todos_by_user(db, user_id=current_user.id, skip=skip, limit=limit)

@router.post("/", response_model=Todo, status_code=201)
async def create_todo(
    todo: TodoCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Create todo for current user."""
    return crud_todo.create_todo(db, todo=todo, user_id=current_user.id)

@router.get("/{todo_id}", response_model=Todo)
async def read_todo(
    todo_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Get specific todo."""
    todo = crud_todo.get_todo(db, todo_id=todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if todo.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return todo

@router.put("/{todo_id}", response_model=Todo)
async def update_todo(
    todo_id: int,
    todo: TodoUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Update todo."""
    db_todo = crud_todo.get_todo(db, todo_id=todo_id)
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if db_todo.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return crud_todo.update_todo(db, todo_id=todo_id, todo=todo)

@router.delete("/{todo_id}", status_code=204)
async def delete_todo(
    todo_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Delete todo."""
    db_todo = crud_todo.get_todo(db, todo_id=todo_id)
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if db_todo.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    crud_todo.delete_todo(db, todo_id=todo_id)
```

These examples progress from simple to production-ready, demonstrating FastAPI best practices at each level.
