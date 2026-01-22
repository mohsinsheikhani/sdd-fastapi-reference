# Quickstart: Task CRUD Operations

**Feature**: 002-task-crud | **Date**: 2026-01-22
**Depends On**: 001-user-auth (must be implemented first)

This guide provides step-by-step instructions to test the Task CRUD API.

## Prerequisites

- Python 3.12+
- UV package manager
- PostgreSQL database (configured from 001-user-auth)
- 001-user-auth feature implemented and working
- Valid user account for testing

## API Usage Examples

All task endpoints require authentication. First, obtain an access token:

```bash
# Login to get access token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}' \
  | jq -r '.access_token')
```

### Create a Task

```bash
# Create task with all fields
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "priority": "high",
    "due_date": "2026-01-25T17:00:00Z"
  }'
```

**Response (201 Created)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "status": "pending",
  "priority": "high",
  "due_date": "2026-01-25T17:00:00Z",
  "is_overdue": false,
  "created_at": "2026-01-22T12:00:00Z",
  "updated_at": "2026-01-22T12:00:00Z"
}
```

```bash
# Create task with only title (uses defaults)
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Call mom"}'
```

### Get a Single Task

```bash
curl -X GET http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $TOKEN"
```

### List Tasks (with Pagination)

```bash
# Default: first 50 tasks, sorted by created_at desc
curl -X GET "http://localhost:8000/api/v1/tasks" \
  -H "Authorization: Bearer $TOKEN"
```

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": "...",
      "title": "Buy groceries",
      "status": "pending",
      "priority": "high",
      "is_overdue": false,
      "..."
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "total_pages": 3
}
```

```bash
# Second page with custom page size
curl -X GET "http://localhost:8000/api/v1/tasks?page=2&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

### Filter Tasks

```bash
# Filter by status
curl -X GET "http://localhost:8000/api/v1/tasks?status=pending" \
  -H "Authorization: Bearer $TOKEN"

# Filter by priority
curl -X GET "http://localhost:8000/api/v1/tasks?priority=high" \
  -H "Authorization: Bearer $TOKEN"

# Filter by due date range
curl -X GET "http://localhost:8000/api/v1/tasks?due_date_from=2026-01-20T00:00:00Z&due_date_to=2026-01-31T23:59:59Z" \
  -H "Authorization: Bearer $TOKEN"

# Combine multiple filters (AND logic)
curl -X GET "http://localhost:8000/api/v1/tasks?status=pending&priority=high" \
  -H "Authorization: Bearer $TOKEN"
```

### Sort Tasks

```bash
# Sort by due date ascending (earliest first)
curl -X GET "http://localhost:8000/api/v1/tasks?sort_by=due_date&sort_order=asc" \
  -H "Authorization: Bearer $TOKEN"

# Sort by priority descending (urgent first)
curl -X GET "http://localhost:8000/api/v1/tasks?sort_by=priority&sort_order=desc" \
  -H "Authorization: Bearer $TOKEN"
```

### Update a Task

```bash
# Update status to completed
curl -X PATCH http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'

# Update multiple fields
curl -X PATCH http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated title",
    "priority": "urgent",
    "due_date": "2026-01-30T12:00:00Z"
  }'
```

### Delete a Task

```bash
curl -X DELETE http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $TOKEN"
```

**Response (204 No Content)**: Empty response body

---

## Running Tests

### Run Task-Specific Tests

```bash
# Run all task tests
uv run pytest tests/integration/test_task_*.py -v

# Run create tests only
uv run pytest tests/integration/test_task_create.py -v

# Run with coverage
uv run pytest tests/integration/test_task_*.py --cov=src/services/task_service --cov-report=term-missing
```

### Test Categories

| Test File | Coverage |
|-----------|----------|
| `test_task_create.py` | Task creation, validation, defaults |
| `test_task_read.py` | Single task retrieval, is_overdue |
| `test_task_update.py` | Updates, status transitions |
| `test_task_delete.py` | Deletion, verification |
| `test_task_filter_sort.py` | List, pagination, filtering, sorting |

---

## TDD Workflow

Follow this process for each task-related acceptance scenario:

1. **Read acceptance scenario** from `spec.md`
2. **Write failing test** based on scenario
3. **Run test** to confirm it fails
4. **Implement minimum code** to pass
5. **Run test again** to confirm it passes
6. **Refactor** if needed while keeping tests green

### Example: Testing Task Creation

```python
# tests/integration/test_task_create.py

def test_create_task_with_all_fields(auth_client, auth_headers):
    """Acceptance scenario 1.1: Create task with all fields."""
    response = auth_client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={
            "title": "Buy groceries",
            "description": "Milk, eggs, bread",
            "priority": "high",
            "due_date": "2026-01-25T17:00:00Z"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Buy groceries"
    assert data["status"] == "pending"  # Default
    assert data["priority"] == "high"
    assert "id" in data
    assert "is_overdue" in data

def test_create_task_with_only_title(auth_client, auth_headers):
    """Acceptance scenario 1.2: Create task with minimum fields."""
    response = auth_client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={"title": "Call mom"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"  # Default
    assert data["priority"] == "medium"  # Default
    assert data["description"] is None

def test_create_task_empty_title_rejected(auth_client, auth_headers):
    """Acceptance scenario 1.3: Empty title rejected."""
    response = auth_client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={"title": "   "}  # Whitespace only
    )
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
```

### Example: Testing Status Transitions

```python
# tests/integration/test_task_update.py

def test_cannot_reopen_completed_task(auth_client, auth_headers, completed_task):
    """Acceptance scenario 3.4: Completed tasks cannot be reopened."""
    response = auth_client.patch(
        f"/api/v1/tasks/{completed_task.id}",
        headers=auth_headers,
        json={"status": "pending"}
    )
    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_STATUS_TRANSITION"

def test_cannot_reopen_cancelled_task(auth_client, auth_headers, cancelled_task):
    """Acceptance scenario 3.5: Cancelled tasks cannot be reopened."""
    response = auth_client.patch(
        f"/api/v1/tasks/{cancelled_task.id}",
        headers=auth_headers,
        json={"status": "in_progress"}
    )
    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_STATUS_TRANSITION"
```

---

## Test Fixtures

Add these fixtures to `conftest.py`:

```python
import pytest
from datetime import datetime, timedelta, UTC

@pytest.fixture
def auth_headers(access_token):
    """Headers with valid access token."""
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def sample_task(auth_client, auth_headers):
    """Create a sample task for testing."""
    response = auth_client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={"title": "Test task"}
    )
    return response.json()

@pytest.fixture
def completed_task(auth_client, auth_headers, sample_task):
    """Create a completed task for testing transitions."""
    auth_client.patch(
        f"/api/v1/tasks/{sample_task['id']}",
        headers=auth_headers,
        json={"status": "completed"}
    )
    return sample_task

@pytest.fixture
def overdue_task(auth_client, auth_headers):
    """Create an overdue task for testing is_overdue."""
    past_date = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    response = auth_client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={"title": "Overdue task", "due_date": past_date}
    )
    return response.json()
```

---

## Error Handling Examples

### Validation Errors

```bash
# Empty title
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": ""}'
# Response: 422 {"code": "VALIDATION_ERROR", "message": "Title cannot be empty..."}

# Title too long
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "This title is way too long and exceeds the seventy character limit that is enforced"}'
# Response: 422 {"code": "VALIDATION_ERROR", "message": "Title must be at most 70 characters"}
```

### Business Rule Errors

```bash
# Trying to reopen completed task
curl -X PATCH http://localhost:8000/api/v1/tasks/COMPLETED_TASK_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "pending"}'
# Response: 422 {"code": "INVALID_STATUS_TRANSITION", "message": "Cannot change status from 'completed'..."}

# Empty update payload
curl -X PATCH http://localhost:8000/api/v1/tasks/TASK_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
# Response: 422 {"code": "NO_FIELDS_TO_UPDATE", "message": "No fields provided for update"}
```

### Not Found

```bash
# Non-existent task
curl -X GET http://localhost:8000/api/v1/tasks/00000000-0000-0000-0000-000000000000 \
  -H "Authorization: Bearer $TOKEN"
# Response: 404 {"code": "TASK_NOT_FOUND", "message": "Task not found"}

# Another user's task (same response to prevent enumeration)
curl -X GET http://localhost:8000/api/v1/tasks/OTHER_USER_TASK_ID \
  -H "Authorization: Bearer $TOKEN"
# Response: 404 {"code": "TASK_NOT_FOUND", "message": "Task not found"}
```

---

## Next Steps

After implementation, proceed with:

1. Run `/sp.tasks` to generate detailed task breakdown
2. Implement Task model (add relationship to User)
3. Follow TDD for each acceptance scenario
4. Implement service layer with status validation
5. Implement routes with proper error handling
6. Run full test suite to verify all acceptance criteria
