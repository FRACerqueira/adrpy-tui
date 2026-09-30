# A failure whose own text could not be built ended the TUI through the failure display

**Front:** Resilience (Sonnet 5.5) | **Severity:** Low | **Resolution:** Direct | **Round:** 2

An exception whose str() raises, or a message the log could not encode, raised inside the mechanism meant to show failures. Both handled; covered by tests/test_async_screens.py::test_a_failure_that_cannot_be_put_into_words_is_still_shown.
