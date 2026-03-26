---
description: Review recent code changes like a staff engineer
---

Review all files modified in this session. Check each against these criteria:

1. **Type safety**: Type hints on all function signatures?
2. **Documentation**: Docstrings on public classes and methods?
3. **Threading**: No serial I/O outside SerialManager? No blocking in GUI thread?
4. **Qt patterns**: Signal/Slot for all cross-component communication?
5. **Data models**: Dataclasses used, no raw dicts for structured data?
6. **Logging**: `logger = logging.getLogger(__name__)` in every module?
7. **Colors**: Channel A = #4fc3f7, Channel B = #ef5350 everywhere?
8. **Error handling**: No bare `except:`, user-friendly messages?
9. **Spec compliance**: Does behavior match docs/SPEC.md?
10. **Memory**: Ring buffers bounded? No growing lists without limit?

Output: numbered list of issues found. Fix anything critical.
For non-critical suggestions, just list them.
