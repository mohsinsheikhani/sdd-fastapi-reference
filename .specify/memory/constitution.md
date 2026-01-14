<!--
SYNC IMPACT REPORT
==================
Version Change: 1.0.0 → 1.1.0
Constitution Type: Minor amendment
Modified Principles:
  - Section 1: Added concrete testability criteria
  - Section 2: Made principles measurable with specific examples
  - Section 3: Defined architectural terms with clear boundaries
  - Section 4: Added exceptions for critical workflows
  - Section 6: Added specific pagination threshold
  - Section 7: Clarified type hint requirements with exceptions
  - Section 9: Set concrete code coverage threshold (80%)
  - All sections: Replaced vague terms with verifiable standards
Added Sections: None
Removed Sections: None
Templates Requiring Updates:
  ✅ plan-template.md - No changes needed (still compatible)
  ✅ spec-template.md - No changes needed (still compatible)
  ✅ tasks-template.md - No changes needed (still compatible)
Follow-up TODOs: None
Rationale: Improved testability and realism based on review feedback.
          All standards now have clear verification methods.
          Unrealistic requirements adjusted to be achievable.
-->

# Task API Constitution

## 1. Purpose and Scope

This project implements a user-specific Task API using FastAPI, PostgreSQL, SQLModel, and Pydantic.

The system provides basic CRUD operations for tasks, scoped to an authenticated user.

### Design Objectives (Testable Criteria)

The codebase MUST meet these verifiable standards:

**Maintainability**:
- All modules pass type checking (mypy/pyright with strict mode)
- All functions have explicit type signatures
- Cyclomatic complexity < 10 per function
- No functions exceed 50 lines of code

**AI-Agent Compatibility**:
- All APIs have Pydantic schemas with field descriptions
- All errors return structured JSON with error codes
- All functions have docstrings explaining purpose and contracts

**Programmatic Safety**:
- All user inputs validated via Pydantic models
- All API endpoints return consistent schema structures
- No raw ORM models exposed in responses
- All database operations use parameterized queries (via ORM)

All specifications, plans, and implementations MUST conform to the standards defined in this constitution.

---

## 2. Core Engineering Principles

### I. Correctness Over Convenience

Correctness takes priority over convenience. Systems MUST behave predictably and deterministically. Shortcuts that compromise correctness are not permitted.

**Rationale**: Task management requires data integrity. User trust depends on reliable behavior.

### II. Explicit Over Implicit

Explicit behavior is preferred over implicit behavior. Code behavior MUST be evident from function signatures, type hints, and names.

**Prohibited patterns**:
- Functions with undocumented side effects (modifying global state, external I/O)
- Implicit type conversions without validation
- Automatic data transformations not declared in schemas
- Configuration loaded from undeclared locations

**Verification**: Code review must identify any behavior not evident from signatures and explicit statements.

**Rationale**: AI-driven agents and programmatic consumers require predictable, well-defined interfaces.

### III. Strong Typing (NON-NEGOTIABLE)

Strong typing is mandatory. All code MUST use explicit type hints. Runtime type validation MUST occur at system boundaries.

**Rationale**: Type safety prevents entire classes of bugs and enables better tooling, AI assistance, and maintainability.

### IV. Separation of Concerns

Separation of concerns MUST be preserved across all layers:
- HTTP/presentation layer
- Business logic layer
- Data access layer

Mixing concerns within a single module or function is not permitted.

**Rationale**: Clear boundaries enable independent testing, reasoning, and modification of each layer.

### V. Explicit Contracts

Public interfaces (API endpoints, service functions) MUST define:
- **Inputs**: Type hints + Pydantic models with field constraints
- **Outputs**: Type hints + Pydantic response models
- **Errors**: Documented error codes and HTTP status codes
- **Side effects**: Docstring must note database writes, external calls, state changes

**Exemptions**: Private functions (prefixed with `_`) and standard library behavior need not be documented beyond type hints.

**Verification**: All public functions have complete type signatures. All API endpoints have request/response schemas. All raised exceptions documented in docstrings or ADRs.

**Rationale**: Clear contracts prevent misuse and enable reliable integration.

---

## 3. Architecture and Boundaries

### Layer Structure (NON-NEGOTIABLE)

FastAPI MUST be used strictly as the HTTP interface layer.

**Definitions** (for testability):

- **Route handler logic** (ALLOWED): Request parsing, calling services, response formatting, HTTP status selection
- **Business logic** (FORBIDDEN in routes): Data validation beyond schema, calculations, state transitions, authorization rules, data queries
- **Service layer** (REQUIRED for): All business rules, data access coordination, transaction management
- **Repository/Model layer** (REQUIRED for): All database queries, ORM operations

**Rules**:
- Route handlers MUST only: parse request, call 1-3 service functions, format response
- Business logic MUST be in service functions (named `*_service.py`)
- Database queries MUST use SQLModel/repositories (not raw SQL in routes)
- Dependency injection MUST be used for: `Session` (DB), `current_user` (auth)
- Global mutable state is not permitted

### Verification Checklist

✅ Route handlers < 20 lines each
✅ No SQLModel queries in route handlers
✅ No `if/else` business logic in route handlers (only HTTP status selection)
✅ Service functions accept domain objects, not HTTP request objects
✅ Models contain no HTTP-specific code

**Rationale**: Clear layer boundaries enable independent testing and controlled complexity.

---

## 4. Global Development Constraints

### Code Generation Standard

All automated code generation MUST use the FastAPI Builder Claude Skill.

Generated code MUST follow the latest syntax and patterns defined by the skill.

Manual code changes MUST NOT violate structures or assumptions introduced by the skill.

Mixing alternative architectural styles is not allowed.

**Rationale**: Consistency in code generation ensures predictable structure and reduces cognitive load.

### Development Workflow

All development MUST follow the Spec-Driven Development (SDD) workflow:
1. Specification first (spec.md)
2. Architecture planning (plan.md)
3. Task breakdown (tasks.md)
4. Implementation with tests

**Exemptions** (must be documented in commit message):
- **Critical hotfixes**: Security vulnerabilities, data loss bugs, production outages (retrospective spec required within 48 hours)
- **Trivial changes**: Typo fixes, log message updates, comment corrections (< 5 lines changed)
- **Configuration updates**: Environment variables, dependency version bumps with no API changes

**Verification**: All PRs without `spec.md` reference must include exemption justification in description.

**Rationale**: Planning before coding reduces rework and ensures alignment with requirements.

---

## 5. API Design Standards

### RESTful Semantics (NON-NEGOTIABLE)

RESTful CRUD semantics MUST be followed:
- GET for retrieval (idempotent)
- POST for creation
- PUT/PATCH for updates
- DELETE for removal

All endpoints MUST be versioned under `/api/v1`.

### Endpoint Requirements

Each endpoint MUST define:
- A request schema (Pydantic model)
- A response schema (Pydantic model)
- Explicit HTTP status codes for success and error cases
- User scoping (all task operations scoped to authenticated user)

### Response Standards

Endpoints MUST NOT return raw ORM models.

All responses MUST use explicit response schemas that:
- Hide internal implementation details
- Provide stable contracts
- Include only necessary fields

**Rationale**: Stable API contracts prevent breaking changes and enable independent evolution of internal and external models.

---

## 6. Data and Persistence Standards

### Database Requirements (NON-NEGOTIABLE)

PostgreSQL is the only supported database.

SQLModel is the only ORM layer.

### Model Requirements

All database models MUST:
- Define explicit table names (via `__tablename__`)
- Use UUID primary keys
- Include `created_at` timestamp field
- Include `updated_at` timestamp field with auto-update
- Include `user_id` foreign key for user-scoped entities

### Query Requirements

All database queries MUST be scoped to the authenticated user.

Queries MUST NOT:
- Allow cross-user data access
- Use raw SQL (unless explicitly justified in specification and reviewed for SQL injection)
- Return unfiltered result sets exceeding 100 records without pagination

**Pagination Requirements**:
- List endpoints returning > 100 records MUST implement pagination
- Default page size: 50 records
- Maximum page size: 100 records
- Use offset+limit or cursor-based pagination

**Verification**: All list endpoints have `limit` parameter. Integration tests verify pagination behavior.

**Rationale**: User data isolation is a security requirement. Pagination prevents memory issues and slow queries.

---

## 7. Typing, Validation, and Schemas

### Type Hint Requirements (NON-NEGOTIABLE)

Python type hints are mandatory for:
- All function signatures (parameters and return types)
- All method signatures
- All class attributes
- All module-level variables (except standard module constants)

**Exemptions**:
- Standard module constants: `__version__`, `__author__`, `__all__`
- Test fixtures with obvious types
- Third-party library compatibility where type hints cause errors

Implicit `Any` types are not permitted in application code.

**Verification**: Run `mypy --strict` or `pyright` with strict mode. All checks must pass.

### Pydantic Standards

Pydantic v2 syntax MUST be used consistently.

Separate schema models MUST exist for:
- Create operations (`TaskCreate`)
- Update operations (`TaskUpdate`)
- Read operations (`TaskRead`)

### Validation Rules

Validation logic MUST reside in:
- Schema models (via Pydantic validators)
- Service functions (for business rules)

Validation logic MUST NOT reside in route handlers.

### Optional Field Declaration

Optional fields MUST be explicitly declared using:
- `field: Optional[Type]` or `field: Type | None`
- Appropriate default values

Implicit optionality is not allowed.

**Rationale**: Explicit typing enables static analysis, better IDE support, and prevents type-related bugs at runtime.

---

## 8. Error Handling and Responses

### Exception Handling (NON-NEGOTIABLE)

Unhandled exceptions MUST NOT be exposed to API consumers.

All errors MUST return structured JSON responses with:
- Appropriate HTTP status code
- Machine-readable error identifier (error code string, e.g., "TASK_NOT_FOUND")
- Human-readable error message

**Optional** (recommended for production):
- Request ID for tracing (can be added via middleware when observability system exists)

### HTTPException Standards

HTTPException usage MUST include:
- HTTP status code (from standard codes: 400, 401, 403, 404, 409, 422, 500)
- Error detail as structured dict

Example:
```python
raise HTTPException(
    status_code=404,
    detail={"code": "TASK_NOT_FOUND", "message": "Task not found or access denied"}
)
```

### Database Error Translation

Database errors MUST be translated into domain-level errors:
- Integrity violations → 409 Conflict
- Not found → 404 Not Found
- Constraint violations → 422 Unprocessable Entity

Raw database exceptions MUST NOT leak to API consumers.

**Rationale**: Structured errors enable better client error handling and prevent security information leakage.

---

## 9. Testing and Quality Gates

### Test Requirements (NON-NEGOTIABLE)

Unit tests are required for:
- Service layer functions
- Repository layer functions
- Validation logic

Integration tests MUST cover:
- Core CRUD flows (Create, Read, Update, Delete)
- Authentication and authorization
- Error scenarios

### Test Environment

Tests MUST use an isolated test database.

Tests MUST NOT:
- Depend on external services
- Share state between test cases
- Modify production data

### Quality Gates

No code may be merged if:
- Tests are failing
- Type checks are failing (mypy/pyright strict mode)
- Linting checks are failing (ruff/flake8)
- Code coverage drops below 80% for:
  - Service layer functions
  - Repository functions
  - Validation logic

**Coverage Exemptions**:
- Route handlers (covered by integration tests)
- Simple getters/setters
- Configuration/settings files
- Third-party integrations (should use mocks)

**Verification**: CI runs `pytest --cov=src --cov-report=term --cov-fail-under=80`

**Rationale**: Automated testing prevents regressions and ensures code quality over time.

---

## 10. Tooling and Enforcement

### Environment Requirements

The Python version MUST be explicitly defined in:
- `pyproject.toml` or `requirements.txt`
- CI/CD configuration
- Development documentation

### Formatting and Linting

Formatting and linting tools MUST be configured and enforced:
- Code formatter (e.g., `black`, `ruff format`)
- Import sorter (e.g., `isort`)
- Linter (e.g., `ruff`, `flake8`)
- Type checker (e.g., `mypy`, `pyright`)

### Continuous Integration

CI MUST run:
- Linting checks (formatting, imports, linting)
- Type checking (mypy/pyright)
- Test suites (unit + integration)
- Security scans (dependency vulnerabilities)

All checks MUST pass before merge.

### Code Review

Code MUST be reviewed for compliance with this constitution.

Reviewers MUST verify:
- Architecture boundaries are respected
- Type hints are present and correct
- Tests cover new functionality
- Error handling is appropriate

**Rationale**: Automated tooling catches errors early and reduces manual review burden.

---

## 11. Amendment Rules

### Amendment Process

Changes to this constitution require:
1. Documented rationale explaining why the change is necessary
2. Impact analysis on existing code and specifications
3. Version increment following semantic versioning
4. Review and approval by project stakeholders

### Versioning

Constitution versions MUST follow semantic versioning:
- **MAJOR**: Backward incompatible changes (principle removals, redefinitions)
- **MINOR**: New principles or sections added
- **PATCH**: Clarifications, wording improvements, non-semantic fixes

### Downstream Impact

After amendment:
- Downstream specifications MUST be reviewed
- Dependent templates MUST be updated
- Existing code MAY require refactoring to comply

### Non-Retroactive Application

Amendments are not retroactive.

Existing code is not automatically non-compliant.

New code MUST comply with the current constitution version.

**Rationale**: Controlled amendment process prevents destabilizing changes and ensures all stakeholders understand governance evolution.

---

## Governance

This constitution supersedes all other development practices and guidelines.

All pull requests and code reviews MUST verify compliance with these principles.

Complexity and deviations MUST be explicitly justified in specifications and architectural decision records (ADRs).

Use `CLAUDE.md` for runtime development guidance and agent-specific instructions.

**Version**: 1.1.0 | **Ratified**: 2026-01-15 | **Last Amended**: 2026-01-15
