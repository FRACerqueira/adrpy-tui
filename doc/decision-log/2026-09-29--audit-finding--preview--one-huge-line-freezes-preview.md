# A file of one huge line passed the preview's line limit and froze it

**Front:** Resilience (Sonnet 5.5) | **Severity:** Low | **Resolution:** Direct | **Round:** 2

About 2 s a megabyte. The preview is also bounded to PREVIEW_CHARACTERS (100 000). Covered by tests/test_ui.py::test_a_file_of_one_huge_line_is_previewed_as_its_first_characters.
