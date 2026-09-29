# Check decided its warning when adrpy answered, not when it began to read

**Front:** Async event ordering in one session (Opus) | **Severity:** Medium | **Resolution:** Direct | **Round:** 4

A left write that ended while check read left a possibly half-written snapshot on screen with no warning (ADR006V02R02's visibility plan). Check asks as its read begins. Covered by tests/test_async_screens.py::test_check_warns_when_a_left_write_was_still_running_as_it_began.
