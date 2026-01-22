# Security Best Practices for FastAPI

Comprehensive security guide for production FastAPI applications.

## Authentication & Authorization

### Password Security

**Never store plaintext passwords:**
```python
# ✅ Good: Hash passwords
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

hashed = pwd_context.hash("user_password")
is_valid = pwd_context.verify("user_password", hashed)
```

**Recommended hashing algorithms:**
1. **Argon2** (best, winner of Password Hashing Competition)
2. bcrypt (good alternative)
3. scrypt (good alternative)

### Secret Key Management

```python
# ❌ Bad: Hardcoded secret
SECRET_KEY = "my-secret-key"

# ✅ Good: Environment variable
import os

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set")

# ✅ Best: Use secrets manager (AWS Secrets Manager, HashiCorp Vault)
```

**Generate strong secret keys:**
```bash
# Generate 32-byte (256-bit) secret key
openssl rand -hex 32

# Or in Python
import secrets
print(secrets.token_hex(32))
```

### JWT Token Security

```python
from datetime import datetime, timedelta, UTC
from jose import jwt

# ✅ Good practices
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Short expiration
REFRESH_TOKEN_EXPIRE_DAYS = 7     # Longer for refresh tokens

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
```

**JWT Best Practices:**
- Use short expiration times (15-30 minutes)
- Include token type in payload
- Validate expiration on every request
- Implement token refresh mechanism
- Consider token blacklisting for logout

## CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

# ❌ Bad: Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dangerous in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Good: Specific origins only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://example.com",
        "https://app.example.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,  # Cache preflight requests
)

# ✅ Best: From environment configuration
from app.core.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # List from env
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)
```

## Input Validation

### Use Pydantic Models

```python
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr  # Validates email format
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=120)

    @validator('password')
    def password_strength(cls, v):
        """Ensure password complexity."""
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

# FastAPI automatically validates using this model
@app.post("/users")
async def create_user(user: UserCreate):
    return user
```

### SQL Injection Prevention

```python
# ✅ Good: Use ORM (prevents SQL injection)
from sqlalchemy.orm import Session

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

# ❌ Bad: Raw SQL with string formatting
def get_user_bad(db: Session, user_id: int):
    query = f"SELECT * FROM users WHERE id = {user_id}"  # Vulnerable!
    return db.execute(query)

# ✅ If raw SQL needed, use parameterized queries
from sqlalchemy import text

def get_user_safe(db: Session, user_id: int):
    query = text("SELECT * FROM users WHERE id = :user_id")
    return db.execute(query, {"user_id": user_id})
```

### Path Traversal Prevention

```python
from pathlib import Path
import os

# ❌ Bad: Direct user input in file path
@app.get("/files/{filename}")
async def get_file(filename: str):
    with open(f"./files/{filename}") as f:  # Vulnerable to ../../../etc/passwd
        return f.read()

# ✅ Good: Validate and sanitize filename
from fastapi import HTTPException

UPLOAD_DIR = Path("./files")

@app.get("/files/{filename}")
async def get_file(filename: str):
    # Remove any path components
    safe_filename = os.path.basename(filename)

    # Construct safe path
    file_path = (UPLOAD_DIR / safe_filename).resolve()

    # Ensure path is within UPLOAD_DIR
    if not str(file_path).startswith(str(UPLOAD_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)
```

## File Upload Security

```python
from fastapi import File, UploadFile, HTTPException
from pathlib import Path
import magic  # python-magic library

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

async def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {file_ext} not allowed")

    # Read file content
    content = await file.read()
    await file.seek(0)  # Reset file pointer

    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    # Verify MIME type (prevent fake extensions)
    mime = magic.from_buffer(content, mime=True)
    allowed_mimes = ["image/jpeg", "image/png", "application/pdf"]
    if mime not in allowed_mimes:
        raise HTTPException(status_code=400, detail=f"Invalid file type: {mime}")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    await validate_file(file)

    # Generate safe filename
    safe_filename = f"{uuid.uuid4()}{Path(file.filename).suffix}"
    file_path = UPLOAD_DIR / safe_filename

    # Save file
    with file_path.open("wb") as f:
        content = await file.read()
        f.write(content)

    return {"filename": safe_filename}
```

## Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply rate limit to specific endpoint
@app.post("/login")
@limiter.limit("5/minute")  # 5 requests per minute
async def login(request: Request, credentials: LoginCredentials):
    return authenticate(credentials)

# Global rate limit
@app.get("/api/items")
@limiter.limit("100/hour")
async def get_items():
    return items
```

## Security Headers

```python
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# Trusted Host (prevent host header injection)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["example.com", "*.example.com"]
)

# Custom security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # XSS Protection
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Strict Transport Security (HTTPS only)
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Content Security Policy
    response.headers["Content-Security-Policy"] = "default-src 'self'"

    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Permissions Policy
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"

    return response
```

## Dependency Injection Security

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_admin(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> User:
    """Verify user is admin."""
    user = await get_current_user(credentials.credentials)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# Use in protected endpoints
@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(verify_admin)
):
    return {"deleted": user_id}
```

## Secrets in Logs

```python
import logging
from typing import Any

# ❌ Bad: Logging sensitive data
logger.info(f"User logged in: {username}, password: {password}")  # Never!

# ✅ Good: Sanitize logs
def sanitize_log_data(data: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive fields from log data."""
    sensitive_fields = {"password", "token", "secret", "api_key", "authorization"}
    return {
        k: "***REDACTED***" if k.lower() in sensitive_fields else v
        for k, v in data.items()
    }

logger.info(f"Request data: {sanitize_log_data(request_data)}")
```

## Environment Variables

```python
# .env (never commit to git!)
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/db

# .env.example (commit this as template)
SECRET_KEY=generate-with-openssl-rand-hex-32
DATABASE_URL=postgresql://user:password@host:5432/dbname

# .gitignore
.env
*.env
.env.local
```

## HTTPS Enforcement

```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Production only
if settings.ENVIRONMENT == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
```

## Database Security

```python
from sqlalchemy import create_engine

# ✅ Good: Use environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# ✅ Best: Use SSL for database connections in production
if settings.ENVIRONMENT == "production":
    DATABASE_URL += "?sslmode=require"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections
    echo=False,          # Don't log SQL queries in production
)
```

## API Key Security

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key from header."""
    if api_key is None:
        raise HTTPException(status_code=401, detail="API key required")

    # ❌ Bad: Compare directly (timing attack vulnerable)
    if api_key != EXPECTED_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # ✅ Good: Use constant-time comparison
    import hmac
    if not hmac.compare_digest(api_key, EXPECTED_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")

    return api_key
```

## Sensitive Data in Responses

```python
from pydantic import BaseModel

class UserInDB(BaseModel):
    id: int
    email: str
    hashed_password: str  # Should not be returned!
    is_active: bool

class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    # hashed_password excluded

# ✅ Good: Use response_model to filter output
@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    return user  # hashed_password automatically excluded
```

## Dependency Vulnerabilities

```bash
# Scan dependencies for vulnerabilities
pip install safety
safety check

# Or use
pip install pip-audit
pip-audit

# Keep dependencies updated
pip install --upgrade -r requirements.txt
```

## Docker Security

```dockerfile
# ✅ Good practices

# Use specific version tags (not 'latest')
FROM python:3.11-slim

# Run as non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# Don't include secrets in image
# Use environment variables or secrets management

# Minimize attack surface
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Scan image for vulnerabilities
# docker scan fastapi-app:latest
```

## Security Checklist

### Authentication & Authorization
- [ ] Hash passwords with Argon2 or bcrypt
- [ ] Use strong secret keys (32+ bytes)
- [ ] Store secrets in environment variables
- [ ] Implement JWT token expiration
- [ ] Use HTTPS in production
- [ ] Implement refresh token mechanism
- [ ] Add rate limiting on auth endpoints

### Input Validation
- [ ] Use Pydantic models for all inputs
- [ ] Validate file uploads (type, size, content)
- [ ] Sanitize filenames (prevent path traversal)
- [ ] Use ORM or parameterized queries (prevent SQL injection)
- [ ] Validate email addresses
- [ ] Enforce password complexity

### API Security
- [ ] Configure CORS with specific origins
- [ ] Add security headers (X-Frame-Options, CSP, etc.)
- [ ] Implement rate limiting
- [ ] Use HTTPS redirect in production
- [ ] Validate API keys using constant-time comparison
- [ ] Add request size limits

### Data Protection
- [ ] Use response_model to exclude sensitive fields
- [ ] Never log passwords or tokens
- [ ] Encrypt sensitive data at rest
- [ ] Use SSL for database connections
- [ ] Implement proper session management
- [ ] Add data retention policies

### Infrastructure
- [ ] Run containers as non-root user
- [ ] Scan dependencies for vulnerabilities
- [ ] Keep dependencies updated
- [ ] Use specific version tags for base images
- [ ] Set up Web Application Firewall (WAF)
- [ ] Configure firewall rules
- [ ] Enable audit logging
- [ ] Implement monitoring and alerting

### Code & Configuration
- [ ] Never commit secrets to git
- [ ] Use .env files (not committed)
- [ ] Implement proper error handling
- [ ] Don't expose stack traces in production
- [ ] Use secrets management (AWS Secrets Manager, Vault)
- [ ] Regular security audits
- [ ] Implement Content Security Policy
- [ ] Add HSTS header (HTTPS only)

## Tools & Resources

### Security Scanning
```bash
# Python dependency vulnerabilities
pip install safety
safety check

# Or
pip install pip-audit
pip-audit

# Docker image scanning
docker scan fastapi-app:latest

# Static code analysis
pip install bandit
bandit -r app/

# SAST (Static Application Security Testing)
pip install semgrep
semgrep --config=auto app/
```

### Testing Security

```python
# tests/test_security.py
def test_no_password_in_response(client):
    """Ensure password is not returned."""
    response = client.post("/users/", json={...})
    assert "password" not in response.json()
    assert "hashed_password" not in response.json()

def test_authentication_required(client):
    """Ensure protected endpoints require auth."""
    response = client.get("/users/me")
    assert response.status_code == 401

def test_rate_limiting(client):
    """Test rate limiting works."""
    for _ in range(6):  # Exceed limit of 5
        response = client.post("/login", json={...})
    assert response.status_code == 429  # Too many requests
```

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
