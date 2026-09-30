# A decision's detail kept stale data and actions when reading it again failed

**Front:** Resilience (Sonnet 5.5) | **Severity:** Medium | **Resolution:** Direct | **Round:** 1

The detail handled only a successful re-read. Fixed: a failure is shown and no action is offered. Reproduced; covered by tests/test_async_screens.py::test_a_detail_that_cannot_be_read_again_says_so.
