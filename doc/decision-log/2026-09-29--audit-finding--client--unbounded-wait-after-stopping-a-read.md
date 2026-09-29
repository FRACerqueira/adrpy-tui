# After stopping a timed-out read, the wait for its output had no bound

**Front:** Resilience (Sonnet 5.5) | **Severity:** Medium | **Resolution:** Direct | **Round:** 2

A process adrpy started, still holding the pipe, kept the call and the lock as long as it lived. The wait after the kill is bounded (2 s). Covered by tests/test_client.py::test_a_stopped_read_does_not_wait_for_what_adrpy_left_holding_its_output.
