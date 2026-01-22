# FastAPI Deployment Patterns

Production deployment patterns with Docker and Uvicorn.

## Overview

FastAPI applications are deployed as ASGI servers. The recommended production setup uses:
- **Uvicorn**: High-performance ASGI server
- **Docker**: Containerization for consistency
- **Gunicorn + Uvicorn Workers**: Process management (optional)

## Local Development

### Development Server

```bash
# Auto-reload on changes
fastapi dev main.py

# Custom port
fastapi dev main.py --port 8080

# Access docs
# http://127.0.0.1:8000/docs
# http://127.0.0.1:8000/redoc
```

## Production Server (Uvicorn)

### Single Process

```bash
# Basic
uvicorn main:app --host 0.0.0.0 --port 8000

# With workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# With SSL
uvicorn main:app --host 0.0.0.0 --port 443 \
    --ssl-keyfile=./key.pem \
    --ssl-certfile=./cert.pem
```

### With Gunicorn (Process Manager)

```bash
# Gunicorn with Uvicorn workers
gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --graceful-timeout 30
```

### Systemd Service

```ini
# /etc/systemd/system/fastapi-app.service
[Unit]
Description=FastAPI Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/fastapi-app
Environment="PATH=/opt/fastapi-app/venv/bin"
ExecStart=/opt/fastapi-app/venv/bin/gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable fastapi-app
sudo systemctl start fastapi-app
sudo systemctl status fastapi-app

# View logs
sudo journalctl -u fastapi-app -f
```

## Docker Deployment

### Dockerfile (Production)

```dockerfile
# Use official Python runtime as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app ./app

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Multi-Stage Dockerfile (Optimized)

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application
COPY ./app ./app

# Set PATH
ENV PATH=/root/.local/bin:$PATH

# Non-root user
RUN useradd -m -u 1000 appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

### Docker Compose (Development)

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/appdb
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./app:/app/app  # Mount for hot-reload in dev
    depends_on:
      - db
    restart: unless-stopped
    command: fastapi dev app/main.py --host 0.0.0.0  # Dev mode

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=appdb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  postgres_data:
```

### Docker Compose (Production)

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    depends_on:
      - db
    restart: always
    command: >
      gunicorn app.main:app
      --workers 4
      --worker-class uvicorn.workers.UvicornWorker
      --bind 0.0.0.0:8000
      --timeout 120
      --graceful-timeout 30
      --access-logfile -
      --error-logfile -
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - api
    restart: always

volumes:
  postgres_data:
```

### Build and Run

```bash
# Build image
docker build -t fastapi-app .

# Run container
docker run -d \
    --name fastapi-app \
    -p 8000:8000 \
    -e DATABASE_URL="postgresql://..." \
    -e SECRET_KEY="your-secret-key" \
    fastapi-app

# Using docker-compose (development)
docker-compose up

# Using docker-compose (production)
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker logs -f fastapi-app

# Execute command in container
docker exec -it fastapi-app bash

# Stop and remove
docker-compose down
```

## Nginx Reverse Proxy

### nginx.conf

```nginx
upstream fastapi_app {
    server api:8000;
}

server {
    listen 80;
    server_name example.com www.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    # SSL configuration
    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Client body size limit (for file uploads)
    client_max_body_size 10M;

    # Timeouts
    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;
    proxy_read_timeout 600s;

    location / {
        proxy_pass http://fastapi_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://fastapi_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Static files (if serving from nginx)
    location /static {
        alias /app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

## Environment Configuration

### .env.example

```bash
# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=generate-secure-key-here
API_V1_PREFIX=/api/v1

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Redis (if using)
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=["https://example.com"]

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Logging
LOG_LEVEL=INFO
```

### Loading Configuration

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## Health Checks

### Basic Health Check

```python
from fastapi import FastAPI, status
from sqlalchemy import text

app = FastAPI()

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Basic health check."""
    return {"status": "healthy"}

@app.get("/readiness", status_code=status.HTTP_200_OK)
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness check including database."""
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not ready: {str(e)}"
        )

@app.get("/liveness", status_code=status.HTTP_200_OK)
async def liveness_check():
    """Liveness check."""
    return {"status": "alive"}
```

## Logging

### Production Logging Setup

```python
# app/core/logging.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging(log_level: str = "INFO"):
    """Configure structured logging for production."""
    logger = logging.getLogger()

    # Remove existing handlers
    logger.handlers.clear()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    # JSON formatter for structured logs
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(log_level)

    return logger

# app/main.py
from app.core.logging import setup_logging
from app.core.config import settings

# Setup logging
logger = setup_logging(settings.LOG_LEVEL)

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up", extra={"environment": settings.ENVIRONMENT})

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down")
```

## Database Migrations in Production

```bash
# In Dockerfile or startup script
# Run migrations before starting server
alembic upgrade head

# Then start server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker Entrypoint

```bash
#!/bin/bash
# entrypoint.sh

set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
exec "$@"
```

```dockerfile
# In Dockerfile
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Performance Tuning

### Worker Configuration

```python
# Calculate optimal workers
# workers = (2 * CPU_CORES) + 1

# For 4 CPU cores:
# workers = (2 * 4) + 1 = 9 workers
```

```bash
# Set workers based on CPU
uvicorn main:app --workers $((2 * $(nproc) + 1))

# Or with Gunicorn
gunicorn main:app \
    --workers $((2 * $(nproc) + 1)) \
    --worker-class uvicorn.workers.UvicornWorker
```

### Connection Pooling

```python
# app/db/session.py
engine = create_engine(
    DATABASE_URL,
    pool_size=10,              # Base pool size
    max_overflow=20,           # Max additional connections
    pool_pre_ping=True,        # Check connection health
    pool_recycle=3600,         # Recycle connections after 1 hour
    echo=False,                # Disable SQL logging in production
)
```

## Monitoring

### Application Metrics

```python
# app/api/v1/endpoints/metrics.py
from fastapi import APIRouter
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

router = APIRouter()

# Define metrics
request_count = Counter('http_requests_total', 'Total HTTP requests')

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

## Security Best Practices

### Production Checklist

- [ ] Use HTTPS (TLS/SSL certificates)
- [ ] Set SECRET_KEY from environment variable
- [ ] Configure CORS properly (specific origins)
- [ ] Enable security headers (via Nginx or middleware)
- [ ] Use non-root user in Docker
- [ ] Implement rate limiting
- [ ] Set up firewall rules
- [ ] Use environment variables for secrets
- [ ] Enable database SSL connections
- [ ] Implement proper logging (no secrets in logs)
- [ ] Set up monitoring and alerts
- [ ] Regular security updates
- [ ] Backup database regularly

### Security Headers

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["example.com", "*.example.com"])
app.add_middleware(HTTPSRedirectMiddleware)  # Production only
```

## Cloud Platform Deployment

### AWS ECS (Fargate)

```json
{
  "family": "fastapi-app",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "fastapi",
      "image": "your-ecr-repo/fastapi-app:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://..."
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:..."
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/fastapi-app",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512"
}
```

### Google Cloud Run

```bash
# Deploy to Cloud Run
gcloud run deploy fastapi-app \
    --image gcr.io/project-id/fastapi-app \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars DATABASE_URL=... \
    --set-secrets SECRET_KEY=secret-key:latest
```

### Heroku

```yaml
# Procfile
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
release: alembic upgrade head
```

## References

- [FastAPI Deployment Documentation](https://fastapi.tiangolo.com/deployment/)
- [Uvicorn Deployment](https://www.uvicorn.org/deployment/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
