# A migrate preview for an old pattern was shown under the new one

**Front:** Async event ordering in one session (Opus) | **Severity:** Medium | **Resolution:** Direct | **Round:** 1

Changing a part while the preview read ran showed the old pattern's preview next to the new pattern. Fixed: the preview is dropped unless its pattern is the current one. Reproduced; covered by tests/test_async_screens.py::test_a_migrate_preview_for_an_old_pattern_is_dropped.
