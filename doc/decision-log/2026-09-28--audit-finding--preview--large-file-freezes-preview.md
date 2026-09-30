# A file of thousands of lines froze the preview for tens of seconds

**Front:** Resilience (Sonnet 5.5) | **Severity:** Low | **Resolution:** Escalated | **Round:** 1

About 5.5 ms a line headless. The user chose a limit by measurement, then 500 lines (PREVIEW_LINES), with a line saying the file was cut; 500 lines open in 2 to 3 s. Covered by tests/test_ui.py::test_a_large_file_is_previewed_as_its_first_lines.
