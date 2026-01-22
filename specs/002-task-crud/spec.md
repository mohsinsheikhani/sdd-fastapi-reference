# Feature Specification: Task CRUD Operations

**Feature Branch**: `002-task-crud`
**Created**: 2026-01-21
**Status**: Draft
**Last Updated**: 2026-01-21
**Input**: User-specific task management system with CRUD operations, filtering, sorting, and pagination

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a New Task (Priority: P1)

An authenticated user wants to create a new task to track something they need to do. They provide task details including a title, optional description, priority, and due date. The system creates the task and confirms it was saved.

**Why this priority**: Task creation is the foundational capability. Without it, no other task operations are possible. This is the entry point for all task management functionality.

**Independent Test**: Can be fully tested by submitting a valid task creation request and verifying the task is returned with a unique ID. Delivers the ability to capture and persist task data.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they submit a task with title "Buy groceries", priority "medium", and due date tomorrow, **Then** the task is created with status "pending" and they receive HTTP 201 with the task ID, title, status, priority, due date, and timestamps
2. **Given** an authenticated user, **When** they submit a task with only a title (minimum required field), **Then** the task is created with default priority "medium" and status "pending"
3. **Given** an authenticated user, **When** they submit a task with an empty or whitespace-only title, **Then** they receive HTTP 422 with a validation error
4. **Given** an authenticated user, **When** they submit a task with title exceeding 70 characters, **Then** they receive HTTP 422 with a validation error
5. **Given** an authenticated user, **When** they submit a task with description exceeding 500 characters, **Then** they receive HTTP 422 with a validation error
6. **Given** an authenticated user, **When** they submit a task with an invalid priority value, **Then** they receive HTTP 422 with a validation error
7. **Given** an authenticated user, **When** they submit a task with a past due date, **Then** the task is created (past due dates are allowed for backdating or importing existing tasks)
8. **Given** an authenticated user, **When** they submit a task with a duplicate title, **Then** the task is created (duplicate titles are allowed)

---

### User Story 2 - View Tasks (Priority: P1)

An authenticated user wants to view their tasks to understand what they need to do. They can view a single task by ID or list all their tasks with filtering, sorting, and pagination options.

**Why this priority**: Viewing tasks is essential for users to track their work. Without retrieval, created tasks have no visibility. Equal priority with creation as both are required for basic usability.

**Independent Test**: Can be fully tested by retrieving a known task by ID and verifying all fields are returned. List endpoint can be tested by creating multiple tasks and verifying pagination works correctly.

**Acceptance Scenarios**:

1. **Given** an authenticated user with existing tasks, **When** they request a task by its ID, **Then** they receive the task with all fields including an "is_overdue" indicator (true if due_date has passed)
2. **Given** an authenticated user, **When** they request a task that doesn't exist, **Then** they receive HTTP 404 with error code "TASK_NOT_FOUND"
3. **Given** an authenticated user, **When** they request another user's task, **Then** they receive HTTP 404 (not 403, to prevent enumeration)
4. **Given** an authenticated user with 150 tasks, **When** they request the task list without pagination parameters, **Then** they receive the first 50 tasks (default page size) with pagination metadata
5. **Given** an authenticated user, **When** they request tasks filtered by status "completed", **Then** they receive only tasks with that status
6. **Given** an authenticated user, **When** they request tasks sorted by due_date ascending, **Then** tasks are returned in chronological order by due date
7. **Given** an authenticated user, **When** they request tasks with multiple filters (status + priority), **Then** all filter conditions are applied (AND logic)

---

### User Story 3 - Update a Task (Priority: P2)

An authenticated user wants to modify an existing task to update its details as circumstances change. They can update the description, priority, due date, or mark it complete.

**Why this priority**: Updates are essential for task management but require existing tasks. Slightly lower than create/view since basic tracking works without updates.

**Independent Test**: Can be fully tested by updating a task's status to "completed" and verifying the change persists. Delivers the ability to track progress and modify task details.

**Acceptance Scenarios**:

1. **Given** an authenticated user with a pending task, **When** they update the description to "Updated description", **Then** the task is updated and they receive HTTP 200 with the modified task
2. **Given** an authenticated user with a pending task, **When** they update the status to "in_progress", **Then** the status changes and updated_at timestamp is refreshed
3. **Given** an authenticated user with a pending task, **When** they update the status to "completed", **Then** the task is marked complete
4. **Given** an authenticated user with a completed task, **When** they attempt to change the status back to "pending", **Then** they receive HTTP 422 with error code "INVALID_STATUS_TRANSITION" (completed tasks cannot be reopened)
5. **Given** an authenticated user with a cancelled task, **When** they attempt to change the status to any other value, **Then** they receive HTTP 422 with error code "INVALID_STATUS_TRANSITION" (cancelled tasks cannot be reopened)
6. **Given** an authenticated user, **When** they attempt to update a task they don't own, **Then** they receive HTTP 404
7. **Given** an authenticated user, **When** they attempt to update a task with an empty title, **Then** they receive HTTP 422 with a validation error
8. **Given** an authenticated user, **When** they send an empty update payload (no fields to update), **Then** they receive HTTP 422 with error code "NO_FIELDS_TO_UPDATE"

---

### User Story 4 - Delete a Task (Priority: P2)

An authenticated user wants to remove a task they no longer need. The deletion is permanent (hard delete).

**Why this priority**: Deletion allows users to clean up their task list. Important for long-term usability but not required for basic task tracking.

**Independent Test**: Can be fully tested by deleting a task and confirming it no longer appears in the task list. Delivers the ability to remove unwanted tasks.

**Acceptance Scenarios**:

1. **Given** an authenticated user with an existing task, **When** they request deletion by task ID, **Then** the task is permanently removed and they receive HTTP 204
2. **Given** an authenticated user, **When** they attempt to delete a task that doesn't exist, **Then** they receive HTTP 404 with error code "TASK_NOT_FOUND"
3. **Given** an authenticated user, **When** they attempt to delete another user's task, **Then** they receive HTTP 404 (not 403, to prevent enumeration)
4. **Given** an authenticated user who deleted a task, **When** they attempt to retrieve the deleted task, **Then** they receive HTTP 404

---

### User Story 5 - Filter and Sort Tasks (Priority: P3)

An authenticated user wants to find specific tasks quickly by applying filters and sorting options. They can filter by status, priority, or due date range, and sort by various fields.

**Why this priority**: Advanced filtering enhances usability but the system is functional with basic list retrieval. Can be added after core CRUD works.

**Independent Test**: Can be fully tested by creating tasks with different statuses/priorities, applying filters, and verifying correct results are returned. Delivers efficient task discovery.

**Acceptance Scenarios**:

1. **Given** an authenticated user with tasks of various priorities, **When** they filter by priority "high", **Then** only high-priority tasks are returned
2. **Given** an authenticated user with tasks of various statuses, **When** they filter by status "pending", **Then** only pending tasks are returned
3. **Given** an authenticated user, **When** they filter by due_date_from and due_date_to, **Then** only tasks with due dates in that range are returned
4. **Given** an authenticated user, **When** they sort by priority descending, **Then** tasks are returned in order: urgent, high, medium, low
5. **Given** an authenticated user, **When** they sort by created_at descending, **Then** newest tasks appear first
6. **Given** an authenticated user, **When** they provide an invalid sort field, **Then** they receive HTTP 422 with a validation error

---

### Edge Cases

- What happens when a user has no tasks and requests the task list? Returns empty array with pagination metadata showing 0 total
- What happens when a user requests page 10 but only has 50 tasks? Returns empty array for that page with correct total count
- What happens when filtering produces no matches? Returns empty array with pagination metadata
- What happens when the due_date_from is after due_date_to? Returns HTTP 422 with validation error
- What happens when multiple users create tasks simultaneously? Each user's task is isolated; no conflicts occur
- What happens when two requests update the same task simultaneously? Last write wins (no optimistic locking)
- How is "is_overdue" calculated? Compares due_date against current UTC datetime; true if due_date < now AND status is not "completed" or "cancelled"
- What happens when a user is deleted? All their tasks are cascade deleted (per auth spec FR-022)

## Constraints

| Field       | Constraint                                                                 |
|-------------|----------------------------------------------------------------------------|
| Title       | Required, 1-70 characters, cannot be whitespace-only                       |
| Description | Optional, max 500 characters                                               |
| Status      | Enum: pending, in_progress, completed, cancelled (default: pending)        |
| Priority    | Enum: low, medium, high, urgent (default: medium)                          |
| Due date    | Optional, datetime (past dates allowed)                                    |
| Page size   | Default 50, maximum 100                                                    |
| Rate limit  | 10 requests per minute per user on task creation endpoint                  |

## Requirements *(mandatory)*

### Functional Requirements

**Task Creation**
- **FR-001**: System MUST allow authenticated users to create tasks with a title
- **FR-002**: System MUST validate title is 1-70 characters and not whitespace-only
- **FR-003**: System MUST validate description does not exceed 500 characters when provided
- **FR-004**: System MUST set default status to "pending" when not specified
- **FR-005**: System MUST set default priority to "medium" when not specified
- **FR-006**: System MUST accept past due dates (for backdating or importing)
- **FR-007**: System MUST allow duplicate task titles for the same user
- **FR-008**: System MUST associate each task with the authenticated user's ID

**Task Retrieval**
- **FR-009**: System MUST allow users to retrieve a single task by ID
- **FR-010**: System MUST return 404 for non-existent tasks or tasks owned by other users
- **FR-011**: System MUST include "is_overdue" boolean in task responses (true if due_date < now AND status not completed/cancelled)
- **FR-012**: System MUST support listing all tasks for the authenticated user
- **FR-013**: System MUST paginate list results with default page size of 50 and maximum of 100
- **FR-014**: System MUST return pagination metadata (total count, page number, page size, total pages)

**Task Filtering**
- **FR-015**: System MUST support filtering tasks by status (single value)
- **FR-016**: System MUST support filtering tasks by priority (single value)
- **FR-017**: System MUST support filtering tasks by due date range (due_date_from, due_date_to)
- **FR-018**: System MUST apply multiple filters with AND logic when provided together

**Task Sorting**
- **FR-019**: System MUST support sorting by: created_at, updated_at, due_date, priority, status
- **FR-020**: System MUST support ascending and descending sort order
- **FR-021**: System MUST default to sorting by created_at descending when not specified

**Task Updates**
- **FR-022**: System MUST allow updating task title, description, status, priority, and due_date
- **FR-023**: System MUST support partial updates (PATCH semantics)
- **FR-024**: System MUST update the updated_at timestamp on any modification
- **FR-025**: System MUST prevent status transitions from "completed" to any other status
- **FR-026**: System MUST prevent status transitions from "cancelled" to any other status
- **FR-027**: System MUST reject update requests with no fields to update

**Task Deletion**
- **FR-028**: System MUST allow users to permanently delete their own tasks
- **FR-029**: System MUST return 404 when attempting to delete non-existent or unauthorized tasks

**Security & Isolation**
- **FR-030**: System MUST scope all task operations to the authenticated user
- **FR-031**: System MUST never expose tasks belonging to other users
- **FR-032**: System MUST use 404 (not 403) for unauthorized access to prevent task ID enumeration
- **FR-033**: System MUST rate limit task creation to 10 requests per minute per user

### Error Codes

All error responses MUST include a machine-readable code and human-readable message.

| Code                        | HTTP Status | Condition                                              |
|-----------------------------|-------------|--------------------------------------------------------|
| `VALIDATION_ERROR`          | 422         | Invalid input format (title, description, dates)       |
| `TASK_NOT_FOUND`            | 404         | Task does not exist or belongs to another user         |
| `INVALID_STATUS_TRANSITION` | 422         | Attempted to reopen completed or cancelled task        |
| `NO_FIELDS_TO_UPDATE`       | 422         | Update request with empty payload                      |
| `INVALID_SORT_FIELD`        | 422         | Sort field not in allowed list                         |
| `INVALID_DATE_RANGE`        | 422         | due_date_from is after due_date_to                     |
| `RATE_LIMIT_EXCEEDED`       | 429         | Too many task creation requests from this user         |

### Key Entities

- **Task**: Represents a user's to-do item. Key attributes: unique ID (UUID), user_id (foreign key to User), title, description, status (enum), priority (enum), due_date, is_overdue (computed), created_at, updated_at

### API Response Shapes

**Task Create Success** (HTTP 201):
- Task ID (UUID)
- Title
- Description (or null)
- Status
- Priority
- Due date (or null)
- Is overdue (boolean, computed)
- Created timestamp
- Updated timestamp

**Task Get/Update Success** (HTTP 200):
- Same fields as create response

**Task List Success** (HTTP 200):
- Array of task objects (same structure as single task)
- Pagination object:
  - Total count
  - Page number
  - Page size
  - Total pages

**Task Delete Success** (HTTP 204):
- No content

**Error Response** (HTTP 4xx):
- Error code (from Error Codes table)
- Error message (human-readable)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a task with required fields in under 1 second (measured from request to response)
- **SC-002**: Users can retrieve a single task in under 200 milliseconds
- **SC-003**: Users can retrieve a paginated task list (50 items) in under 500 milliseconds
- **SC-004**: Users can update any task field and see changes reflected immediately on subsequent retrieval
- **SC-005**: Users can delete a task and confirm it no longer appears in their task list
- **SC-006**: Zero cross-user data leakage verified by integration tests attempting to access other users' tasks
- **SC-007**: Task creation rate limiting blocks the 11th request within 60 seconds from the same user
- **SC-008**: 80% or higher code coverage on task service and repository layers (verified by CI)
- **SC-009**: All task operations return structured error responses with machine-readable error codes
- **SC-010**: Pagination correctly limits results to maximum 100 items per page regardless of requested page size

## Assumptions

- User authentication is implemented per the 001-user-auth specification
- All task operations require a valid access token (JWT)
- User IDs are UUID v4 format (from auth system)
- All timestamps are stored and returned in UTC ISO 8601 format
- Database cascades ensure tasks are deleted when user account is deleted (per auth spec)
- "is_overdue" is computed at read time, not stored in database
- Concurrent updates follow last-write-wins semantics (no optimistic locking)
- Title uniqueness is not enforced; users can have multiple tasks with same title
- Empty string for description is treated as null (no description)

## Technical Decisions

### Status Transitions
- **Allowed transitions**: pending → in_progress → completed, pending → cancelled, in_progress → cancelled
- **Forbidden transitions**: completed → any, cancelled → any (terminal states)
- **No transition validation** between non-terminal states (pending ↔ in_progress freely allowed)

### Priority Sorting Order
- When sorting by priority descending: urgent (highest) → high → medium → low (lowest)
- When sorting by priority ascending: low (lowest) → medium → high → urgent (highest)

### Overdue Calculation
- `is_overdue = (due_date IS NOT NULL) AND (due_date < current_utc_datetime) AND (status NOT IN ['completed', 'cancelled'])`
- Calculated at response time, not stored

### Rate Limiting
- Scope: Per authenticated user (not per IP like auth endpoints)
- Applied only to POST /tasks (creation), not to GET/PATCH/DELETE
- Shared rate limiter middleware with auth endpoints (different configuration)

## Non-Goals

- Multi-user collaboration or task sharing between users
- Task assignment to other users
- Subtasks or task hierarchies
- Recurring or repeating tasks
- File attachments on tasks
- Comments or activity history on tasks
- Notifications or reminders for due dates
- Tags, labels, or categories for tasks
- Full-text search across task content
- Task templates or cloning
- Bulk operations (create/update/delete multiple tasks in one request)
- Soft delete or trash/restore functionality
- Task dependencies or blocking relationships
