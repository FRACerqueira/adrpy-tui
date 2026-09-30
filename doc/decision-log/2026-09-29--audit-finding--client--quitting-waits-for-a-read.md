# Quitting the TUI waited for a read in flight

**Front:** Resilience (Sonnet 5.5); also Async event ordering in one session (Opus), independently | **Severity:** Medium | **Resolution:** Direct | **Round:** 2

The interpreter joined the read's thread at exit. Client.shutdown(), called by the app's exit, stops a read and leaves a write. Covered by tests/test_client.py::test_shutdown_stops_a_read_and_leaves_a_write and tests/test_async_screens.py::test_quitting_during_a_read_does_not_wait_for_it.
