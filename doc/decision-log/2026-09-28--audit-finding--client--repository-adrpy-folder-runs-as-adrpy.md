# A repository's own adrpy folder ran instead of adrpy when the TUI started inside it

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** High | **Resolution:** Direct | **Round:** 1

`python -m adrpy` puts the current folder first on the module path, so a repository holding an `adrpy/` folder ran its own code on the start-up config read, with no key pressed, and its JSON was trusted as adrpy's. Fixed: both prefixes run `python -P -m`. Reproduced (a file written by the fake adrpy) and covered by tests/test_client.py::test_a_folder_named_adrpy_in_the_current_folder_is_never_run. Class: `subprocess|Popen|os.system` in src/ matches core/client.py only.
