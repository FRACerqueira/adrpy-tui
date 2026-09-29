# Leaving a write released the lock, and a second write could run beside the first

**Front:** Async event ordering in one session (Opus); also Resilience (Sonnet 5.5), independently | **Severity:** Medium | **Resolution:** Escalated | **Round:** 2

Two adrpy writes on one working copy are a usage error for adrpy-ai. The user chose: refuse another write while a left one runs (tui-write-still-running), reads still run (ADR0006V02). Covered by tests/test_client.py::test_a_write_is_refused_while_one_left_running_still_runs and ::test_a_read_runs_while_a_write_left_running_still_runs.
