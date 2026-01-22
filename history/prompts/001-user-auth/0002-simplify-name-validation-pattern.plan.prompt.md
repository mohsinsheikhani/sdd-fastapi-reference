---
id: "0002"
title: "simplify name validation pattern"
stage: plan
date: 2026-01-22
surface: agent
model: claude-opus-4-5-20251101
feature: 001-user-auth
branch: 001-user-auth
user: mohsin
command: /sp.plan
labels: ["validation", "data-model", "simplification"]
links:
  spec: specs/001-user-auth/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-user-auth/data-model.md
  - specs/001-user-auth/contracts/auth-api.yaml
tests:
  - null
---

## Prompt

@data-model.md The name doesn't require hyphens or apostrophes.

## Response snapshot

Updated data-model.md and auth-api.yaml to simplify the name validation pattern:

**Before**: `^[a-zA-Z\s\-']+$` (letters, spaces, hyphens, apostrophes)
**After**: `^[a-zA-Z\s]+$` (letters and spaces only)

Changes made in:
1. Entity definition table (constraints column)
2. Validation rules section
3. Pydantic schema validator with error message
4. Constraints summary table
5. OpenAPI schema pattern and description

## Outcome

- Impact: Simplified name validation to letters and spaces only
- Tests: No tests affected (validation simplification)
- Files: data-model.md, contracts/auth-api.yaml updated
- Next prompts: /sp.tasks to generate implementation tasks
- Reflection: User feedback incorporated to simplify validation rules

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A (documentation update)
- Prompt variant (if applicable): User feedback on spec artifacts
- Next experiment: N/A
