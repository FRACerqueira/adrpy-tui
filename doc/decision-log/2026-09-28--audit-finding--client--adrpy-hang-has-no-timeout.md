# An adrpy that did not answer left the TUI waiting forever, with no way out

**Front:** Resilience (Sonnet 5.5) | **Severity:** High | **Resolution:** Escalated | **Round:** 1

No timeout: a hung read kept the start-up screen loading, blocked every later call behind the one-call lock and kept the process alive after quitting. The user chose a timeout on reads only, and a write never stopped but leavable, with its result said to be unknown and Check offered (ADR0006V01). Covered by tests/test_client.py and tests/test_async_screens.py.
