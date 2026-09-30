# --version with no summary had no test

**Front:** Test adequacy (Sonnet 5.5) | **Severity:** Low | **Resolution:** Direct | **Round:** 4

Printing a None summary passed the suite; tests/test_versions.py::test_version_without_a_summary_prints_no_none kills it.
