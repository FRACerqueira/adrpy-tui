# Two reads in flight for one screen showed its content twice

**Front:** Async event ordering in one session (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 1

Both handlers removed then mounted. Fixed: only the latest read is applied. Covered by tests/test_async_screens.py::test_two_reads_in_flight_show_the_screen_once.
