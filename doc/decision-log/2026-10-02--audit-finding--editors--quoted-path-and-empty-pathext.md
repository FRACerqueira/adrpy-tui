# A quoted PATH entry or a PATHEXT with nothing runnable hid an installed editor

**Front:** Resilience and untrusted input (Sonnet) | **Severity:** Low | **Resolution:** Direct | **Round:** 8

A PATH entry quoted as cmd.exe accepts it was skipped, and an empty PATHEXT (or one listing only scripts) gave no candidate at all: an installed editor showed as not found. The entry is unquoted and the default PATHEXT used then (de33e9a). Red then green: test_a_quoted_path_entry_is_searched_as_a_shell_does, test_a_pathext_with_nothing_windows_starts_falls_back_to_the_default.
