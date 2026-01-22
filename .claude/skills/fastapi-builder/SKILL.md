---
name: fastapi-builder
description: |
  Build production-ready FastAPI REST APIs with SQLModel ORM, type-safe CRUD operations. Handles project initialization, database integration with Neon PostgreSQL, JWT authentication, pytest with TDD workflow, error handling, and Docker deployment. This skill should be used when building REST APIs with database backends, implementing CRUD endpoints with proper validation, setting up FastAPI projects with SQLModel and Neon, or creating type-safe APIs with comprehensive testing. NOT when building simple CLI scripts, or data processing pipelines without APIs.
---

# FastAPI Builder

Build production-ready FastAPI applications with official best practices.

## Before Implementation

Gather context to ensure successful implementation:

| Source               | Gather                                                                    |
| -------------------- | ------------------------------------------------------------------------- |
| **Codebase**         | Existing project structure, current dependencies, coding patterns         |
| **Conversation**     | User's specific requirements, features needed, scale expectations         |
| **Skill References** | FastAPI patterns from `references/` (routing, auth, database, deployment) |
| **User Guidelines**  | Project conventions, team standards, existing infrastructure              |

Ensure all required context is gathered before implementing.
Only ask user for THEIR specific requirements (domain expertise is in this skill).

---

## Clarifications

Ask about the user's specific project requirements:

### 1. Project Type

| Type               | Description                                  | Use When                   |
| ------------------ | -------------------------------------------- | -------------------------- |
| **Hello World**    | Minimal API with basic routing               | Learning, proof of concept |
| **REST API**       | Standard CRUD API with database              | Most common use case       |
| **Production API** | Full-featured with auth, testing, deployment | Production-ready system    |

### 2. Key Features

Identify which features the project needs:

- **Authentication**: OAuth2 + JWT, API keys, or none
- **Database**: SQLAlchemy ORM, raw SQL, or none
- **File Operations**: File uploads/downloads
- **Background Tasks**: Async task processing
- **WebSockets**: Real-time communication
- **CORS**: Cross-origin requests

### 3. Scale Requirements

| Scale         | Characteristics                        |
| ------------- | -------------------------------------- |
| **Prototype** | Single file, minimal dependencies      |
| **Small**     | Multiple files, basic structure        |
| **Medium**    | Modular structure, organized routers   |
| **Large**     | Full architecture, microservices-ready |

### 4. Deployment Target

- **Local development** (fastapi dev)
- **Docker container** (Dockerfile + docker-compose)
- **Production server** (Uvicorn + Gunicorn workers)

---

## Implementation Workflow

### Phase 1: Initialize Project

**For New Projects with uv:**

```bash
# Initialize with uv (modern approach)
uv init project_name
cd project_name
source .venv/bin/activate  # Unix
# .venv\Scripts\activate   # Windows

# Add dependencies
uv add "fastapi[standard]"
uv add --dev pytest pytest-asyncio httpx

# For database projects
uv add sqlmodel

# Run development server
uv run uvicorn main:app --reload
```

**Alternatively, use script:**

```bash
bash scripts/init-project.sh <project-name> <type>
```

**For Existing Projects:**

- Analyze current structure
- Identify integration points
- Plan incremental additions

### Phase 2: Core Application

Follow FastAPI's official patterns:

1. **Create FastAPI app** with metadata
2. **Define routers** for organized endpoints
3. **Implement path operations** with proper types
4. **Add dependencies** for shared logic
5. **Configure middleware** as needed

See `references/core-patterns.md` for implementation details.

### Phase 3: Add Features

Implement features based on requirements:

| Feature        | Reference                           | Key Components                    |
| -------------- | ----------------------------------- | --------------------------------- |
| Authentication | `references/auth-patterns.md`       | OAuth2, JWT, password hashing     |
| Database       | `references/database-patterns.md`   | SQLModel, sessions, Neon, CRUD    |
| Testing        | `references/testing-patterns.md`    | TestClient, pytest, TDD, fixtures |
| Deployment     | `references/deployment-patterns.md` | Docker, Uvicorn, health checks    |

### Phase 4: Production Readiness

Ensure production quality:

1. **Error handling** - Custom exception handlers
2. **Logging** - Structured logging setup
3. **Security** - CORS, rate limiting, input validation
4. **Documentation** - Enhanced OpenAPI metadata
5. **Health checks** - Readiness and liveness endpoints

See `references/production-checklist.md` for complete list.

---

## Project Structure Templates

Use appropriate structure for project scale:

### Prototype (Single File)

```
app.py              # All code in one file
requirements.txt    # Dependencies
```

### Small Project

```
app/
├── main.py         # FastAPI app + routes
├── models.py       # Pydantic models
├── database.py     # DB connection
└── config.py       # Configuration
requirements.txt
```

### Medium Project

```
app/
├── main.py         # FastAPI app initialization
├── api/
│   └── v1/
│       ├── endpoints/    # Route modules
│       └── deps.py       # Dependencies
├── core/
│   ├── config.py         # Settings
│   └── security.py       # Auth logic
├── db/
│   ├── base.py           # SQLAlchemy base
│   └── session.py        # DB session
├── models/               # SQLAlchemy models
└── schemas/              # Pydantic schemas
requirements.txt
Dockerfile
```

### Large/Production Project

```
app/
├── main.py
├── api/
│   ├── deps.py
│   └── v1/
│       ├── api.py        # Route aggregation
│       └── endpoints/    # Individual route files
├── core/
│   ├── config.py
│   ├── security.py
│   └── logging.py
├── db/
│   ├── base.py
│   ├── session.py
│   └── init_db.py
├── models/               # SQLAlchemy models
├── schemas/              # Pydantic schemas
├── crud/                 # CRUD operations
├── services/             # Business logic
├── middleware/           # Custom middleware
└── tests/
    ├── conftest.py
    ├── test_api.py
    └── test_services.py
requirements.txt
requirements-dev.txt
Dockerfile
docker-compose.yml
.env.example
alembic.ini
pytest.ini
```

See `assets/templates/` for complete project templates.

---

## Critical Best Practices

**MUST follow these non-negotiable patterns:**

1. **Type Hints Everywhere**: All path/query parameters, function signatures, and return types MUST have type hints
2. **Always Return Dictionaries**: Endpoints MUST return dictionaries (or Pydantic models), NEVER None
3. **Descriptive Function Names**: Function names MUST match endpoint purpose (e.g., `get_user_by_id`, not `get_user`)
4. **Request/Response Separation**: Define separate Pydantic models for input (`UserCreate`) and output (`User`)
5. **Field Constraints**: Use `Field()` with validation (min/max, regex, etc.)
6. **Validation Errors**: Understand 422 (Pydantic validation failure) vs 400 (business logic error)
7. **Status Codes**: Use `status` module constants, proper codes (201 for create, 204 for delete, 404 for not found)
8. **HTTPException**: Always use for client (4xx) and server (5xx) errors with descriptive detail
9. **Depends Pattern**: Use `Depends()` for shared logic, `lru_cache` for config, `yield` for cleanup
10. **Configuration**: Use `pydantic-settings` BaseSettings, .env files, .gitignore secrets, cached injection

---

## Standards

### Code Quality

**Type Annotations**

- All functions MUST have complete type hints
- Use Pydantic models for request/response validation
- Leverage FastAPI's automatic validation

**Async/Await**

- Use `async def` for I/O-bound operations
- Use regular `def` for CPU-bound operations
- Don't mix sync and async unnecessarily

**Dependency Injection**

- Use `Depends()` for shared logic
- Inject database sessions, not global connections
- Create reusable dependencies
- Use `lru_cache` for cached dependencies (e.g., settings)

### Security

**Authentication**

- Use OAuth2 with Password (and hashing), Bearer with JWT tokens
- Hash passwords with Argon2 or bcrypt
- Implement token expiration and refresh
- Validate scopes for authorization

**Input Validation**

- Rely on Pydantic models for automatic validation
- Use `Field()` with constraints (min/max, regex)
- Validate file uploads (size, type)

**Security Headers**

- Configure CORS properly (don't use `allow_origins=["*"]` in production)
- Add security middleware for headers
- Implement rate limiting

See `references/security-best-practices.md` for complete guide.

### Database

**SQLModel Patterns (Modern Approach)**

- Use SQLModel for table definitions (combines SQLAlchemy + Pydantic)
- Use dependency injection for sessions with `yield`
- Session management: `get_db()` dependency that yields and closes
- Support Neon (PostgreSQL) connections with connection pooling
- Proper CRUD operations with type hints

**Query Safety**

- Use SQLModel/ORM queries, not raw SQL (prevents injection)
- Implement pagination for list endpoints
- Add database indexes for performance
- Always handle not-found cases (404 when resource missing)

### Testing

**TDD Workflow (Red-Green-Refactor)**

1. **Red**: Write failing test first
2. **Green**: Implement minimal code to pass
3. **Refactor**: Improve code quality

**Coverage Requirements**

- Test all endpoints (happy path + error cases)
- Use TestClient for integration tests
- Mock external dependencies
- Aim for >80% coverage

**Test Organization**

- Use pytest fixtures in conftest.py for setup
- Organize by feature/endpoint
- Include test data factories
- Test validation errors (422 and 400)
- Test authentication and authorization

### Documentation

**API Metadata**

- Set title, version, description in FastAPI()
- Add tags to organize endpoints
- Include contact and license info

**Endpoint Documentation**

- Add docstrings to path operations
- Use `response_model` for clear contracts
- Document error responses with `responses` parameter

---

## Validation Checklist

Before considering implementation complete:

### Functionality

- [ ] All required endpoints implemented
- [ ] Request/response models defined with Pydantic
- [ ] Proper HTTP methods used (GET, POST, PUT, DELETE, PATCH)
- [ ] Error handling for invalid inputs
- [ ] Success and error responses documented

### Security

- [ ] Authentication implemented if required
- [ ] Authorization/scopes configured properly
- [ ] Passwords hashed (Argon2/bcrypt, never plaintext)
- [ ] CORS configured appropriately
- [ ] Input validation on all endpoints
- [ ] No sensitive data in logs

### Database (if applicable)

- [ ] SQLModel table definitions created
- [ ] Database session managed properly (dependency injection with yield)
- [ ] Connection pooling configured (especially for Neon/PostgreSQL)
- [ ] Indexes added for query performance
- [ ] CRUD operations with proper type hints
- [ ] Not-found cases handled (404 errors)

### Testing

- [ ] TestClient setup
- [ ] Unit tests for core logic
- [ ] Integration tests for endpoints
- [ ] Test coverage >80%
- [ ] Tests pass: `pytest`

### Deployment

- [ ] Dependencies in requirements.txt
- [ ] Environment variables in .env.example
- [ ] Dockerfile created (if containerized)
- [ ] Health check endpoint implemented
- [ ] Production server configured (Uvicorn/Gunicorn)

### Documentation

- [ ] OpenAPI metadata configured (title, version, description)
- [ ] Endpoints tagged and organized
- [ ] Interactive docs accessible at /docs
- [ ] ReDoc accessible at /redoc
- [ ] README with setup instructions

### Code Quality

- [ ] Type hints on all functions
- [ ] Async/await used appropriately
- [ ] No hardcoded secrets (use environment variables)
- [ ] Logging configured
- [ ] Code follows project structure conventions

---

## Quick Reference

### Essential Patterns

**Basic App**

```python
from fastapi import FastAPI

app = FastAPI(title="My API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

**With Dependencies**

```python
from fastapi import Depends

async def verify_token(token: str = Header()):
    if token != "secret":
        raise HTTPException(status_code=401)

@app.get("/items", dependencies=[Depends(verify_token)])
async def get_items():
    return [{"item": "foo"}]
```

**With Database (SQLModel)**

```python
from sqlmodel import Session, select
from typing import Annotated

def get_db():
    with Session(engine) as session:
        yield session

@app.get("/users/{user_id}")
def get_user_by_id(user_id: int, db: Annotated[Session, Depends(get_db)]) -> dict:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "username": user.username}  # Always return dict
```

**Run Development Server**

```bash
# Modern approach with uv
uv run uvicorn main:app --reload

# Or traditional
fastapi dev main.py
```

**Run Production Server**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

For detailed patterns, see references/ directory.

---

## References

| File                                    | Content                                                                                    |
| --------------------------------------- | ------------------------------------------------------------------------------------------ |
| `references/core-patterns.md`           | App initialization, routing, path operations, dependencies, validation errors (422 vs 400) |
| `references/auth-patterns.md`           | OAuth2 + JWT implementation, password hashing, scopes                                      |
| `references/database-patterns.md`       | SQLModel integration, sessions, Neon connections, CRUD patterns with type hints            |
| `references/testing-patterns.md`        | TestClient usage, TDD workflow (red-green-refactor), pytest fixtures in conftest.py        |
| `references/deployment-patterns.md`     | Docker setup, Uvicorn configuration, production deployment                                 |
| `references/security-best-practices.md` | CORS, rate limiting, input validation, security headers                                    |
| `references/production-checklist.md`    | Complete production readiness checklist                                                    |
| `references/api-examples.md`            | Real-world API examples from simple to complex                                             |

## Scripts

| Script                    | Purpose                                              |
| ------------------------- | ---------------------------------------------------- |
| `scripts/init-project.sh` | Initialize new FastAPI project with chosen structure |
| `scripts/setup-auth.sh`   | Add OAuth2 + JWT authentication to existing project  |
| `scripts/setup-db.sh`     | Configure SQLAlchemy database integration            |

## Assets

| Asset                           | Purpose                          |
| ------------------------------- | -------------------------------- |
| `assets/templates/hello-world/` | Minimal single-file FastAPI app  |
| `assets/templates/rest-api/`    | Standard REST API structure      |
| `assets/templates/production/`  | Full production-ready structure  |
| `assets/Dockerfile`             | Production Dockerfile template   |
| `assets/docker-compose.yml`     | Local development docker-compose |
| `assets/.env.example`           | Environment variables template   |
