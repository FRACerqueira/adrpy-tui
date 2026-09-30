# The check that a write already left is never started had no test

**Front:** Test adequacy (Fable) | **Severity:** Medium | **Resolution:** Direct | **Round:** 3

Removing the leave check before Popen passed the suite. tests/test_client.py::test_a_write_already_left_is_never_started now fails without it.
