# FastAPI Authentication Patterns

Official OAuth2 + JWT authentication patterns from FastAPI documentation.

## Overview

FastAPI provides built-in support for OAuth2 with Password flow and JWT Bearer tokens, the industry standard for API authentication.

**Key Components:**
- **OAuth2 Password Flow**: User provides username/password, receives JWT token
- **JWT Tokens**: Signed tokens containing user identity and scopes
- **Password Hashing**: Argon2 or bcrypt for secure password storage
- **Scopes**: Fine-grained authorization permissions

## Complete OAuth2 + JWT Implementation

### Dependencies Installation

```txt
# requirements.txt
fastapi
python-jose[cryptography]  # JWT encoding/decoding
passlib[argon2]            # Password hashing with Argon2
python-multipart           # Form data parsing
```

### Configuration

```python
# app/core/security.py
from datetime import datetime, timedelta, UTC
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError

# Security configuration
SECRET_KEY = "your-secret-key-here"  # Generate with: openssl rand -hex 32
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context (Argon2 recommended)
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,
    argon2__parallelism=4,
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "me": "Read information about the current user",
        "items": "Read items",
    },
)

# Data models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
    scopes: list[str] = []

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)

# User authentication
def authenticate_user(fake_db: dict, username: str, password: str) -> User | bool:
    """Authenticate user credentials."""
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# JWT token creation
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Get current user from token
async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """Extract and validate user from JWT token."""
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scope", "").split()
        token_data = TokenData(username=username, scopes=token_scopes)
    except (JWTError, ValidationError):
        raise credentials_exception

    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception

    # Validate scopes
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )

    return user

# Get current active user
async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Ensure user is active."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

### Database Models (Example)

```python
# Fake database for demonstration
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$...",
        "disabled": False,
    }
}

def get_user(db: dict, username: str) -> UserInDB | None:
    """Get user from database."""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
```

### Authentication Endpoints

```python
# app/api/v1/endpoints/auth.py
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import (
    authenticate_user,
    create_access_token,
    Token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter()

@router.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    """
    OAuth2 compatible token login endpoint.

    Accepts form data with username and password.
    Returns JWT access token.
    """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create token with scopes
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scope": " ".join(form_data.scopes)},
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
```

### Protected Endpoints

```python
# app/api/v1/endpoints/users.py
from typing import Annotated
from fastapi import APIRouter, Depends, Security
from app.core.security import get_current_active_user, User

router = APIRouter()

# Endpoint with no specific scope requirement
@router.get("/users/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get current user information."""
    return current_user

# Endpoint requiring "me" scope
@router.get("/users/me/", response_model=User)
async def read_own_info(
    current_user: Annotated[User, Security(get_current_active_user, scopes=["me"])]
):
    """Get current user information (requires 'me' scope)."""
    return current_user

# Endpoint requiring multiple scopes
@router.get("/users/me/items")
async def read_own_items(
    current_user: Annotated[
        User,
        Security(get_current_active_user, scopes=["items", "me"])
    ]
):
    """Get current user's items (requires 'items' and 'me' scopes)."""
    return [{"item_id": 1, "owner": current_user.username}]

# Public endpoint (no authentication)
@router.get("/status")
async def get_status():
    """Public status endpoint."""
    return {"status": "ok"}
```

## Simplified Authentication (No Scopes)

For simpler use cases without scope-based authorization:

```python
# app/core/security.py (simplified)
from datetime import datetime, timedelta, UTC
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: str | None = None
    disabled: bool | None = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
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

    user = get_user_from_db(username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

## API Key Authentication

For service-to-service authentication:

```python
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY = "your-api-key-here"
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key from header."""
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return api_key

# Use in endpoints
@app.get("/protected", dependencies=[Depends(verify_api_key)])
async def protected_endpoint():
    return {"message": "Access granted"}
```

## Best Practices

### Secret Key Generation

```bash
# Generate a secure secret key
openssl rand -hex 32
```

Store in environment variable:
```python
import os

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set")
```

### Password Hashing

**Recommended: Argon2**
```python
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,
    argon2__parallelism=4,
)
```

**Alternative: bcrypt**
```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

### Token Expiration

```python
# Short-lived access tokens
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Optional: Implement refresh tokens for longer sessions
REFRESH_TOKEN_EXPIRE_DAYS = 7
```

### Environment Variables

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
```

### HTTPS Only in Production

```python
# Force HTTPS in production
if os.getenv("ENV") == "production":
    oauth2_scheme = OAuth2PasswordBearer(
        tokenUrl="token",
        scheme_name="OAuth2",
        auto_error=True,
    )
```

## Testing Authentication

```python
# tests/test_auth.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_success():
    response = client.post(
        "/token",
        data={"username": "johndoe", "password": "secret"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_failure():
    response = client.post(
        "/token",
        data={"username": "johndoe", "password": "wrong"},
    )
    assert response.status_code == 401

def test_protected_endpoint():
    # Login first
    login_response = client.post(
        "/token",
        data={"username": "johndoe", "password": "secret"},
    )
    token = login_response.json()["access_token"]

    # Access protected endpoint
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "johndoe"

def test_protected_endpoint_no_token():
    response = client.get("/users/me")
    assert response.status_code == 401
```

## Interactive Testing

### Using Swagger UI

1. Navigate to `/docs`
2. Click "Authorize" button
3. Enter credentials:
   - **username**: johndoe
   - **password**: secret
   - **scopes**: Select required scopes (me, items, etc.)
4. Click "Authorize"
5. Test protected endpoints

### Using curl

```bash
# Get token
TOKEN=$(curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=johndoe&password=secret" \
  | jq -r '.access_token')

# Use token
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer $TOKEN"
```

## Common Patterns

### Role-Based Access Control (RBAC)

```python
from enum import Enum

class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"

class User(BaseModel):
    username: str
    role: Role

def require_role(required_role: Role):
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return role_checker

# Admin-only endpoint
@app.get("/admin/users")
async def get_all_users(
    admin: Annotated[User, Depends(require_role(Role.ADMIN))]
):
    return {"users": all_users}
```

### Token Refresh

```python
@router.post("/token/refresh", response_model=Token)
async def refresh_token(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Refresh access token."""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}
```

### Logout (Token Invalidation)

```python
# Implement token blacklist in Redis
from redis import Redis

redis_client = Redis(host='localhost', port=6379, db=0)

async def revoke_token(token: str):
    """Add token to blacklist."""
    # Decode to get expiration
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    exp = payload.get("exp")
    ttl = exp - datetime.now(UTC).timestamp()
    redis_client.setex(f"blacklist:{token}", int(ttl), "1")

async def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted."""
    return redis_client.exists(f"blacklist:{token}") == 1

@router.post("/logout")
async def logout(token: Annotated[str, Depends(oauth2_scheme)]):
    """Logout by blacklisting token."""
    await revoke_token(token)
    return {"message": "Successfully logged out"}
```

## Security Checklist

- [ ] Use HTTPS in production
- [ ] Generate strong SECRET_KEY (32+ random bytes)
- [ ] Store SECRET_KEY in environment variables, never in code
- [ ] Hash passwords with Argon2 or bcrypt
- [ ] Set appropriate token expiration (30 minutes recommended)
- [ ] Implement token refresh for long sessions
- [ ] Validate scopes for fine-grained authorization
- [ ] Use `get_current_active_user` to check user status
- [ ] Never log tokens or passwords
- [ ] Implement rate limiting on login endpoints
- [ ] Use token blacklisting for logout if needed
- [ ] Validate input on all endpoints
- [ ] Return generic error messages (don't reveal if username exists)

## References

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [OAuth2 with Password (and hashing), Bearer with JWT tokens](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [OAuth2 Scopes](https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/)
