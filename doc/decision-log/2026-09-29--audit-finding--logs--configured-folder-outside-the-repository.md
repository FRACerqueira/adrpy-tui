# The log browser listed and opened files outside the repository when its configured folder led there

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Medium | **Resolution:** Direct | **Round:** 2

`adrpy config --folderlog ../x` is refused (path-outside-repository), but a hand-edited or cloned adr-config.adrplus is read back as it is (checked by the main model). The log browser and migrate now refuse a configured folder outside the repository. Covered by tests/test_ui.py::test_the_log_browser_does_not_list_a_folder_outside_the_repository.
