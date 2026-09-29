# An empty configuration setting had no test

**Front:** Test adequacy (Sonnet 5.5) | **Severity:** Low | **Resolution:** Direct | **Round:** 4

setting accepting an empty string passed the suite; tests/test_ui.py::test_an_empty_setting_is_its_default kills it.
