# A second restart right after the first crashed the TUI with NoActiveAppError

**Front:** Async event ordering in one session (Opus) | **Severity:** High | **Resolution:** Direct | **Round:** 1

Two Enter on Change repository (or two Esc on a reloading result) queued two restarts; the first start-up screen's thread reached the app through the detached screen. Fixed: the thread captures the app, a read is applied only to an open screen, and a restart is ignored while one is under way. Reproduced; covered by tests/test_async_screens.py::test_two_restarts_in_a_row_leave_one_main_menu.
