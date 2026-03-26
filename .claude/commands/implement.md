---
description: Implement a specific phase from the development plan
argument-hint: "Phase N (e.g., Phase 1)"
---

Read docs/PLAN.md and docs/SPEC.md fully before starting.
Implement the requested phase following this process:

1. Find the phase in docs/PLAN.md — read its deliverables and acceptance criteria
2. Read docs/PROTOCOL.md if touching anything in src/core/
3. Write ALL tests first (TDD) — create test files before implementation
4. Implement source files to make tests pass
5. Run `pytest tests/ -v` after each module
6. Commit with message "Phase N: <module name>" after each module passes
7. After all deliverables complete, verify EVERY acceptance criterion
8. Run full test suite one final time

Rules:
- Do NOT implement beyond the current phase
- If a previous phase's code exists, READ it first to understand interfaces
- Follow all conventions from CLAUDE.md
- If acceptance criteria mention visual checks, note them for the human
