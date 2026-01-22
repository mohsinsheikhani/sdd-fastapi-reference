#!/bin/bash

# Initialize a new FastAPI project with chosen structure using uv
# Usage: bash init-project.sh <project-name> <type>
# Types: hello-world, rest-api, production

set -e

PROJECT_NAME="$1"
PROJECT_TYPE="${2:-rest-api}"  # Default to rest-api

if [ -z "$PROJECT_NAME" ]; then
    echo "Error: Project name required"
    echo "Usage: bash init-project.sh <project-name> <type>"
    echo "Types: hello-world, rest-api, production"
    exit 1
fi

if [[ "$PROJECT_TYPE" != "hello-world" && "$PROJECT_TYPE" != "rest-api" && "$PROJECT_TYPE" != "production" ]]; then
    echo "Error: Invalid project type '$PROJECT_TYPE'"
    echo "Valid types: hello-world, rest-api, production"
    exit 1
fi

echo "Creating FastAPI project: $PROJECT_NAME (type: $PROJECT_TYPE) using uv"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Install it first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Initialize project with uv
uv init "$PROJECT_NAME"
cd "$PROJECT_NAME"

# Initialize based on type
case "$PROJECT_TYPE" in
    "hello-world")
        echo "Initializing hello-world project..."

        # Add dependencies
        uv add "fastapi[standard]"

        # Create main.py
        cat > main.py <<'EOF'
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root() -> dict:
    return {"message": "Hello World"}
EOF

        echo "✓ Hello world project created"
        echo ""
        echo "To run:"
        echo "  cd $PROJECT_NAME"
        echo "  source .venv/bin/activate  # or .venv\\Scripts\\activate on Windows"
        echo "  uv run uvicorn main:app --reload"
        ;;

    "rest-api")
        echo "Initializing REST API project..."

        # Add dependencies
        uv add "fastapi[standard]"
        uv add sqlmodel
        uv add --dev pytest pytest-asyncio httpx

        # Create directory structure
        mkdir -p app

        # Create main.py
        cat > app/main.py <<'EOF'
from fastapi import FastAPI

app = FastAPI(
    title="My API",
    version="1.0.0",
)

@app.get("/")
async def root() -> dict:
    return {"message": "Welcome to My API"}

@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy"}
EOF

        # Create models.py with SQLModel
        cat > app/models.py <<'EOF'
from sqlmodel import Field, SQLModel
from typing import Optional

class ItemBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(gt=0)

class Item(ItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class ItemCreate(ItemBase):
    pass

class ItemRead(ItemBase):
    id: int
EOF

        # Create database.py with SQLModel
        cat > app/database.py <<'EOF'
from sqlmodel import Session, create_engine
from typing import Annotated
from fastapi import Depends

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=True
)

def get_db():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_db)]
EOF

        # Create config.py
        cat > app/config.py <<'EOF'
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "My API"
    debug: bool = True
    database_url: str = "sqlite:///./app.db"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
EOF

        # Create .env.example
        cat > .env.example <<'EOF'
APP_NAME=My API
DEBUG=true
DATABASE_URL=sqlite:///./app.db
EOF

        # Create .gitignore
        cat > .gitignore <<'EOF'
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv
.env
*.db
*.log
.DS_Store
.idea/
.vscode/
.pytest_cache/
.coverage
htmlcov/
EOF

        # Create pytest.ini
        cat > pytest.ini <<'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=app --cov-report=term-missing
EOF

        # Create tests directory with conftest.py
        mkdir -p tests
        cat > tests/conftest.py <<'EOF'
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from app.main import app
from app.database import get_db

DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="function")
def session():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def client(session: Session):
    def get_session_override():
        return session
    app.dependency_overrides[get_db] = get_session_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
EOF

        cat > tests/test_main.py <<'EOF'
def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to My API"}

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
EOF

        echo "✓ REST API project created with SQLModel and tests"
        echo ""
        echo "To run:"
        echo "  cd $PROJECT_NAME"
        echo "  source .venv/bin/activate  # or .venv\\Scripts\\activate on Windows"
        echo "  cp .env.example .env"
        echo "  uv run uvicorn app.main:app --reload"
        echo ""
        echo "To run tests:"
        echo "  uv run pytest"
        ;;

    "production")
        echo "Initializing production project..."

        # Add dependencies
        uv add "fastapi[standard]"
        uv add sqlmodel pydantic-settings
        uv add "passlib[argon2]" "python-jose[cryptography]"
        uv add --dev pytest pytest-asyncio pytest-cov httpx

        # Create directory structure
        mkdir -p app/{api/v1/endpoints,core,crud,db,models,schemas}
        mkdir -p tests

        # Create main.py
        cat > app/main.py <<'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api.v1.api import api_router
from sqlmodel import SQLModel
from app.db.session import engine

settings = get_settings()

# Create database tables
SQLModel.metadata.create_all(engine)

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy"}
EOF

        # Create core/config.py
        cat > app/core/config.py <<'EOF'
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "My Production API"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str
    DATABASE_URL: str
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
EOF

        # Create db/session.py
        cat > app/db/session.py <<'EOF'
from sqlmodel import Session, create_engine
from typing import Annotated
from fastapi import Depends
from app.core.config import get_settings

settings = get_settings()

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG
)

def get_db():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_db)]
EOF

        # Create api/v1/api.py
        cat > app/api/v1/api.py <<'EOF'
from fastapi import APIRouter

api_router = APIRouter()

# Include your endpoint routers here
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(users.router, prefix="/users", tags=["users"])
EOF

        # Create .env.example
        cat > .env.example <<'EOF'
APP_NAME=My Production API
DEBUG=false
API_V1_PREFIX=/api/v1
SECRET_KEY=generate-with-openssl-rand-hex-32
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
# For Neon (serverless PostgreSQL):
# DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require
CORS_ORIGINS=["http://localhost:3000"]
EOF

        # Create pytest.ini
        cat > pytest.ini <<'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
EOF

        # Create tests/conftest.py
        cat > tests/conftest.py <<'EOF'
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from app.main import app
from app.db.session import get_db

DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="function")
def session():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def client(session: Session):
    def get_session_override():
        return session
    app.dependency_overrides[get_db] = get_session_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
EOF

        # Create tests/test_main.py
        cat > tests/test_main.py <<'EOF'
def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
EOF

        # Create Dockerfile with uv
        cat > Dockerfile <<'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy application code
COPY ./app ./app

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

        # Create docker-compose.yml
        cat > docker-compose.yml <<'EOF'
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/dbname
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
    volumes:
      - ./app:/app/app

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=dbname
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
EOF

        # Create .gitignore
        cat > .gitignore <<'EOF'
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv
.env
*.db
*.log
.DS_Store
.idea/
.vscode/
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
EOF

        # Create README.md
        cat > README.md <<'EOF'
# My Production API

FastAPI production application with SQLModel and modern tooling.

## Setup

1. Activate virtual environment:
   ```bash
   source .venv/bin/activate  # Unix
   # .venv\Scripts\activate   # Windows
   ```

2. Copy environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your values (generate SECRET_KEY with: openssl rand -hex 32)
   ```

3. Run development server:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

4. Or use Docker:
   ```bash
   docker-compose up
   ```

## Documentation

- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## Testing

```bash
uv run pytest
uv run pytest --cov=app --cov-report=html  # With coverage report
```

## Database

This project uses SQLModel with support for:
- SQLite (development)
- PostgreSQL (production)
- Neon (serverless PostgreSQL)

Update DATABASE_URL in .env for your database.
EOF

        echo "✓ Production project created with SQLModel, uv, and tests"
        echo ""
        echo "To run:"
        echo "  cd $PROJECT_NAME"
        echo "  source .venv/bin/activate  # or .venv\\Scripts\\activate on Windows"
        echo "  cp .env.example .env"
        echo "  # Edit .env with your SECRET_KEY (generate with: openssl rand -hex 32)"
        echo "  uv run uvicorn app.main:app --reload"
        echo ""
        echo "To run tests:"
        echo "  uv run pytest"
        echo ""
        echo "Access docs at: http://localhost:8000/api/v1/docs"
        ;;
esac

echo ""
echo "Project '$PROJECT_NAME' initialized successfully!"
echo "Visit http://127.0.0.1:8000/docs for interactive API documentation"
