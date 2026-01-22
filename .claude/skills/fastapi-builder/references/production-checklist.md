# Production Readiness Checklist

Complete checklist for deploying FastAPI to production.

## Security

### Authentication & Authorization
- [ ] Passwords hashed with Argon2 or bcrypt (never plaintext)
- [ ] SECRET_KEY stored in environment variable (not hardcoded)
- [ ] SECRET_KEY is cryptographically strong (32+ bytes)
- [ ] JWT tokens have expiration (15-30 minutes recommended)
- [ ] Token refresh mechanism implemented
- [ ] HTTPS enforced in production
- [ ] OAuth2 scopes configured for fine-grained permissions
- [ ] Rate limiting on authentication endpoints
- [ ] Failed login attempts tracked and throttled

### Input Validation
- [ ] All inputs validated with Pydantic models
- [ ] Email validation using EmailStr
- [ ] Password complexity requirements enforced
- [ ] File upload validation (type, size, content)
- [ ] Path traversal prevention for file operations
- [ ] SQL injection prevention (using ORM)
- [ ] Request size limits configured
- [ ] Query parameter validation with min/max constraints

### API Security
- [ ] CORS configured with specific origins (no `*` in production)
- [ ] Security headers added (X-Frame-Options, CSP, HSTS, etc.)
- [ ] Rate limiting implemented on all endpoints
- [ ] API keys validated using constant-time comparison
- [ ] Trusted host middleware configured
- [ ] Input sanitization for user-generated content
- [ ] Protection against common attacks (XSS, CSRF, clickjacking)

### Data Protection
- [ ] Sensitive data excluded from API responses (use response_model)
- [ ] No secrets in logs (passwords, tokens, API keys)
- [ ] Database connections use SSL in production
- [ ] Sensitive data encrypted at rest
- [ ] Data retention policies implemented
- [ ] User data deletion mechanism (GDPR compliance)
- [ ] Audit logging for sensitive operations

## Configuration

### Environment Variables
- [ ] All secrets in environment variables (not in code)
- [ ] `.env` file added to `.gitignore`
- [ ] `.env.example` provided as template
- [ ] Environment-specific configs (dev, staging, prod)
- [ ] Database URL from environment
- [ ] CORS origins from environment
- [ ] Debug mode disabled in production (`DEBUG=false`)
- [ ] Configuration validation on startup

### Database
- [ ] Database connection pooling configured
- [ ] Connection pool size appropriate for load
- [ ] Database migrations tested and automated (Alembic)
- [ ] Indexes added for frequently queried fields
- [ ] Foreign key constraints properly defined
- [ ] Database backups configured and tested
- [ ] Database credentials rotated regularly
- [ ] Connection timeouts configured
- [ ] Read replicas for scaling (if needed)

### Logging
- [ ] Structured logging configured (JSON format recommended)
- [ ] Log level set appropriately (INFO or WARNING in production)
- [ ] Request/response logging (excluding sensitive data)
- [ ] Error tracking integrated (Sentry, Rollbar, etc.)
- [ ] Log aggregation configured (ELK, CloudWatch, etc.)
- [ ] Log rotation configured
- [ ] Performance metrics logged
- [ ] Audit trail for sensitive operations

## Application Code

### API Design
- [ ] API versioning implemented (e.g., `/api/v1`)
- [ ] Consistent endpoint naming conventions
- [ ] Proper HTTP methods used (GET, POST, PUT, DELETE, PATCH)
- [ ] Appropriate status codes returned
- [ ] Error responses have consistent format
- [ ] Pagination implemented for list endpoints
- [ ] Response models defined for all endpoints
- [ ] API documentation complete (OpenAPI/Swagger)

### Error Handling
- [ ] Custom exception handlers defined
- [ ] Validation errors return 422 with details
- [ ] 404 errors for missing resources
- [ ] 500 errors logged and tracked
- [ ] Error messages don't expose internal details
- [ ] User-friendly error messages
- [ ] Stack traces hidden in production
- [ ] Error codes defined for client handling

### Performance
- [ ] Database queries optimized (avoid N+1 queries)
- [ ] Eager loading configured where needed
- [ ] Connection pooling enabled
- [ ] Caching implemented for expensive operations
- [ ] Background tasks for long-running operations
- [ ] Async/await used appropriately
- [ ] Static files served efficiently (CDN or nginx)
- [ ] Compression enabled (gzip)

### Testing
- [ ] Unit tests for business logic (>80% coverage)
- [ ] Integration tests for API endpoints
- [ ] Authentication tests (valid/invalid credentials)
- [ ] Authorization tests (permissions/scopes)
- [ ] Input validation tests
- [ ] Error handling tests
- [ ] Database tests (CRUD operations)
- [ ] Performance tests for critical endpoints
- [ ] All tests pass before deployment

## Deployment

### Infrastructure
- [ ] Application containerized (Docker)
- [ ] Multi-stage Dockerfile for optimized image
- [ ] Non-root user in container
- [ ] Health check endpoints implemented (`/health`, `/readiness`)
- [ ] Liveness and readiness probes configured
- [ ] Resource limits set (CPU, memory)
- [ ] Auto-scaling configured based on metrics
- [ ] Load balancer configured
- [ ] CDN configured for static assets

### Server Configuration
- [ ] Uvicorn or Gunicorn configured
- [ ] Appropriate number of workers (2 × CPU + 1)
- [ ] Worker timeout configured
- [ ] Graceful shutdown implemented
- [ ] Process manager configured (systemd, supervisord, or K8s)
- [ ] Reverse proxy configured (nginx, traefik)
- [ ] SSL/TLS certificates installed and valid
- [ ] HTTP/2 enabled
- [ ] Timeouts configured appropriately

### Database
- [ ] Database migrations run before deployment
- [ ] Migration rollback plan documented
- [ ] Database connection URL secured
- [ ] Database backups scheduled
- [ ] Backup restoration tested
- [ ] Database monitoring configured
- [ ] Connection pool tuned for production load

### Monitoring & Observability
- [ ] Application metrics exposed (Prometheus, CloudWatch)
- [ ] Health check monitoring (uptime checks)
- [ ] Error rate monitoring and alerting
- [ ] Latency monitoring (p50, p95, p99)
- [ ] Database performance monitoring
- [ ] Resource utilization monitoring (CPU, memory, disk)
- [ ] Log aggregation and search configured
- [ ] Distributed tracing implemented (optional)
- [ ] Alerting thresholds configured
- [ ] On-call rotation documented

## Documentation

### API Documentation
- [ ] OpenAPI/Swagger docs enabled (`/docs`)
- [ ] ReDoc enabled (`/redoc`)
- [ ] API metadata configured (title, version, description)
- [ ] Endpoints organized with tags
- [ ] Request/response examples provided
- [ ] Authentication documented
- [ ] Error responses documented
- [ ] Deprecation notices for old endpoints

### Developer Documentation
- [ ] README with project overview
- [ ] Setup instructions (local development)
- [ ] Environment variables documented
- [ ] Database schema documented
- [ ] API architecture documented
- [ ] Deployment process documented
- [ ] Troubleshooting guide
- [ ] Contributing guidelines (if open source)

### Operations Documentation
- [ ] Deployment runbook
- [ ] Rollback procedures
- [ ] Database migration procedures
- [ ] Backup and restore procedures
- [ ] Incident response plan
- [ ] Monitoring and alerting guide
- [ ] Security incident response plan
- [ ] Disaster recovery plan

## Compliance & Legal

### Data Protection
- [ ] GDPR compliance (if handling EU data)
- [ ] CCPA compliance (if handling CA data)
- [ ] Data retention policies defined
- [ ] User data deletion mechanism
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] Cookie consent implemented (if applicable)
- [ ] Data processing agreements in place

### Security Compliance
- [ ] Security audit completed
- [ ] Penetration testing performed
- [ ] Vulnerability scanning automated
- [ ] Dependencies scanned for vulnerabilities
- [ ] Security patches applied regularly
- [ ] Incident response plan documented
- [ ] Access control policies defined
- [ ] Audit logging enabled

## Performance & Scalability

### Load Testing
- [ ] Load tests performed (target RPS achieved)
- [ ] Stress tests performed (failure points identified)
- [ ] Database performance tested under load
- [ ] Memory leaks checked
- [ ] Connection pool sizing validated
- [ ] Rate limiting tested
- [ ] Auto-scaling tested

### Optimization
- [ ] Response time optimized (<200ms for simple endpoints)
- [ ] Database indexes optimized
- [ ] N+1 queries eliminated
- [ ] Caching strategy implemented
- [ ] Static assets compressed
- [ ] CDN configured for static content
- [ ] Database queries profiled and optimized

## Continuous Integration / Continuous Deployment

### CI/CD Pipeline
- [ ] Automated tests run on every commit
- [ ] Code linting configured (ruff, pylint, or black)
- [ ] Type checking configured (mypy)
- [ ] Security scanning in pipeline
- [ ] Docker image built automatically
- [ ] Image scanned for vulnerabilities
- [ ] Automated deployment to staging
- [ ] Manual approval for production deployment
- [ ] Rollback mechanism automated

### Version Control
- [ ] Git repository configured
- [ ] Branch protection rules enabled
- [ ] Code review required before merge
- [ ] Commit messages follow convention
- [ ] Semantic versioning used for releases
- [ ] CHANGELOG maintained
- [ ] Tags for releases

## Post-Deployment

### Monitoring
- [ ] Application started successfully
- [ ] Health checks passing
- [ ] No errors in logs
- [ ] Response times acceptable
- [ ] Database connections stable
- [ ] Memory usage normal
- [ ] CPU usage normal
- [ ] Disk space sufficient

### Validation
- [ ] Critical user flows tested
- [ ] Authentication working
- [ ] Database migrations applied
- [ ] External integrations working
- [ ] Email/notifications working
- [ ] File uploads working
- [ ] Background jobs processing
- [ ] Monitoring alerts working

### Communication
- [ ] Deployment communicated to team
- [ ] Release notes published
- [ ] Users notified of changes (if significant)
- [ ] Documentation updated
- [ ] Known issues documented
- [ ] On-call engineer identified

## Maintenance

### Regular Tasks
- [ ] Dependency updates scheduled (monthly)
- [ ] Security patches applied (within 24-48 hours)
- [ ] Database backups verified (weekly)
- [ ] Log rotation configured
- [ ] SSL certificate renewal automated
- [ ] Monitoring metrics reviewed (weekly)
- [ ] Error rates reviewed (daily)
- [ ] Performance trends analyzed (monthly)

### Incident Response
- [ ] Incident response plan documented
- [ ] On-call rotation defined
- [ ] Escalation procedures documented
- [ ] Runbooks for common issues
- [ ] Post-mortem process defined
- [ ] Communication channels defined
- [ ] Disaster recovery tested

## Quick Reference

### Pre-Deployment Checklist
```bash
# Run tests
pytest --cov=app tests/

# Check security
safety check
bandit -r app/

# Lint code
ruff check app/
mypy app/

# Build Docker image
docker build -t fastapi-app:latest .

# Scan image
docker scan fastapi-app:latest

# Run locally
docker-compose up
```

### Deployment Commands
```bash
# Run migrations
alembic upgrade head

# Start production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or with Gunicorn
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

### Post-Deployment Validation
```bash
# Check health
curl https://api.example.com/health

# Check readiness
curl https://api.example.com/readiness

# Check API docs
open https://api.example.com/docs

# Monitor logs
docker logs -f fastapi-app
# or
tail -f /var/log/fastapi-app/app.log
```

## Resources

- [ ] [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [ ] [12-Factor App](https://12factor.net/)
- [ ] [FastAPI Best Practices](https://fastapi.tiangolo.com/deployment/)
- [ ] [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [ ] [PostgreSQL Performance](https://wiki.postgresql.org/wiki/Performance_Optimization)
