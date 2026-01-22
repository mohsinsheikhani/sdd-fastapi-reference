# Research: Task CRUD Operations

**Feature**: 002-task-crud | **Date**: 2026-01-22

This document resolves technology decisions and documents research findings for the Task CRUD feature. Since this feature builds on 001-user-auth, most technology choices are inherited.

## Technology Decisions

### 1. Task Status Enum

**Decision**: Use `str, Enum` for JSON serialization and database storage

**Research Findings**:
- SQLModel/SQLAlchemy stores Enum as VARCHAR by default
- `str, Enum` combination allows direct JSON serialization
- Terminal status validation must be in service layer (business rule)

**Implementation Pattern**:
```python
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Terminal states that cannot transition to other states
TERMINAL_STATUSES = frozenset({TaskStatus.COMPLETED, TaskStatus.CANCELLED})
```

**State Transition Matrix**:
| From/To | pending | in_progress | completed | cancelled |
|---------|---------|-------------|-----------|-----------|
| pending | - | ✓ | ✓ | ✓ |
| in_progress | ✓ | - | ✓ | ✓ |
| completed | ✗ | ✗ | - | ✗ |
| cancelled | ✗ | ✗ | ✗ | - |

---

### 2. Task Priority Enum

**Decision**: Use `IntEnum` for sortable database values

**Research Findings**:
- `IntEnum` allows `ORDER BY priority` in SQL
- Integer values stored directly in database
- Maintains type safety while enabling sorting

**Implementation Pattern**:
```python
from enum import IntEnum

class TaskPriority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

# Default priority
DEFAULT_PRIORITY = TaskPriority.MEDIUM
```

**Sort Order**:
- Descending: URGENT (4) → HIGH (3) → MEDIUM (2) → LOW (1)
- Ascending: LOW (1) → MEDIUM (2) → HIGH (3) → URGENT (4)

---

### 3. Computed Field: `is_overdue`

**Decision**: Use Pydantic v2's `@computed_field` decorator

**Research Findings**:
- Pydantic v2 introduced `@computed_field` for derived properties
- Field is computed at serialization time (not stored)
- Always current (no stale data)
- Included in JSON output automatically

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
        if self.status in TERMINAL_STATUSES:
            return False
        return self.due_date < datetime.now(UTC)
```

**Behavior**:
- `None` due_date → `False`
- Completed/cancelled tasks → `False` (regardless of due_date)
- Past due_date + active status → `True`

---

### 4. Pagination Implementation

**Decision**: Offset-based pagination with metadata

**Research Findings**:
- Offset pagination: `OFFSET (page-1) * page_size LIMIT page_size`
- Requires separate `COUNT(*)` query for total
- Simple for < 100k records (learning project scope)
- Constitution requires pagination for > 100 records

**Implementation Pattern**:
```python
from math import ceil

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int

    @computed_field
    @property
    def total_pages(self) -> int:
        return ceil(self.total / self.page_size) if self.total > 0 else 0
```

**Query Pattern**:
```python
def list_tasks(session: Session, user_id: UUID, params: PaginationParams) -> PaginatedResponse[Task]:
    # Count query
    total = session.exec(
        select(func.count()).select_from(Task).where(Task.user_id == user_id)
    ).one()

    # Data query with pagination
    tasks = session.exec(
        select(Task)
        .where(Task.user_id == user_id)
        .offset(params.offset)
        .limit(params.page_size)
    ).all()

    return PaginatedResponse(items=tasks, total=total, **params.model_dump())
```

---

### 5. Filtering Strategy

**Decision**: AND-logic filters via query parameters

**Research Findings**:
- RESTful convention: filters as query params
- Multiple filters combine with AND logic
- Each filter is optional
- Empty filter returns all (within pagination)

**Implementation Pattern**:
```python
class TaskFilterParams(BaseModel):
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date_from: datetime | None = None
    due_date_to: datetime | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if self.due_date_from and self.due_date_to:
            if self.due_date_from > self.due_date_to:
                raise ValueError("due_date_from must be before due_date_to")
        return self

def apply_filters(query: Select, filters: TaskFilterParams) -> Select:
    if filters.status:
        query = query.where(Task.status == filters.status)
    if filters.priority:
        query = query.where(Task.priority == filters.priority)
    if filters.due_date_from:
        query = query.where(Task.due_date >= filters.due_date_from)
    if filters.due_date_to:
        query = query.where(Task.due_date <= filters.due_date_to)
    return query
```

---

### 6. Sorting Strategy

**Decision**: Whitelist allowed sort fields, validate in schema

**Research Findings**:
- Dynamic field names can lead to SQL injection
- Whitelist approach prevents injection
- Pydantic validator enforces allowed fields
- Default: `created_at DESC`

**Implementation Pattern**:
```python
ALLOWED_SORT_FIELDS = frozenset({
    "created_at",
    "updated_at",
    "due_date",
    "priority",
    "status"
})

class TaskSortParams(BaseModel):
    sort_by: str = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"

    @field_validator("sort_by")
    @classmethod
    def validate_sort_field(cls, v: str) -> str:
        if v not in ALLOWED_SORT_FIELDS:
            raise ValueError(f"Invalid sort field. Allowed: {sorted(ALLOWED_SORT_FIELDS)}")
        return v

def apply_sorting(query: Select, sort: TaskSortParams) -> Select:
    column = getattr(Task, sort.sort_by)
    if sort.sort_order == "desc":
        column = column.desc()
    return query.order_by(column)
```

---

### 7. User-Based Rate Limiting

**Decision**: Extend existing rate limiter with configurable key type

**Research Findings**:
- Auth endpoints: 5 req/min per IP
- Task creation: 10 req/min per user
- Same sliding window algorithm
- Different key extraction (IP vs user_id)

**Implementation Pattern**:
```python
from enum import Enum

class RateLimitKeyType(str, Enum):
    IP = "ip"
    USER = "user"

class RateLimiter:
    def __init__(self, requests: int, window: int, key_type: RateLimitKeyType = RateLimitKeyType.IP):
        self.requests = requests
        self.window = window
        self.key_type = key_type
        self.clients: dict[str, list[float]] = defaultdict(list)

    def get_key(self, request: Request, user_id: str | None = None) -> str:
        if self.key_type == RateLimitKeyType.USER:
            if user_id is None:
                raise ValueError("user_id required for user-based rate limiting")
            return f"user:{user_id}"
        return request.client.host or "unknown"

# Factory functions for different limiters
def get_auth_rate_limiter() -> RateLimiter:
    return RateLimiter(requests=5, window=60, key_type=RateLimitKeyType.IP)

def get_task_rate_limiter() -> RateLimiter:
    return RateLimiter(requests=10, window=60, key_type=RateLimitKeyType.USER)
```

---

### 8. PATCH Update Semantics

**Decision**: Exclude unset fields using Pydantic's `model_dump(exclude_unset=True)`

**Research Findings**:
- PATCH should update only provided fields
- `exclude_unset=True` distinguishes "not provided" from "set to None"
- Empty payload (all unset) → error
- Service validates at least one field provided

**Implementation Pattern**:
```python
class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None

def update_task(session: Session, task: Task, update_data: TaskUpdate) -> Task:
    update_dict = update_data.model_dump(exclude_unset=True)

    if not update_dict:
        raise NoFieldsToUpdateError("No fields provided for update")

    # Validate status transition if status is being updated
    if "status" in update_dict:
        validate_status_transition(task.status, update_dict["status"])

    for field, value in update_dict.items():
        setattr(task, field, value)

    task.updated_at = datetime.now(UTC)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task
```

---

### 9. Title Validation

**Decision**: Use Pydantic validators with whitespace stripping

**Research Findings**:
- Max 70 characters per spec
- Cannot be whitespace-only
- Strip whitespace then validate
- Empty after strip = validation error

**Implementation Pattern**:
```python
class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=70)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty or whitespace-only")
        return v
```

---

## Best Practices Applied

### SQLModel Best Practices

1. **Use relationships for cascade delete** - Tasks deleted when User deleted
2. **Index foreign keys** - `user_id` indexed for efficient filtering
3. **Use proper typing** - Enum types stored correctly
4. **Separate model from schema** - SQLModel for DB, Pydantic for API

### Testing Best Practices

1. **Test user isolation** - Verify user A cannot see user B's tasks
2. **Test pagination edges** - Empty page, last page, page beyond total
3. **Test status transitions** - All valid and invalid transitions
4. **Test computed fields** - `is_overdue` with various date/status combinations

### Security Best Practices

1. **Always filter by user_id** - Never expose other users' tasks
2. **Return 404 for unauthorized** - Prevent task ID enumeration
3. **Validate sort field whitelist** - Prevent SQL injection
4. **Rate limit task creation** - Prevent spam/abuse

---

## Resolved Clarifications

| Item | Resolution |
|------|------------|
| Status transitions | Terminal states (completed/cancelled) cannot transition |
| Priority sorting | IntEnum values: low=1, medium=2, high=3, urgent=4 |
| is_overdue calculation | Computed at read time, false for completed/cancelled |
| Pagination | Offset-based, default 50, max 100 per page |
| Rate limiting | 10 req/min per user on task creation only |
| Empty PATCH | Returns 422 with NO_FIELDS_TO_UPDATE code |
