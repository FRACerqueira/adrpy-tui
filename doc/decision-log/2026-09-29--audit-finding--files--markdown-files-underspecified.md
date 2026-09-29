# markdown_files' top-only listing, case and order had no test

**Front:** Test adequacy (Sonnet 5.5) | **Severity:** Medium | **Resolution:** Direct | **Round:** 4

recursive=False recursing, a case-sensitive .md and an unsorted result passed the suite. tests/test_files.py::test_markdown_files_lists_in_order_any_case_and_only_the_top_when_asked kills all three (the order needed a top-level file after a subfolder's: NTFS already returns names sorted).
