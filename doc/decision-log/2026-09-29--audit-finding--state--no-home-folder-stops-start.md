# A machine with no home folder kept the TUI from starting

**Front:** Resilience (Sonnet 5.5) | **Severity:** Low | **Resolution:** Direct | **Round:** 2

Path.home() raised in default_state_path; the temporary folder is used instead. Covered by tests/test_state.py::test_the_state_path_does_not_need_a_home_folder.
