# A left write printing more than a pipe holds never ended on Linux and macOS

**Front:** Async event ordering in one session (Opus) | **Severity:** Medium | **Resolution:** Direct | **Round:** 3

Closes 2026-09-29--deferred--client--left-write-large-output-on-posix.md. Reproduced on Linux (WSL): the left write blocked on its full pipe and every later write was refused (tui-write-still-running). A daemon thread now drains and drops a left write's output. Red was reproduced on WSL, then green; not reproducible on Windows, whose communicate threads drain anyway. Covered by tests/test_client.py::test_a_left_write_printing_more_than_a_pipe_holds_still_ends (POSIX legs).
