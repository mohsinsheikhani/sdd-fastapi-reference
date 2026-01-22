# Implementation Plan: Task CRUD Operations

**Branch**: `002-task-crud` | **Date**: 2026-01-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-task-crud/spec.md`
**Depends On**: `001-user-auth` (authentication, User model, cascade delete)

## Summary

Task management CRUD operations for authenticated users. Implements create, read (single/list), update (PATCH), and delete operations with filtering, sorting, and pagination. Tasks are user-scoped with terminal status states (completed/cancelled cannot be reopened). Includes computed `is_overdue` field and per-user rate limiting on task creation.

## Technical Context

**Language/Version**: Python 3.12+ (using `|` union syntax for type hints)
**Primary Dependencies**: FastAPI, SQLModel, Pydantic v2 (inherits from 001-user-auth)
**Storage**: PostgreSQL (Neon-compatible), SQLModel ORM
**Testing**: pytest, pytest-asyncio, httpx (for async test client)
**Target Platform**: Linux server (containerized deployment)
**Project Type**: Single project (backend API only)
**Performance Goals**: Single task retrieval < 200ms, list (50 items) < 500ms, create < 1s
**Constraints**: Rate limiting 10 req/min/user on task creation, max page size 100
**Scale/Scope**: Single-tenant, minimal user volume (learning project)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **1. Purpose/Scope** | PASS | Task CRUD is core to "user-specific Task API" per constitution |
| **2.I Correctness Over Convenience** | PASS | Spec defines deterministic state transitions, terminal states |
| **2.II Explicit Over Implicit** | PASS | All behaviors documented, computed fields explicit |
| **2.III Strong Typing** | PASS | Enums for status/priority, Pydantic v2 schemas |
| **2.IV Separation of Concerns** | PASS | Service layer for business logic, routes for HTTP |
| **2.V Explicit Contracts** | PASS | All inputs, outputs, error codes defined in spec |
| **3. Layer Structure** | PASS | Routes call services, services handle validation/DB |
| **4. SDD Workflow** | PASS | Following spec -> plan -> tasks workflow |
| **5. API Design Standards** | PASS | RESTful CRUD under `/api/v1/tasks`, versioned |
| **6. Data/Persistence** | PASS | PostgreSQL + SQLModel, UUID PK, user_id FK, timestamps |
| **7. Typing/Validation** | PASS | Pydantic v2 with Create/Update/Read schemas |
| **8. Error Handling** | PASS | Structured JSON errors with codes from spec |
| **9. Testing/Quality** | PASS | Unit + integration tests, 80% coverage target |
| **10. Tooling** | PASS | UV, pytest, mypy, ruff |

**Gate Status**: PASS - No violations identified

### Post-Design Re-evaluation (Phase 1 Complete)

| Artifact | Compliance Check | Status |
|----------|------------------|--------|
| `data-model.md` | Task model has UUID PK, user_id FK, timestamps | PASS |
| `data-model.md` | Pydantic schemas separate Create/Update/Read | PASS |
| `data-model.md` | Cascade delete configured via User relationship | PASS |
| `data-model.md` | Enums for status (str) and priority (IntEnum) | PASS |
| `contracts/tasks-api.yaml` | OpenAPI 3.1 with explicit schemas | PASS |
| `contracts/tasks-api.yaml` | All error codes defined in responses | PASS |
| `contracts/tasks-api.yaml` | Versioned under `/api/v1/tasks` | PASS |
| `contracts/tasks-api.yaml` | Pagination metadata in list response | PASS |
| `research.md` | Status transitions, pagination, filtering documented | PASS |
| `quickstart.md` | TDD workflow with test examples | PASS |

**Post-Design Gate Status**: PASS - All artifacts comply with constitution

## Project Structure

### Documentation (this feature)

```text
specs/002-task-crud/
├── plan.md              # This file
├── research.md          # Phase 0 output (technology decisions)
├── data-model.md        # Phase 1 output (entity definitions)
├── quickstart.md        # Phase 1 output (setup guide)
├── contracts/           # Phase 1 output (OpenAPI specs)
│   └── tasks-api.yaml   # Task CRUD API contract
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (extends 001-user-auth structure)

```text
src/
├── models/
│   ├── user.py               # (from 001-user-auth)
│   ├── token.py              # (from 001-user-auth)
│   └── task.py               # NEW: Task model
├── schemas/
│   ├── user.py               # (from 001-user-auth)
│   ├── auth.py               # (from 001-user-auth)
│   ├── error.py              # (from 001-user-auth)
│   ├── task.py               # NEW: TaskCreate, TaskUpdate, TaskRead
│   └── pagination.py         # NEW: PaginatedResponse, PaginationParams
├── services/
│   ├── auth_service.py       # (from 001-user-auth)
│   ├── user_service.py       # (from 001-user-auth)
│   ├── token_service.py      # (from 001-user-auth)
│   ├── password_service.py   # (from 001-user-auth)
│   └── task_service.py       # NEW: Task CRUD business logic
├── api/
│   ├── v1/
│   │   ├── router.py         # Updated: includes tasks router
│   │   ├── auth.py           # (from 001-user-auth)
│   │   ├── users.py          # (from 001-user-auth)
│   │   └── tasks.py          # NEW: Task endpoints
│   └── deps.py               # (from 001-user-auth)
├── middleware/
│   └── rate_limit.py         # Updated: user-based rate limiting support
└── core/
    ├── security.py           # (from 001-user-auth)
    └── exceptions.py         # Updated: task-specific exceptions

tests/
├── unit/
│   ├── test_auth_service.py     # (from 001-user-auth)
│   ├── test_user_service.py     # (from 001-user-auth)
│   ├── test_token_service.py    # (from 001-user-auth)
│   ├── test_password_service.py # (from 001-user-auth)
│   └── test_task_service.py     # NEW: Task service unit tests
└── integration/
    ├── test_registration.py     # (from 001-user-auth)
    ├── test_login.py            # (from 001-user-auth)
    ├── test_token_refresh.py    # (from 001-user-auth)
    ├── test_logout.py           # (from 001-user-auth)
    ├── test_password_reset.py   # (from 001-user-auth)
    ├── test_account_deletion.py # (from 001-user-auth)
    ├── test_task_create.py      # NEW
    ├── test_task_read.py        # NEW
    ├── test_task_update.py      # NEW
    ├── test_task_delete.py      # NEW
    └── test_task_filter_sort.py # NEW
```

**Structure Decision**: Extends existing 001-user-auth structure. New files only for Task-specific functionality. Reuses existing infrastructure (config, database, middleware framework).

## Complexity Tracking

No constitution violations requiring justification. The design follows all principles without exceptions.

## Key Architecture Decisions

### 1. Status Enum with Terminal States

**Decision**: Use Python Enum with explicit transition validation in service layer

**Options Considered**:
- A) Validate transitions in Pydantic schema
- B) Validate transitions in service layer
- C) Use database constraints

**Rationale for B**:
- Business logic belongs in service layer per constitution
- Pydantic handles format validation, not business rules
- Database constraints are inflexible for future changes
- Service layer can provide meaningful error messages

**Implementation Pattern**:
```python
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

TERMINAL_STATUSES = {TaskStatus.COMPLETED, TaskStatus.CANCELLED}

def validate_status_transition(current: TaskStatus, new: TaskStatus) -> None:
    if current in TERMINAL_STATUSES:
        raise InvalidStatusTransitionError(
            f"Cannot change status from {current.value} to {new.value}"
        )
```

### 2. Priority Enum with Sortable Values

**Decision**: Use IntEnum for database-sortable priority values

**Rationale**:
- Allows `ORDER BY priority` in SQL queries
- Maintains type safety in Python
- Clear ordering: urgent(4) > high(3) > medium(2) > low(1)

**Implementation Pattern**:
```python
from enum import IntEnum

class TaskPriority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
```

### 3. Computed `is_overdue` Field

**Decision**: Calculate at read time using `@computed_field` in Pydantic

**Options Considered**:
- A) Store in database, update via scheduled job
- B) Calculate in service layer
- C) Calculate in Pydantic schema with `@computed_field`

**Rationale for C**:
- No stale data risk (always current)
- No background job complexity
- Clean separation (model stores data, schema computes display)
- Pydantic v2's `@computed_field` is purpose-built for this

**Implementation Pattern**:
```python
from pydantic import BaseModel, computed_field
from datetime import datetime, UTC

class TaskRead(BaseModel):
    due_date: datetime | None
    status: TaskStatus
    # ... other fields

    @computed_field
    @property
    def is_overdue(self) -> bool:
        if self.due_date is None:
            return False
        if self.status in {TaskStatus.COMPLETED, TaskStatus.CANCELLED}:
            return False
        return self.due_date < datetime.now(UTC)
```

### 4. Pagination Strategy

**Decision**: Offset-based pagination with total count

**Options Considered**:
- A) Offset-based (page/page_size)
- B) Cursor-based (next_cursor token)
- C) Keyset pagination (after_id)

**Rationale for A**:
- Simple for learning project
- Supports "jump to page X" UI pattern
- Constitution requires pagination for > 100 records (offset works)
- Cursor-based is overkill for expected data volumes

**Implementation Pattern**:
```python
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)

class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
```

### 5. Filtering and Sorting

**Decision**: Query parameters with explicit field validation

**Rationale**:
- RESTful convention for list filtering
- Service layer validates allowed fields
- Prevents SQL injection via field name validation

**Implementation Pattern**:
```python
ALLOWED_SORT_FIELDS = {"created_at", "updated_at", "due_date", "priority", "status"}

class TaskListParams(BaseModel):
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date_from: datetime | None = None
    due_date_to: datetime | None = None
    sort_by: str = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"

    @field_validator("sort_by")
    @classmethod
    def validate_sort_field(cls, v: str) -> str:
        if v not in ALLOWED_SORT_FIELDS:
            raise ValueError(f"Invalid sort field. Allowed: {ALLOWED_SORT_FIELDS}")
        return v
```

### 6. User-Based Rate Limiting

**Decision**: Extend rate limiter to support user ID key

**Rationale**:
- Spec requires per-user rate limiting (not per-IP)
- Same middleware framework as auth rate limiting
- Different configuration (10 req/min vs 5 req/min)

**Implementation Pattern**:
```python
# Rate limiter supports both IP and user-based limiting
rate_limiter = RateLimiter(requests=10, window=60, key_type="user")

# In route handler
@router.post("/tasks")
async def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    rate_limiter: RateLimiter = Depends(get_task_rate_limiter)
):
    rate_limiter.check(key=str(current_user.id))
    # ...
```

## Testing Strategy

### Unit Tests

| Service | Test Cases |
|---------|------------|
| `task_service.create_task` | Valid task, defaults applied, title validation |
| `task_service.get_task` | Found, not found, wrong user (404) |
| `task_service.list_tasks` | Empty list, pagination, filtering, sorting |
| `task_service.update_task` | Valid update, status transitions, empty payload |
| `task_service.delete_task` | Successful delete, not found, wrong user |
| `task_service.validate_status_transition` | Terminal states block transitions |

### Integration Tests

| Endpoint | Test Cases (from acceptance scenarios) |
|----------|----------------------------------------|
| `POST /tasks` | Valid creation (201), title validation (422), defaults, duplicate titles |
| `GET /tasks/{id}` | Found (200), not found (404), wrong user (404), is_overdue calculation |
| `GET /tasks` | Pagination, empty list, filters, sorting, combined filters |
| `PATCH /tasks/{id}` | Valid update (200), status transitions (422), empty payload (422) |
| `DELETE /tasks/{id}` | Successful (204), not found (404), wrong user (404), verify deleted |

### TDD Workflow

1. Write failing test from acceptance scenario
2. Implement minimum code to pass
3. Refactor while keeping tests green
4. Repeat for each acceptance criterion

## Error Handling Strategy

All errors follow the spec's Error Codes table:

```python
# Example error response structure
{
    "code": "TASK_NOT_FOUND",
    "message": "Task not found"
}
```

### Exception Mapping

| Exception Type | HTTP Status | Error Code |
|---------------|-------------|------------|
| `ValidationError` (Pydantic) | 422 | `VALIDATION_ERROR` |
| `TaskNotFoundError` | 404 | `TASK_NOT_FOUND` |
| `InvalidStatusTransitionError` | 422 | `INVALID_STATUS_TRANSITION` |
| `NoFieldsToUpdateError` | 422 | `NO_FIELDS_TO_UPDATE` |
| `InvalidSortFieldError` | 422 | `INVALID_SORT_FIELD` |
| `InvalidDateRangeError` | 422 | `INVALID_DATE_RANGE` |
| `RateLimitError` | 429 | `RATE_LIMIT_EXCEEDED` |

## Dependencies

No new dependencies required beyond 001-user-auth. All functionality uses existing libraries:

- FastAPI for routing
- SQLModel for Task model
- Pydantic v2 for schemas with `@computed_field`

## Integration with 001-user-auth

| Integration Point | Details |
|-------------------|---------|
| User model | Task has `user_id` FK to `users.id` |
| Cascade delete | Task relationship with `cascade="all, delete-orphan"` |
| Authentication | `get_current_user` dependency for all task endpoints |
| Rate limiter | Shared middleware, different config (user key vs IP key) |
| Error handling | Same `ErrorResponse` schema structure |

## Next Steps

1. Run `/sp.tasks` to generate detailed task breakdown
2. Implement Task model (extends User relationship)
3. Follow TDD: write tests first for each acceptance scenario
4. Implement services, then routes
5. Run integration tests against test database
