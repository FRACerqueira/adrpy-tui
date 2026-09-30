# Damaged adrpy-ai metadata stopped the TUI from starting

**Front:** Resilience (Sonnet 5.5) | **Severity:** Low | **Resolution:** Direct | **Round:** 2

METADATA that is not UTF-8 raised in the app's constructor and in --version; one with no Version showed None. Both read as not installed now; covered by tests/test_versions.py::test_damaged_metadata_reads_as_not_installed.
