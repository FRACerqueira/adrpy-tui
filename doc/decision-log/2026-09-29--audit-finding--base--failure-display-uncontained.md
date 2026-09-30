# A failure while showing a failure ended the app

**Front:** Resilience (Sonnet 5.5) | **Severity:** Low | **Resolution:** Direct | **Round:** 3

_deliver called show_internal_error unguarded; if it raised, the worker failed and the app ended. It falls back to a plain notification. Covered by tests/test_async_screens.py::test_a_failure_while_showing_a_failure_is_not_fatal.
