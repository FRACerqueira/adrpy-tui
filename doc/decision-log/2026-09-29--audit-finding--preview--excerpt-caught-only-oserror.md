# The excerpt caught OSError only, not a path no system call takes

**Front:** Resilience (Sonnet 5.5) | **Severity:** Low | **Resolution:** Direct | **Round:** 4

A path with a NUL raises ValueError; inside_repository refuses it first today, so it was not reachable. excerpt catches both, as core/files does. Covered by tests/test_ui.py.
