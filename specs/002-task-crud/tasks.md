# Tasks: Task CRUD Operations

**Input**: Design documents from `/specs/002-task-crud/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/tasks-api.yaml ✓, quickstart.md ✓
**Depends On**: `001-user-auth` (must be fully implemented first)

**Tests**: Tests are included per TDD workflow specified in plan.md and quickstart.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US5)
- Include exact file paths in descriptions

## Path Conventions

- **Structure**: `src/`, `tests/` at repository root (extends 001-user-auth)
- Based on plan.md project structure

---

## Phase 1: Setup (Feature Infrastructure)

**Purpose**: Add task-specific infrastructure to existing 001-user-auth codebase

- [ ] T001 Add task-specific exceptions to src/core/exceptions.py (TaskNotFoundError, InvalidStatusTransitionError, NoFieldsToUpdateError, InvalidSortFieldError, InvalidDateRangeError)
- [ ] T002 [P] Create TaskStatus enum (str, Enum) in src/models/task.py with PENDING, IN_PROGRESS, COMPLETED, CANCELLED and TERMINAL_STATUSES frozenset
- [ ] T003 [P] Create TaskPriority IntEnum in src/models/task.py with LOW=1, MEDIUM=2, HIGH=3, URGENT=4
- [ ] T004 [P] Create pagination schemas (PaginationParams, PaginatedResponse) in src/schemas/pagination.py
- [ ] T005 Extend rate limiter to support user-based rate limiting (key_type parameter) in src/middleware/rate_limit.py

### ✅ Checkpoint 1: Setup Complete

**Verification**:
```bash
# All must pass:
uv run python -c "from src.core.exceptions import TaskNotFoundError, InvalidStatusTransitionError"
uv run python -c "from src.models.task import TaskStatus, TaskPriority, TERMINAL_STATUSES"
uv run python -c "from src.schemas.pagination import PaginationParams, PaginatedResponse"
uv run python -c "from src.middleware.rate_limit import RateLimiter; r = RateLimiter(10, 60, 'user')"
```

**Exit Criteria**:
- [ ] All task-specific exceptions are defined and importable
- [ ] TaskStatus enum has 4 values and TERMINAL_STATUSES contains completed/cancelled
- [ ] TaskPriority IntEnum has 4 values with correct ordering
- [ ] PaginationParams and PaginatedResponse work with generics
- [ ] RateLimiter supports both IP and user key types

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Task infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create Task SQLModel with all fields per data-model.md in src/models/task.py (id, user_id FK, title, description, status, priority, due_date, created_at, updated_at)
- [ ] T007 Update User model to add tasks relationship with cascade="all, delete-orphan" in src/models/user.py
- [ ] T008 [P] Create TaskCreate schema with title validation in src/schemas/task.py
- [ ] T009 [P] Create TaskUpdate schema (PATCH semantics) in src/schemas/task.py
- [ ] T010 [P] Create TaskRead schema with @computed_field is_overdue in src/schemas/task.py
- [ ] T011 [P] Create TaskListParams schema (filters + sorting with validation) in src/schemas/task.py
- [ ] T012 Add exception handlers for task-specific exceptions in src/main.py
- [ ] T013 Create tasks router skeleton in src/api/v1/tasks.py
- [ ] T014 Wire tasks router to v1 router in src/api/v1/router.py
- [ ] T015 Add task fixtures (sample_task, completed_task, cancelled_task, overdue_task) to tests/conftest.py

### ✅ Checkpoint 2: Foundation Ready

**Verification**:
```bash
# All must pass:
uv run python -c "from src.models.task import Task; print(Task.__tablename__)"
uv run python -c "from src.models.user import User; print('tasks' in dir(User))"
uv run python -c "from src.schemas.task import TaskCreate, TaskUpdate, TaskRead, TaskListParams"
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 &
sleep 2
curl http://localhost:8000/docs | grep -q "tasks"  # Tasks endpoints visible in docs
pkill -f uvicorn
```

**Exit Criteria**:
- [ ] Task model has all fields per data-model.md
- [ ] User model has tasks relationship configured
- [ ] All task schemas are defined with proper validation
- [ ] TaskRead includes computed is_overdue field
- [ ] Tasks router is wired and appears in OpenAPI docs
- [ ] Test fixtures are available

**Gate**: User story implementation may now begin

---

## Phase 3: User Story 1 - Create a New Task (Priority: P1) 🎯 MVP

**Goal**: Allow authenticated users to create tasks with title, optional description, priority, and due date

**Independent Test**: Submit task creation with title "Buy groceries", priority "high", due date tomorrow → verify HTTP 201 with task ID, title, status "pending", priority, due date, timestamps

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T016 [P] [US1] Integration test for valid task creation with all fields (201) in tests/integration/test_task_create.py
- [ ] T017 [P] [US1] Integration test for task creation with only title (201, defaults applied) in tests/integration/test_task_create.py
- [ ] T018 [P] [US1] Integration test for empty/whitespace title rejected (422) in tests/integration/test_task_create.py
- [ ] T019 [P] [US1] Integration test for title exceeding 70 chars (422) in tests/integration/test_task_create.py
- [ ] T020 [P] [US1] Integration test for description exceeding 500 chars (422) in tests/integration/test_task_create.py
- [ ] T021 [P] [US1] Integration test for invalid priority value (422) in tests/integration/test_task_create.py
- [ ] T022 [P] [US1] Integration test for past due date allowed (201) in tests/integration/test_task_create.py
- [ ] T023 [P] [US1] Integration test for duplicate titles allowed (201) in tests/integration/test_task_create.py
- [ ] T024 [P] [US1] Integration test for rate limiting (429 after 10 req/min) in tests/integration/test_task_create.py

### Implementation for User Story 1

- [ ] T025 [US1] Implement create_task function in src/services/task_service.py (associate with user, apply defaults)
- [ ] T026 [US1] Implement get_task_rate_limiter dependency returning user-based limiter in src/api/deps.py
- [ ] T027 [US1] Implement POST /tasks endpoint in src/api/v1/tasks.py (rate limited, requires auth)
- [ ] T028 [US1] Run task creation tests to verify all scenarios pass

### ✅ Checkpoint 3: Task Creation Functional

**Verification**:
```bash
# Run creation tests:
uv run pytest tests/integration/test_task_create.py -v

# Manual API test:
# 1. Login to get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}' | jq -r '.access_token')

# 2. Create task with all fields
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy groceries", "description": "Milk, eggs", "priority": "high", "due_date": "2026-01-25T17:00:00Z"}'
# Expected: HTTP 201 with task data, status=pending

# 3. Create task with only title
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Call mom"}'
# Expected: HTTP 201 with priority=medium, status=pending
```

**Exit Criteria**:
- [ ] All 9 task creation tests pass (T016-T024)
- [ ] POST /api/v1/tasks returns 201 with valid input
- [ ] Default status is "pending", default priority is "medium"
- [ ] Title validation enforces 1-70 chars, no whitespace-only
- [ ] Rate limiting enforces 10 req/min per user

**Deliverable**: Users can create tasks (MVP v0.1)

---

## Phase 4: User Story 2 - View Tasks (Priority: P1) 🎯 MVP

**Goal**: Allow users to view single task by ID or list all tasks with pagination

**Independent Test**: Retrieve task by ID → verify all fields returned including is_overdue indicator

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T029 [P] [US2] Integration test for get task by ID (200) with all fields in tests/integration/test_task_read.py
- [ ] T030 [P] [US2] Integration test for task not found (404 TASK_NOT_FOUND) in tests/integration/test_task_read.py
- [ ] T031 [P] [US2] Integration test for another user's task returns 404 (not 403) in tests/integration/test_task_read.py
- [ ] T032 [P] [US2] Integration test for is_overdue calculation (past due + active status) in tests/integration/test_task_read.py
- [ ] T033 [P] [US2] Integration test for list tasks default pagination (50 items) in tests/integration/test_task_read.py
- [ ] T034 [P] [US2] Integration test for list tasks with page/page_size params in tests/integration/test_task_read.py
- [ ] T035 [P] [US2] Integration test for empty task list returns empty array with metadata in tests/integration/test_task_read.py

### Implementation for User Story 2

- [ ] T036 [P] [US2] Implement get_task function in src/services/task_service.py (user scoped, 404 if not found or wrong user)
- [ ] T037 [P] [US2] Implement list_tasks function with pagination in src/services/task_service.py
- [ ] T038 [US2] Implement GET /tasks/{task_id} endpoint in src/api/v1/tasks.py
- [ ] T039 [US2] Implement GET /tasks endpoint with pagination params in src/api/v1/tasks.py
- [ ] T040 [US2] Run task retrieval tests to verify all scenarios pass

### ✅ Checkpoint 4: Task Retrieval Functional (MVP Complete)

**Verification**:
```bash
# Run read tests:
uv run pytest tests/integration/test_task_read.py -v

# Manual API test:
# 1. Get single task
curl -X GET http://localhost:8000/api/v1/tasks/TASK_ID_HERE \
  -H "Authorization: Bearer $TOKEN"
# Expected: HTTP 200 with task including is_overdue field

# 2. List tasks
curl -X GET "http://localhost:8000/api/v1/tasks" \
  -H "Authorization: Bearer $TOKEN"
# Expected: HTTP 200 with items array, total, page, page_size, total_pages

# 3. Paginate
curl -X GET "http://localhost:8000/api/v1/tasks?page=2&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

**Exit Criteria**:
- [ ] All 7 task retrieval tests pass (T029-T035)
- [ ] GET /api/v1/tasks/{id} returns 200 with all fields
- [ ] GET /api/v1/tasks returns paginated response with metadata
- [ ] is_overdue computed correctly (false for completed/cancelled, true for past due + active)
- [ ] User isolation: cannot see other users' tasks (404)

**Deliverable**: Users can create AND view tasks (MVP v0.2)

**🎯 MVP MILESTONE**: Basic task management is now usable

---

## Phase 5: User Story 3 - Update a Task (Priority: P2)

**Goal**: Allow users to modify task details using PATCH semantics with status transition validation

**Independent Test**: Update task status to "completed" → verify change persists and updated_at refreshed

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T041 [P] [US3] Integration test for update description (200) in tests/integration/test_task_update.py
- [ ] T042 [P] [US3] Integration test for update status pending → in_progress (200) in tests/integration/test_task_update.py
- [ ] T043 [P] [US3] Integration test for update status to completed (200) in tests/integration/test_task_update.py
- [ ] T044 [P] [US3] Integration test for completed → pending blocked (422 INVALID_STATUS_TRANSITION) in tests/integration/test_task_update.py
- [ ] T045 [P] [US3] Integration test for cancelled → any blocked (422 INVALID_STATUS_TRANSITION) in tests/integration/test_task_update.py
- [ ] T046 [P] [US3] Integration test for update non-existent task (404) in tests/integration/test_task_update.py
- [ ] T047 [P] [US3] Integration test for update another user's task (404) in tests/integration/test_task_update.py
- [ ] T048 [P] [US3] Integration test for update with empty title (422) in tests/integration/test_task_update.py
- [ ] T049 [P] [US3] Integration test for empty update payload (422 NO_FIELDS_TO_UPDATE) in tests/integration/test_task_update.py
- [ ] T050 [P] [US3] Integration test for updated_at timestamp refresh on update in tests/integration/test_task_update.py

### Implementation for User Story 3

- [ ] T051 [US3] Implement validate_status_transition function in src/services/task_service.py
- [ ] T052 [US3] Implement update_task function in src/services/task_service.py (PATCH semantics, status validation)
- [ ] T053 [US3] Implement PATCH /tasks/{task_id} endpoint in src/api/v1/tasks.py
- [ ] T054 [US3] Run task update tests to verify all scenarios pass

### ✅ Checkpoint 5: Task Update Functional

**Verification**:
```bash
# Run update tests:
uv run pytest tests/integration/test_task_update.py -v

# Manual API test:
# 1. Update status to in_progress
curl -X PATCH http://localhost:8000/api/v1/tasks/TASK_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
# Expected: HTTP 200

# 2. Update to completed
curl -X PATCH http://localhost:8000/api/v1/tasks/TASK_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
# Expected: HTTP 200

# 3. Try to reopen (should fail)
curl -X PATCH http://localhost:8000/api/v1/tasks/TASK_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "pending"}'
# Expected: HTTP 422 INVALID_STATUS_TRANSITION
```

**Exit Criteria**:
- [ ] All 10 task update tests pass (T041-T050)
- [ ] PATCH /api/v1/tasks/{id} returns 200 on valid update
- [ ] Status transitions from terminal states blocked (422)
- [ ] Empty payload rejected with NO_FIELDS_TO_UPDATE
- [ ] updated_at timestamp refreshes on any modification

**Deliverable**: Users can modify tasks (v0.3 partial)

---

## Phase 6: User Story 4 - Delete a Task (Priority: P2)

**Goal**: Allow users to permanently delete tasks (hard delete)

**Independent Test**: Delete task by ID → verify HTTP 204 and task no longer appears in list

### Tests for User Story 4 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T055 [P] [US4] Integration test for successful delete (204) in tests/integration/test_task_delete.py
- [ ] T056 [P] [US4] Integration test for delete non-existent task (404 TASK_NOT_FOUND) in tests/integration/test_task_delete.py
- [ ] T057 [P] [US4] Integration test for delete another user's task (404) in tests/integration/test_task_delete.py
- [ ] T058 [P] [US4] Integration test for deleted task not retrievable (404) in tests/integration/test_task_delete.py

### Implementation for User Story 4

- [ ] T059 [US4] Implement delete_task function in src/services/task_service.py (user scoped)
- [ ] T060 [US4] Implement DELETE /tasks/{task_id} endpoint in src/api/v1/tasks.py
- [ ] T061 [US4] Run task deletion tests to verify all scenarios pass

### ✅ Checkpoint 6: Task Deletion Functional (Core CRUD Complete)

**Verification**:
```bash
# Run delete tests:
uv run pytest tests/integration/test_task_delete.py -v

# Manual API test:
# 1. Create a task to delete
TASK_ID=$(curl -s -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Delete me"}' | jq -r '.id')

# 2. Delete it
curl -X DELETE http://localhost:8000/api/v1/tasks/$TASK_ID \
  -H "Authorization: Bearer $TOKEN"
# Expected: HTTP 204 No Content

# 3. Verify it's gone
curl -X GET http://localhost:8000/api/v1/tasks/$TASK_ID \
  -H "Authorization: Bearer $TOKEN"
# Expected: HTTP 404 TASK_NOT_FOUND
```

**Exit Criteria**:
- [ ] All 4 task deletion tests pass (T055-T058)
- [ ] DELETE /api/v1/tasks/{id} returns 204 on success
- [ ] Non-existent or other user's tasks return 404
- [ ] Deleted tasks cannot be retrieved

**Deliverable**: Full CRUD operations (v0.3 - Create, Read, Update, Delete)

---

## Phase 7: User Story 5 - Filter and Sort Tasks (Priority: P3)

**Goal**: Allow users to filter by status/priority/date range and sort by various fields

**Independent Test**: Create tasks with different statuses, filter by "pending" → verify only pending tasks returned

### Tests for User Story 5 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T062 [P] [US5] Integration test for filter by priority (200) in tests/integration/test_task_filter_sort.py
- [ ] T063 [P] [US5] Integration test for filter by status (200) in tests/integration/test_task_filter_sort.py
- [ ] T064 [P] [US5] Integration test for filter by due date range (200) in tests/integration/test_task_filter_sort.py
- [ ] T065 [P] [US5] Integration test for sort by priority descending (urgent first) in tests/integration/test_task_filter_sort.py
- [ ] T066 [P] [US5] Integration test for sort by created_at descending (newest first) in tests/integration/test_task_filter_sort.py
- [ ] T067 [P] [US5] Integration test for invalid sort field (422 INVALID_SORT_FIELD) in tests/integration/test_task_filter_sort.py
- [ ] T068 [P] [US5] Integration test for invalid date range (422 INVALID_DATE_RANGE) in tests/integration/test_task_filter_sort.py
- [ ] T069 [P] [US5] Integration test for combined filters (AND logic) in tests/integration/test_task_filter_sort.py
- [ ] T070 [P] [US5] Integration test for filter with pagination in tests/integration/test_task_filter_sort.py

### Implementation for User Story 5

- [ ] T071 [US5] Implement apply_filters function in src/services/task_service.py
- [ ] T072 [US5] Implement apply_sorting function in src/services/task_service.py
- [ ] T073 [US5] Update list_tasks to accept TaskListParams and apply filters/sorting
- [ ] T074 [US5] Update GET /tasks endpoint to accept filter/sort query params in src/api/v1/tasks.py
- [ ] T075 [US5] Run filter/sort tests to verify all scenarios pass

### ✅ Checkpoint 7: Filtering & Sorting Functional (Feature Complete)

**Verification**:
```bash
# Run filter/sort tests:
uv run pytest tests/integration/test_task_filter_sort.py -v

# Manual API test:
# 1. Filter by status
curl -X GET "http://localhost:8000/api/v1/tasks?status=pending" \
  -H "Authorization: Bearer $TOKEN"
# Expected: Only pending tasks

# 2. Filter by priority
curl -X GET "http://localhost:8000/api/v1/tasks?priority=high" \
  -H "Authorization: Bearer $TOKEN"
# Expected: Only high priority tasks

# 3. Sort by priority descending
curl -X GET "http://localhost:8000/api/v1/tasks?sort_by=priority&sort_order=desc" \
  -H "Authorization: Bearer $TOKEN"
# Expected: Tasks ordered urgent → high → medium → low

# 4. Combined filters
curl -X GET "http://localhost:8000/api/v1/tasks?status=pending&priority=high" \
  -H "Authorization: Bearer $TOKEN"
# Expected: Only pending AND high priority tasks

# 5. Invalid sort field
curl -X GET "http://localhost:8000/api/v1/tasks?sort_by=invalid_field" \
  -H "Authorization: Bearer $TOKEN"
# Expected: HTTP 422 INVALID_SORT_FIELD
```

**Exit Criteria**:
- [ ] All 9 filter/sort tests pass (T062-T070)
- [ ] Filter by status, priority, date range works
- [ ] Sort by created_at, updated_at, due_date, priority, status works
- [ ] Combined filters use AND logic
- [ ] Invalid sort field returns 422 INVALID_SORT_FIELD
- [ ] Invalid date range returns 422 INVALID_DATE_RANGE

**Deliverable**: Complete Task CRUD with filtering (v1.0 - All User Stories Complete)

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and improvements

- [ ] T076 [P] Add docstrings to all public functions in src/services/task_service.py
- [ ] T077 [P] Add docstrings to all endpoint functions in src/api/v1/tasks.py
- [ ] T078 Run mypy type checking on src/ (task-related files) and fix any errors
- [ ] T079 Run ruff linting on src/ and fix any issues
- [ ] T080 Integration test for user cascade delete (tasks deleted when user deleted) in tests/integration/test_task_cascade.py
- [ ] T081 Run full test suite with coverage: uv run pytest tests/integration/test_task_*.py --cov=src/services/task_service --cov-report=term-missing
- [ ] T082 Validate against quickstart.md examples (manual API testing)
- [ ] T083 Verify all acceptance criteria from spec.md are covered by tests

### ✅ Checkpoint 8: Production Ready

**Verification**:
```bash
# Type checking
uv run mypy src/models/task.py src/schemas/task.py src/services/task_service.py src/api/v1/tasks.py
# Expected: No errors

# Linting
uv run ruff check src/models/task.py src/schemas/task.py src/services/task_service.py src/api/v1/tasks.py
# Expected: No issues

# Full test suite with coverage
uv run pytest tests/integration/test_task_*.py --cov=src/services/task_service --cov-report=term-missing -v
# Expected: All tests pass, coverage >80%

# Test cascade delete
uv run pytest tests/integration/test_task_cascade.py -v
# Expected: Tasks deleted when user account deleted

# Verify quickstart.md examples work
# (Run through each example in quickstart.md manually)
```

**Exit Criteria**:
- [ ] mypy reports no type errors
- [ ] ruff reports no linting issues
- [ ] All 39 integration tests pass
- [ ] Code coverage is adequate (target >80%)
- [ ] Cascade delete works (tasks deleted with user)
- [ ] All quickstart.md examples work as documented
- [ ] All acceptance scenarios from spec.md are covered

**Deliverable**: Production-ready Task CRUD feature (v1.0 GA)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Depends on 001-user-auth being complete
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2)
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2)
- **User Story 3 (Phase 5)**: Depends on User Stories 1+2 (needs tasks to update)
- **User Story 4 (Phase 6)**: Depends on User Stories 1+2 (needs tasks to delete)
- **User Story 5 (Phase 7)**: Depends on User Stories 1+2 (needs tasks to filter/sort)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

```
    ┌─────────────────────────────────────┐
    │          001-user-auth              │
    │         (prerequisite)              │
    └─────────────────┬───────────────────┘
                      │
              ┌───────▼───────┐
              │    Setup      │
              │   (Phase 1)   │
              └───────┬───────┘
                      │
              ┌───────▼───────┐
              │ Foundational  │
              │   (Phase 2)   │
              └───────┬───────┘
                      │
          ┌───────────┴───────────┐
          │                       │
   ┌──────▼──────┐         ┌──────▼──────┐
   │    US1      │         │    US2      │
   │   Create    │         │    View     │
   │  (P1) MVP   │         │  (P1) MVP   │
   └──────┬──────┘         └──────┬──────┘
          │                       │
          └───────────┬───────────┘
                      │
          ┌───────────┼───────────┐
          │           │           │
   ┌──────▼────┐ ┌────▼────┐ ┌────▼─────┐
   │   US3     │ │   US4   │ │   US5    │
   │  Update   │ │  Delete │ │  Filter  │
   │   (P2)    │ │   (P2)  │ │   (P3)   │
   └───────────┘ └─────────┘ └──────────┘
```

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Service functions before endpoints
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
- T002, T003, T004 can run in parallel

**Phase 2 (Foundational)**:
- T008, T009, T010, T011 can run in parallel

**Phases 3+4 (US1 + US2)**:
- Can run in parallel after Foundational is complete
- All tests within each story can run in parallel

**Phases 5+6+7 (US3 + US4 + US5)**:
- Can run in parallel after US1+US2 are complete
- All tests within each story can run in parallel

---

## Parallel Examples

### Setup Phase Parallel Tasks

```bash
# Launch together:
Task: "Create TaskStatus enum"
Task: "Create TaskPriority IntEnum"
Task: "Create pagination schemas"
```

### User Story 1 + 2 Parallel

```bash
# After Foundational is complete, launch both stories:
Task: "US1 - Task Creation tests and implementation"
Task: "US2 - Task Retrieval tests and implementation"
```

### User Story 3 + 4 + 5 Parallel

```bash
# After US1+US2 complete, launch all three:
Task: "US3 - Task Update tests and implementation"
Task: "US4 - Task Delete tests and implementation"
Task: "US5 - Filter/Sort tests and implementation"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup → **Checkpoint 1**
2. Complete Phase 2: Foundational → **Checkpoint 2** (CRITICAL)
3. Complete Phase 3: User Story 1 → **Checkpoint 3**
4. Complete Phase 4: User Story 2 → **Checkpoint 4** 🎯
5. **STOP and VALIDATE**: Test create + read flow end-to-end
6. Deploy/demo if ready - **users can now create and view tasks**

### Incremental Delivery

1. Setup + Foundational → **Checkpoints 1 & 2**: Foundation ready
2. Add US1 (Create) → **Checkpoint 3**: **MVP v0.1**: Users can create tasks
3. Add US2 (View) → **Checkpoint 4**: **MVP v0.2**: Users can create + view tasks 🎯
4. Add US3 (Update) → **Checkpoint 5**: **v0.3 partial**: Task modification
5. Add US4 (Delete) → **Checkpoint 6**: **v0.3**: Full CRUD
6. Add US5 (Filter/Sort) → **Checkpoint 7**: **v1.0**: Complete feature
7. Polish → **Checkpoint 8**: **v1.0 GA**: Production ready

---

## Summary

| Phase | Task Count | Parallelizable | User Story | Checkpoint |
|-------|------------|----------------|------------|------------|
| Setup | 5 | 3 | - | ✅ 1 |
| Foundational | 10 | 4 | - | ✅ 2 |
| US1: Create Task | 13 | 9 | P1 MVP | ✅ 3 |
| US2: View Tasks | 12 | 7 | P1 MVP | ✅ 4 🎯 |
| US3: Update Task | 14 | 10 | P2 | ✅ 5 |
| US4: Delete Task | 7 | 4 | P2 | ✅ 6 |
| US5: Filter & Sort | 14 | 9 | P3 | ✅ 7 |
| Polish | 8 | 2 | - | ✅ 8 |
| **Total** | **83** | **48** | - | **8 checkpoints** |

**MVP Scope**: Phases 1-4 (US1 + US2) = 40 tasks → Users can create and view tasks

**Independent Test Criteria per Story**:
- US1: Create task with title → 201 with task data, status=pending
- US2: Get task by ID → 200 with all fields including is_overdue
- US3: Update task status → 200, terminal states blocked
- US4: Delete task → 204, subsequent retrieval returns 404
- US5: Filter by status → only matching tasks returned

**Test Count**: 39 integration tests total
- US1: 9 tests (T016-T024)
- US2: 7 tests (T029-T035)
- US3: 10 tests (T041-T050)
- US4: 4 tests (T055-T058)
- US5: 9 tests (T062-T070)
