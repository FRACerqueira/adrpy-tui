# A symlink or junction inside the repository led a preview outside it

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Medium | **Resolution:** Escalated | **Round:** 2

The link check was lexical. The user chose: every preview, whoever names the file, checks the path lexically, then each folder below the root with lstat, never resolving it (ADR0006V02). Reproduced with an NTFS junction; covered by tests/test_ui.py::test_a_link_through_a_folder_link_leading_outside_is_not_followed and ::test_a_preview_opens_only_a_file_inside_the_repository_whoever_names_it.
