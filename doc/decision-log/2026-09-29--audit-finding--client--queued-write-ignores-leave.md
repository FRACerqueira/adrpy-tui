# A write waiting behind a hung read ignored Leave and Quit, then started after the person left

**Front:** Resilience (Sonnet 5.5) | **Severity:** Medium | **Resolution:** Direct | **Round:** 2

The lock was taken with a plain `with`, and Popen came before `leave` was looked at. Waiting for the lock now ends when the person leaves (tui-not-started), and `leave` is checked before starting. Covered by tests/test_client.py::test_a_write_waiting_behind_a_hung_read_can_be_left_before_it_starts.
