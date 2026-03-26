---
description: Run tests and fix any failures
---

1. Run `pytest tests/ -v --tb=short`
2. If failures exist:
   - Read the failing test to understand expected behavior
   - Read the source code being tested
   - Fix the SOURCE (not the test) unless the test is clearly wrong
   - Re-run the specific failing test: `pytest tests/test_xxx.py::test_name -v`
   - Repeat until it passes
3. Run full suite again: `pytest tests/ -v`
4. Report: total / passed / failed / skipped
