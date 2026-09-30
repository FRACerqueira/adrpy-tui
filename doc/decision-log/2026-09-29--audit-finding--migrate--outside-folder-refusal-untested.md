# Migrate's refusal of a folder outside the repository had no test

**Front:** Test adequacy (Fable) | **Severity:** Medium | **Resolution:** Direct | **Round:** 3

Replacing the check by False passed the whole suite. A test now covers it, and that mutation is killed. Covered by tests/test_ui.py::test_migrate_refuses_a_configured_folder_outside_the_repository.
