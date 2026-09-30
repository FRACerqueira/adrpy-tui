# A crash closed the app without stopping adrpy

**Front:** Resilience (Sonnet 5.5) | **Severity:** Medium | **Resolution:** Direct | **Round:** 3

Shutdown lived in AdrpyTui.exit, which a crash does not call: a read in flight kept the process up to READ_TIMEOUT, a write for as long as it ran. on_unmount calls Client.shutdown on every teardown. Also found by the async front, independently. Covered by tests/test_async_screens.py::test_a_crash_never_waits_for_adrpy.
