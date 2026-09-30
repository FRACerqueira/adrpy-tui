# No test showed the new result codes on a screen

**Front:** Test adequacy (Fable) | **Severity:** Low | **Resolution:** Direct | **Round:** 3

WRITE_STILL_RUNNING and ABANDONED were checked only on the Client. A test now drives a refused write to its result screen, its Check button and Check's warning: tests/test_async_screens.py::test_a_refused_write_offers_check_and_check_says_a_left_write_still_runs.
