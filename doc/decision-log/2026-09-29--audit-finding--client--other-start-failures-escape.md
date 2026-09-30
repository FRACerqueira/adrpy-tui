# A ValueError or TypeError starting adrpy escaped Client.run

**Front:** Resilience (Sonnet 5.5) | **Severity:** Low | **Resolution:** Direct | **Round:** 2

Such a failure (an embedded NUL, a non-string flag) is now tui-run-failed like an OSError. Covered by tests/test_client.py::test_other_failures_to_start_adrpy_are_failures_too.
