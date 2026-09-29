# The notification shown when a failure note fails was never asserted

**Front:** Test adequacy (Sonnet 5.5) | **Severity:** Low | **Resolution:** Direct | **Round:** 4

Removing it passed the suite. The test also went vacuous with decisions.listed, which leaves out the decision it used to provoke the failure: it now fails a read and asserts the notification. tests/test_async_screens.py::test_a_failure_while_showing_a_failure_is_not_fatal.
