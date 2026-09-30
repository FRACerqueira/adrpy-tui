# A call that never started, or a read stopped on quit, was reported still running

**Front:** Resilience (Sonnet 5.5) | **Severity:** Low | **Resolution:** Direct | **Round:** 3

Every _Left became ABANDONED. _Left now says whether adrpy started: NOT_STARTED when it did not, STOPPED for a read stopped because the TUI quits, ABANDONED only for a write left running. Also found by the async front. Covered by tests/test_client.py.
