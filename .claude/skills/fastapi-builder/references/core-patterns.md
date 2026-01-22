# FastAPI Core Patterns

Official patterns for FastAPI application structure based on FastAPI documentation.

## Application Initialization

### Basic Application

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

### Production Application with Metadata

```python
from fastapi import FastAPI

app = FastAPI(
    title="My Production API",
    summary="A high-quality API for production use",
    description="""
    ## Features

    * **Authentication**: OAuth2 with JWT tokens
    * **Database**: SQLAlchemy ORM with PostgreSQL
    * **Documentation**: Auto-generated OpenAPI docs

    You can use **Markdown** in the description.
    """,
    version="1.0.0",
    terms_of_service="https://example.com/terms/",
    contact={
        "name": "API Support",
        "url": "https://example.com/contact",
        "email": "support@example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)
```

### Key Parameters

| Parameter | Purpose | Example |
|-----------|---------|---------|
| `title` | API name shown in docs | "My API" |
| `summary` | Brief description | "A production API" |
| `description` | Full description (supports Markdown) | Multi-line with features |
| `version` | API version | "1.0.0" |
| `docs_url` | Swagger UI path | "/docs" (default) |
| `redoc_url` | ReDoc path | "/redoc" (default) |
| `openapi_url` | OpenAPI schema path | "/openapi.json" (default) |

## Path Operations

### HTTP Methods

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items")           # Read/List
async def read_items():
    return [{"item": "foo"}]

@app.get("/items/{item_id}") # Read one
async def read_item(item_id: int):
    return {"item_id": item_id}

@app.post("/items")          # Create
async def create_item(item: Item):
    return item

@app.put("/items/{item_id}") # Update (full)
async def update_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.dict()}

@app.patch("/items/{item_id}") # Update (partial)
async def patch_item(item_id: int, item: ItemUpdate):
    return {"item_id": item_id, **item.dict(exclude_unset=True)}

@app.delete("/items/{item_id}") # Delete
async def delete_item(item_id: int):
    return {"deleted": item_id}
```

### Path Parameters

```python
from fastapi import FastAPI, Path
from typing import Annotated

app = FastAPI()

# Basic path parameter
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

# With validation
@app.get("/items/{item_id}")
async def read_item(
    item_id: Annotated[int, Path(ge=1, le=1000, description="Item ID")]
):
    return {"item_id": item_id}

# Multiple path parameters
@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(user_id: int, item_id: int):
    return {"user_id": user_id, "item_id": item_id}
```

### Query Parameters

```python
from fastapi import FastAPI, Query
from typing import Annotated

app = FastAPI()

# Optional query parameter
@app.get("/items")
async def read_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

# Required query parameter
@app.get("/items")
async def read_items(q: str):
    return {"q": q}

# With validation and metadata
@app.get("/items")
async def read_items(
    q: Annotated[str | None, Query(
        min_length=3,
        max_length=50,
        title="Query string",
        description="Search query for items",
    )] = None
):
    return {"q": q}

# Multiple values (list)
@app.get("/items")
async def read_items(tags: Annotated[list[str] | None, Query()] = None):
    return {"tags": tags}
```

### Request Body

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    price: float = Field(..., gt=0)
    tax: float | None = Field(None, ge=0)

app = FastAPI()

@app.post("/items")
async def create_item(item: Item):
    return item

# Multiple body parameters
class User(BaseModel):
    username: str
    full_name: str | None = None

@app.post("/users/items")
async def create_user_item(user: User, item: Item):
    return {"user": user, "item": item}
```

### Response Models

```python
from fastapi import FastAPI
from pydantic import BaseModel

class ItemIn(BaseModel):
    name: str
    price: float
    secret_data: str

class ItemOut(BaseModel):
    name: str
    price: float

app = FastAPI()

# Response model filters output
@app.post("/items", response_model=ItemOut)
async def create_item(item: ItemIn):
    # secret_data is NOT returned to client
    return item

# Response model with status code
@app.post("/items", response_model=ItemOut, status_code=201)
async def create_item(item: ItemIn):
    return item
```

## Dependencies

### Basic Dependencies

```python
from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()

# Simple dependency
async def verify_token(token: str = Header()):
    if token != "valid-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

@app.get("/items")
async def read_items(token: str = Depends(verify_token)):
    return {"token": token}
```

### Dependencies with Parameters

```python
from fastapi import Depends, FastAPI

def get_current_user(token: str = Header()):
    # Validate token and return user
    return {"username": "john", "id": 1}

def check_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return user

@app.get("/admin")
async def admin_only(admin: dict = Depends(check_admin)):
    return {"admin": admin}
```

### Dependencies That Don't Return Values

Use `dependencies` parameter when you need to execute dependencies but don't need their return values:

```python
from fastapi import Depends, FastAPI

async def verify_token(token: str = Header()):
    if token != "valid-token":
        raise HTTPException(status_code=401)

async def verify_key(key: str = Header(alias="X-Key")):
    if key != "valid-key":
        raise HTTPException(status_code=401)

app = FastAPI()

# Both dependencies execute, but values not passed to function
@app.get("/items", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "foo"}]
```

### Dependencies with Yield (Cleanup)

```python
from fastapi import Depends, FastAPI

def get_db():
    db = Database()
    try:
        yield db  # Dependency provides db
    finally:
        db.close()  # Cleanup after request

@app.get("/users")
async def read_users(db: Database = Depends(get_db)):
    return db.query_users()  # db automatically closed after
```

## Routers

### Creating Routers

```python
from fastapi import APIRouter

router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def read_items():
    return [{"item": "foo"}]

@router.get("/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

@router.post("/")
async def create_item(item: Item):
    return item
```

### Including Routers

```python
from fastapi import FastAPI

app = FastAPI()

# Include router
app.include_router(router)

# Include with custom prefix and tags
app.include_router(
    router,
    prefix="/api/v1",
    tags=["v1"],
)
```

### Organized Router Structure

```python
# app/api/v1/endpoints/items.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def read_items():
    return [{"item": "foo"}]

# app/api/v1/endpoints/users.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def read_users():
    return [{"user": "john"}]

# app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import items, users

api_router = APIRouter()
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

# app/main.py
from fastapi import FastAPI
from app.api.v1.api import api_router

app = FastAPI()
app.include_router(api_router, prefix="/api/v1")
```

## Error Handling

### Understanding Error Status Codes

**422 Unprocessable Entity**: Pydantic validation failure (automatic)
**400 Bad Request**: Business logic error (manual)
**404 Not Found**: Resource doesn't exist
**500 Internal Server Error**: Unexpected server error

### 422 vs 400: Critical Distinction

```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator

# 422: Pydantic validation errors (automatic by FastAPI)
class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)
    quantity: int = Field(ge=0)

@app.post("/items")
def create_item(item: ItemCreate) -> dict:
    """
    Validation errors return 422 automatically:
    - name too short/long: 422
    - price negative: 422
    - quantity negative: 422
    - missing required field: 422
    """
    return {"name": item.name, "price": item.price}

# 400: Business logic errors (manual HTTPException)
@app.post("/items")
def create_item(item: ItemCreate, session: SessionDep) -> dict:
    """Use 400 for business logic violations"""
    # Check if item already exists (business rule)
    existing = session.exec(select(Item).where(Item.name == item.name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,  # 400 for business logic
            detail="Item with this name already exists"
        )

    # Check stock availability (business rule)
    if item.quantity > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,  # 400 for business logic
            detail="Quantity exceeds maximum stock limit"
        )

    # Success
    return {"name": item.name, "price": item.price}
```

### When to Use Each Status Code

| Code | Use When | Example |
|------|----------|---------|
| **422** | Pydantic validation fails | Missing field, wrong type, length violations |
| **400** | Business logic violation | Duplicate email, insufficient funds, invalid state |
| **404** | Resource not found | User ID doesn't exist, item not in database |
| **409** | Conflict state | Editing a deleted resource, race condition |
| **500** | Unexpected error | Database connection failed, external API error |

### Validation Error Handling Patterns

```python
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator

app = FastAPI()

# Custom 422 error handler (optional)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Customize 422 validation error response"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body,
            "message": "Validation failed"
        }
    )

# Model with custom validation
class UserCreate(BaseModel):
    email: str = Field(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Custom validation returns 422 if it fails"""
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v

@app.post("/users")
def create_user(user: UserCreate, session: SessionDep) -> dict:
    """
    Automatic 422 errors:
    - Invalid email format: 422
    - Password too short: 422
    - Password validation fails: 422

    Manual 400 errors:
    - Email already registered: 400
    """
    # Check business rule
    existing = crud.get_user_by_email(session, user.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    return {"email": user.email, "id": 1}
```

### HTTP Exceptions

```python
from fastapi import FastAPI, HTTPException, status

app = FastAPI()

@app.get("/items/{item_id}")
def read_item(item_id: int, session: SessionDep) -> dict:
    """Proper error handling with status codes"""
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found",
            headers={"X-Error": "Resource-Not-Found"},
        )
    # Always return dict
    return {"id": item.id, "name": item.name}

@app.post("/items")
def create_item(item: ItemCreate, session: SessionDep) -> dict:
    """Business logic validation"""
    # Duplicate check (400 - business logic)
    existing = session.exec(select(Item).where(Item.name == item.name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item name must be unique"
        )

    # Create item
    db_item = Item(**item.model_dump())
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return {"id": db_item.id, "name": db_item.name}
```

### Custom Exception Handlers

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class CustomException(Exception):
    def __init__(self, name: str):
        self.name = name

app = FastAPI()

@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something wrong."},
    )

@app.get("/custom")
async def trigger_custom():
    raise CustomException(name="test")
```

## Middleware

### Adding CORS Middleware

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],  # In production: specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Custom Middleware

```python
from fastapi import FastAPI, Request
import time

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

### ASGI Middleware

```python
from fastapi import FastAPI

app = FastAPI()

# Recommended: Use add_middleware for third-party ASGI middleware
app.add_middleware(SomeASGIMiddleware, config="value")
```

## Running the Application

### Development Server

```bash
# Auto-reload on changes
fastapi dev main.py

# Access documentation
# Swagger UI: http://127.0.0.1:8000/docs
# ReDoc: http://127.0.0.1:8000/redoc
```

### Production Server

```bash
# Single worker
uvicorn main:app --host 0.0.0.0 --port 8000

# Multiple workers (production)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# With Gunicorn + Uvicorn workers
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Best Practices

### Type Hints Everywhere

```python
from typing import List, Optional
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
    tags: List[str] = []

@app.get("/items", response_model=List[Item])
async def read_items(skip: int = 0, limit: int = 10) -> List[Item]:
    return items[skip : skip + limit]
```

### Async vs Sync

```python
# Use async for I/O-bound operations
@app.get("/users")
async def read_users():
    users = await database.fetch_all("SELECT * FROM users")
    return users

# Use sync for CPU-bound operations or when calling sync libraries
@app.get("/compute")
def heavy_computation():
    result = complex_calculation()  # Sync CPU-bound work
    return {"result": result}
```

### Tags for Organization

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items", tags=["items"])
async def read_items():
    return [{"item": "foo"}]

@app.get("/users", tags=["users"])
async def read_users():
    return [{"user": "john"}]

# Tags appear in docs for organization
```

### Status Codes

```python
from fastapi import FastAPI, status

app = FastAPI()

@app.post("/items", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item):
    return item

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int):
    items.pop(item_id)
    return None  # 204 means no content
```

## Common Patterns

### Pagination

```python
from fastapi import FastAPI, Query
from typing import Annotated

app = FastAPI()

@app.get("/items")
async def read_items(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    return {
        "items": items[skip : skip + limit],
        "total": len(items),
        "skip": skip,
        "limit": limit,
    }
```

### Health Check

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/readiness")
async def readiness_check(db: Database = Depends(get_db)):
    # Check database connection
    try:
        await db.execute("SELECT 1")
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database not ready")
```

### Background Tasks

```python
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()

def write_log(message: str):
    with open("log.txt", "a") as f:
        f.write(message + "\n")

@app.post("/send-notification")
async def send_notification(
    email: str,
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(write_log, f"Notification sent to {email}")
    return {"message": "Notification sent"}
```

## Documentation Enhancement

### Documenting Responses

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

class Message(BaseModel):
    message: str

app = FastAPI()

@app.get(
    "/items/{item_id}",
    response_model=Item,
    responses={
        404: {"model": Message, "description": "Item not found"},
        400: {"model": Message, "description": "Invalid item ID"},
    },
)
async def read_item(item_id: int):
    """
    Get an item by ID.

    - **item_id**: The ID of the item to retrieve

    Returns the item if found, otherwise 404.
    """
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]
```

This reference covers the core FastAPI patterns. For authentication, database integration, and deployment, see the respective reference files.
