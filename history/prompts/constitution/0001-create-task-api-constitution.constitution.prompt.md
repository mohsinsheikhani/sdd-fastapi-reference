---
id: 0001
title: Create Task API Constitution
stage: constitution
date: 2026-01-15
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: main
user: mohsin
command: /sp.constitution
labels: ["constitution", "governance", "principles", "standards"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - N/A
---

## Prompt

```text


# Project Constitution: Task API

## 1. Purpose and Scope

This project implements a user-specific Task API using FastAPI, PostgreSQL, SQLModel, and Pydantic.

The system provides basic CRUD operations for tasks, scoped to an authenticated user.

The codebase is designed to be:
- maintainable and explicitly typed
- suitable for extension with AI-driven agents
- safe for programmatic consumption by both humans and machines

All specifications, plans, and implementations must conform to the standards defined in this constitution.

---

## 2. Core Engineering Principles

- Correctness takes priority over convenience
- Explicit behavior is preferred over implicit behavior
- Strong typing is mandatory
- Separation of concerns must be preserved
- No undocumented or ambiguous behavior is allowed

---

## 3. Architecture and Boundaries

- FastAPI is used strictly as the HTTP interface layer
- Route handlers must not contain business logic
- Business logic must be implemented in service-level functions
- Database access must be isolated behind repositories or services
- Dependency injection must be used for database sessions and user context
- Global mutable state is not permitted

---

## 4. Global Development Constraints

- All automated code generation must use the FastAPI Builder Claude Skill
- Generated code must follow the latest syntax and patterns defined by the skill
- Manual code changes must not violate structures or assumptions introduced by the skill
- Mixing alternative architectural styles is not allowed

---

## 5. API Design Standards

- RESTful CRUD semantics must be followed
- All endpoints must be versioned under `/api/v1`
- Each endpoint must define:
  - a request schema
  - a response schema
  - explicit HTTP status codes
- Task operations must always be scoped to the authenticated user
- Endpoints must not return raw ORM models

---

## 6. Data and Persistence Standards

- PostgreSQL is the only supported database
- SQLModel is the only ORM layer
- All database models must:
  - define explicit table names
  - use UUID primary keys
  - include `created_at` and `updated_at` fields
- All database queries must be scoped to the authenticated user
- Raw SQL is not allowed unless explicitly justified in a specification

---

## 7. Typing, Validation, and Schemas

- Python type hints are mandatory for all functions, methods, and variables
- Pydantic v2 syntax must be used consistently
- Separate schema models must exist for:
  - create operations
  - update operations
  - read operations
- Validation logic must reside in schema models or services, not in route handlers
- Optional fields must be explicitly declared as optional

---

## 8. Error Handling and Responses

- Unhandled exceptions must not be exposed to API consumers
- All errors must return structured JSON responses
- HTTPException usage must include:
  - an appropriate HTTP status code
  - a machine-readable error identifier
  - a human-readable error message
- Database errors must be translated into domain-level errors

---

## 9. Testing and Quality Gates

- Unit tests are required for service and repository layers
- Integration tests must cover core CRUD flows
- Tests must use an isolated test database
- No code may be merged if tests are failing

---

## 10. Tooling and Enforcement

- The Python version must be explicitly defined
- Formatting and linting tools must be configured and enforced
- Continuous integration must run:
  - linting checks
  - test suites
- Code must be reviewed for compliance with this constitution

---

## 11. Amendment Rules

- Changes to this constitution require documented rationale
- Each amendment must include a version increment
- Amendments must not silently invalidate existing specifications
- Downstream specifications must be reviewed after any amendment
```

## Response snapshot

Created Task API Constitution v1.0.0 with 11 comprehensive sections covering:

1. **Purpose and Scope**: Defined project goals and design objectives
2. **Core Engineering Principles**: Established 5 foundational principles (Correctness, Explicitness, Strong Typing, Separation of Concerns, Zero Ambiguity)
3. **Architecture and Boundaries**: Set layered architecture requirements and constraints
4. **Global Development Constraints**: Mandated FastAPI Builder Claude Skill and SDD workflow
5. **API Design Standards**: Specified RESTful requirements and response standards
6. **Data and Persistence Standards**: Established PostgreSQL/SQLModel requirements and model conventions
7. **Typing, Validation, and Schemas**: Defined type hint and Pydantic standards
8. **Error Handling and Responses**: Set structured error response requirements
9. **Testing and Quality Gates**: Specified testing requirements and quality gates
10. **Tooling and Enforcement**: Defined tooling and CI/CD requirements
11. **Amendment Rules**: Established governance for constitution changes

All placeholders from template filled with concrete, testable requirements. Constitution uses declarative MUST/MUST NOT language throughout. No unresolved placeholder tokens remain.

Templates reviewed:
- plan-template.md: Constitution Check section is generic, no changes needed
- spec-template.md: Requirements section is generic, no changes needed
- tasks-template.md: Task structure aligns with testing principles, no changes needed

Constitution file written to `.specify/memory/constitution.md` with Sync Impact Report prepended as HTML comment.

## Outcome

- ✅ Impact: Comprehensive constitution established defining all engineering standards for Task API project. Provides foundation for all future development work.
- 🧪 Tests: N/A (documentation artifact)
- 📁 Files: Created `.specify/memory/constitution.md` (v1.0.0)
- 🔁 Next prompts: `/sp.specify` to create first feature specification, or begin codebase development following constitution standards
- 🧠 Reflection: Constitution successfully transforms user input into structured governance document with 5 core principles expanded into 11 detailed sections. All requirements made testable and explicit using MUST/MUST NOT language. Templates validated for consistency.

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS - All placeholders filled, no bracket tokens remaining, version properly set, dates in ISO format, principles declarative and testable
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
