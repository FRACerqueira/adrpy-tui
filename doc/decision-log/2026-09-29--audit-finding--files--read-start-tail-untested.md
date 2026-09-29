# read_start's last partial character had no test

**Front:** Test adequacy (Sonnet 5.5) | **Severity:** Low | **Resolution:** Direct | **Round:** 4

Dropping the decoder's final flush passed the suite; the truncated-utf8 case of tests/test_files.py::test_read_start_counts_lines_as_they_are_cut kills it.
