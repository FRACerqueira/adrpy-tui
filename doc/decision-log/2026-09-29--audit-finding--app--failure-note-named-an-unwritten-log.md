# A failure note said its details were in error.log when they could not be written

**Front:** Resilience (Sonnet 5.5) | **Severity:** Low | **Resolution:** Direct | **Round:** 3

internal_error_text named the log whether or not the write succeeded. A new text, app.internal_error_unlogged, says they could not be written. Covered by tests/test_async_screens.py.
