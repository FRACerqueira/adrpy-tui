# An empty or relative PYTHONPATH entry let a repository's adrpy folder run despite -P

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Low | **Resolution:** Escalated | **Round:** 2

The user chose to drop such entries from adrpy's environment (not -E, which would break an adrpy found through PYTHONPATH). Covered by tests/test_client.py::test_an_empty_or_relative_pythonpath_entry_does_not_let_the_current_folder_in.
