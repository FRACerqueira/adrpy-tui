# Every reparse point was taken for a folder link

**Front:** Resilience (Sonnet 5.5) | **Severity:** Low | **Resolution:** Escalated | **Round:** 4

A repository under OneDrive, whose files are cloud placeholders, read as outside the repository. Owner's choice: only a symlink, a junction (mount point) and a WSL symlink are links; any other tag is the file itself (reading a placeholder downloads it). Covered by tests/test_files.py::test_only_a_reparse_point_that_leads_elsewhere_is_a_link.
