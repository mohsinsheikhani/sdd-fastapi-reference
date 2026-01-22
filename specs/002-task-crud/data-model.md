# Data Model: Task CRUD Operations

**Feature**: 002-task-crud | **Date**: 2026-01-22

This document defines all database entities, their fields, relationships, validation rules, and state transitions for the Task CRUD feature.

## Entity Diagram

```
┌─────────────────────────────────────────────┐
│                    User                      │
│              (from 001-user-auth)            │
├─────────────────────────────────────────────┤
│ id: UUID (PK)                               │
│ name: str                                    │
│ email: str                                   │
│ ...                                          │
├─────────────────────────────────────────────┤
│ tasks: list[Task] (1:N)                     │
└─────────────────────────────────────────────┘
           │
           │ 1:N (cascade delete)
           ▼
┌─────────────────────────────────────────────┐
│                    Task                      │
├─────────────────────────────────────────────┤
│ id: UUID (PK)                               │
│ user_id: UUID (FK → User.id)                │
│ title: str [1-70 chars, required]           │
│ description: str | None [max 500]           │
│ status: TaskStatus [default: pending]       │
│ priority: TaskPriority [default: medium]    │
│ due_date: datetime | None                   │
│ created_at: datetime                        │
│ updated_at: datetime                        │
├─────────────────────────────────────────────┤
│ user: User (N:1)                            │
│ is_overdue: bool [computed, not stored]     │
└─────────────────────────────────────────────┘
```

## Enum Definitions

### TaskStatus

Represents the current state of a task. Completed and cancelled are terminal states.

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

### TaskPriority

Represents task importance level. Uses IntEnum for database sorting.

```python
from enum import IntEnum

class TaskPriority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

DEFAULT_PRIORITY = TaskPriority.MEDIUM
```

---

## Entity Definitions

### Task

Primary entity representing a user's to-do item.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `UUID` | PK, default uuid4 | Unique task identifier |
| `user_id` | `UUID` | FK → User.id, indexed | Owner of the task |
| `title` | `str` | 1-70 chars, not whitespace-only | Task title |
| `description` | `str \| None` | max 500 chars | Optional task description |
| `status` | `TaskStatus` | default PENDING | Current task state |
| `priority` | `TaskPriority` | default MEDIUM | Task importance level |
| `due_date` | `datetime \| None` | nullable | Optional deadline (past dates allowed) |
| `created_at` | `datetime` | auto-set UTC | Task creation timestamp |
| `updated_at` | `datetime` | auto-update UTC | Last modification timestamp |

**SQLModel Definition**:
```python
import uuid
from datetime import datetime, UTC
from sqlmodel import SQLModel, Field, Relationship

class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    title: str = Field(min_length=1, max_length=70)
    description: str | None = Field(default=None, max_length=500)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    due_date: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)}
    )

    # Relationship
    user: "User" = Relationship(back_populates="tasks")
```

**User Model Update** (add to existing User model):
```python
# In User model from 001-user-auth
class User(SQLModel, table=True):
    # ... existing fields ...

    # Add this relationship
    tasks: list["Task"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
```

**Validation Rules**:
- Title: 1-70 characters, cannot be whitespace-only (stripped then validated)
- Description: Optional, max 500 characters (empty string treated as None)
- Status: Must be valid enum value
- Priority: Must be valid enum value
- Due date: Optional, past dates allowed for backdating/importing

---

## State Transitions

### Task Status States

```
                    ┌──────────────────┐
                    │     Created      │
                    │  (status=pending)│
                    └────────┬─────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │  in_progress  │ │   completed   │ │   cancelled   │
    │               │ │   (terminal)  │ │   (terminal)  │
    └───────┬───────┘ └───────────────┘ └───────────────┘
            │                 ▲                ▲
            │                 │                │
            ├─────────────────┘                │
            │                                  │
            └──────────────────────────────────┘

    ┌─────────────────────────────────────────────┐
    │               pending                        │
    │  ┌──────────────────────────────────────┐   │
    │  │         ↓           ↓           ↓    │   │
    │  │   in_progress   completed   cancelled │   │
    │  │         │           ↑           ↑    │   │
    │  │         └───────────┴───────────┘    │   │
    │  └──────────────────────────────────────┘   │
    └─────────────────────────────────────────────┘

Note: pending ↔ in_progress is bidirectional
      completed and cancelled are terminal (no transitions out)
```

**Transition Matrix**:

| Current Status | → pending | → in_progress | → completed | → cancelled |
|----------------|-----------|---------------|-------------|-------------|
| pending | - | ✓ | ✓ | ✓ |
| in_progress | ✓ | - | ✓ | ✓ |
| **completed** | ✗ | ✗ | - | ✗ |
| **cancelled** | ✗ | ✗ | ✗ | - |

---

## Computed Fields

### is_overdue

Computed at read time, not stored in database.

**Logic**:
```python
def compute_is_overdue(task: Task) -> bool:
    # No due date = not overdue
    if task.due_date is None:
        return False
    # Terminal states = not overdue (even if past due date)
    if task.status in TERMINAL_STATUSES:
        return False
    # Past due date with active status = overdue
    return task.due_date < datetime.now(UTC)
```

**Examples**:

| due_date | status | is_overdue |
|----------|--------|------------|
| None | pending | False |
| 2026-01-20 (past) | pending | True |
| 2026-01-20 (past) | completed | False |
| 2026-01-20 (past) | cancelled | False |
| 2026-01-25 (future) | pending | False |

---

## Indexes

| Table | Index | Columns | Purpose |
|-------|-------|---------|---------|
| `tasks` | `ix_tasks_user_id` | `user_id` | Filter tasks by user |
| `tasks` | `ix_tasks_user_status` | `user_id, status` | Filter by user + status |
| `tasks` | `ix_tasks_user_priority` | `user_id, priority` | Filter/sort by priority |
| `tasks` | `ix_tasks_user_due_date` | `user_id, due_date` | Filter/sort by due date |

---

## Pydantic Schemas

### Task Create Schema

```python
from pydantic import BaseModel, Field, field_validator

class TaskCreate(BaseModel):
    """Schema for task creation."""
    title: str = Field(min_length=1, max_length=70)
    description: str | None = Field(default=None, max_length=500)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    due_date: datetime | None = Field(default=None)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty or whitespace-only")
        return v

    @field_validator("description")
    @classmethod
    def normalize_description(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            return v if v else None
        return None
```

### Task Update Schema

```python
class TaskUpdate(BaseModel):
    """Schema for task update (PATCH semantics)."""
    title: str | None = Field(default=None, min_length=1, max_length=70)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Title cannot be empty or whitespace-only")
        return v
```

### Task Read Schema

```python
from pydantic import BaseModel, Field, ConfigDict, computed_field

class TaskRead(BaseModel):
    """Schema for task response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def is_overdue(self) -> bool:
        if self.due_date is None:
            return False
        if self.status in TERMINAL_STATUSES:
            return False
        return self.due_date < datetime.now(UTC)
```

### Pagination Schemas

```python
from math import ceil

class PaginationParams(BaseModel):
    """Pagination input parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

class PaginatedResponse[T](BaseModel):
    """Paginated response wrapper."""
    items: list[T]
    total: int
    page: int
    page_size: int

    @computed_field
    @property
    def total_pages(self) -> int:
        return ceil(self.total / self.page_size) if self.total > 0 else 0
```

### Filter and Sort Schemas

```python
from typing import Literal

ALLOWED_SORT_FIELDS = frozenset({
    "created_at", "updated_at", "due_date", "priority", "status"
})

class TaskListParams(BaseModel):
    """Combined filter and sort parameters."""
    # Filters
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date_from: datetime | None = None
    due_date_to: datetime | None = None

    # Sorting
    sort_by: str = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"

    @field_validator("sort_by")
    @classmethod
    def validate_sort_field(cls, v: str) -> str:
        if v not in ALLOWED_SORT_FIELDS:
            raise ValueError(f"Invalid sort field. Allowed: {sorted(ALLOWED_SORT_FIELDS)}")
        return v

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if self.due_date_from and self.due_date_to:
            if self.due_date_from > self.due_date_to:
                raise ValueError("due_date_from must be before due_date_to")
        return self
```

### Error Schemas

```python
class ErrorResponse(BaseModel):
    """Standard error response (same as 001-user-auth)."""
    code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error message")
```

---

## Database Migration

Add tasks table (extends existing schema from 001-user-auth):

```sql
-- Create tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(70) NOT NULL,
    description VARCHAR(500),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 2,
    due_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX ix_tasks_user_id ON tasks(user_id);
CREATE INDEX ix_tasks_user_status ON tasks(user_id, status);
CREATE INDEX ix_tasks_user_priority ON tasks(user_id, priority);
CREATE INDEX ix_tasks_user_due_date ON tasks(user_id, due_date);

-- Add constraint for valid status values
ALTER TABLE tasks ADD CONSTRAINT chk_task_status
    CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled'));

-- Add constraint for valid priority values
ALTER TABLE tasks ADD CONSTRAINT chk_task_priority
    CHECK (priority BETWEEN 1 AND 4);
```

---

## Constraints Summary

| Entity | Field | Constraint | Source |
|--------|-------|------------|--------|
| Task | title | 1-70 chars, not whitespace-only | Spec constraints |
| Task | description | Max 500 chars | Spec constraints |
| Task | status | Enum: pending, in_progress, completed, cancelled | FR-004 |
| Task | priority | Enum: low(1), medium(2), high(3), urgent(4) | FR-005 |
| Task | due_date | Optional, past dates allowed | FR-006 |
| Task | user_id | FK to users, cascade delete | FR-008, FR-022 (auth) |
| List | page_size | Default 50, max 100 | FR-013 |

---

## Service Layer Responsibilities

### Status Transition Validation

```python
def validate_status_transition(current: TaskStatus, new: TaskStatus) -> None:
    """Validate that status transition is allowed.

    Args:
        current: Current task status
        new: Requested new status

    Raises:
        InvalidStatusTransitionError: If transition is not allowed
    """
    if current in TERMINAL_STATUSES:
        raise InvalidStatusTransitionError(
            f"Cannot change status from '{current.value}' - task is in terminal state"
        )
```

### Update Validation

```python
def validate_update(update_data: TaskUpdate) -> dict:
    """Validate and extract update fields.

    Args:
        update_data: Update request data

    Returns:
        Dict of fields to update

    Raises:
        NoFieldsToUpdateError: If no fields provided
    """
    update_dict = update_data.model_dump(exclude_unset=True)
    if not update_dict:
        raise NoFieldsToUpdateError("No fields provided for update")
    return update_dict
```
