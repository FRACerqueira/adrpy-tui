# The drain of a left write had no test that runs on Windows

**Front:** Test adequacy (Sonnet 5.5) | **Severity:** Medium | **Resolution:** Direct | **Round:** 4

Removing the drain thread, or the read in it, passed the suite: the only test is POSIX-only. tests/test_client.py::test_a_left_write_is_drained_on_every_system kills both mutations.
