# Change repository crashed on ~name and silently used the current folder when empty

**Front:** Resilience (Sonnet 5.5) | **Severity:** Medium | **Resolution:** Direct | **Round:** 1

`Path('~name').expanduser()` raised RuntimeError in the handler; an empty value became `.`. Fixed: both shown as not a folder. Reproduced; covered by tests/test_ui.py::test_change_repository_refuses_an_empty_path_and_an_unknown_home.
