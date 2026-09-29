# A preview of CR line ends showed 500 lines and did not say it was cut

**Front:** Resilience (Sonnet 5.5) | **Severity:** Low | **Resolution:** Direct | **Round:** 4

read_start counted lines by LF but cut them by splitlines. It counts line breaks as splitlines does, a CRLF split across two chunks once. Covered by tests/test_files.py::test_read_start_counts_lines_as_they_are_cut.
