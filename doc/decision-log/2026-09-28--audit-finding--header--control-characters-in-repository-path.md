# The repository path and some folder names were shown without stripping control characters

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 1

The header, the confirmation and the empty-folder messages now go through `visible()`. Covered by tests/test_untrusted_text.py::test_the_header_shows_a_hostile_repository_path_as_it_is.
