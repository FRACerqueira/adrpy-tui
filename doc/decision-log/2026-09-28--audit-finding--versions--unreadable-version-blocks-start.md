# An installed adrpy-ai version that could not be parsed kept the TUI from starting

**Front:** Resilience (Sonnet 5.5) | **Severity:** Medium | **Resolution:** Direct | **Round:** 1

`_release` raised AttributeError on a version with no leading number or on damaged metadata, in the app's constructor. ADR0003V01 makes the check a warning: such a version is now named on the main menu. Covered by tests/test_versions.py::test_an_installed_version_that_cannot_be_read_is_named_not_a_crash.
