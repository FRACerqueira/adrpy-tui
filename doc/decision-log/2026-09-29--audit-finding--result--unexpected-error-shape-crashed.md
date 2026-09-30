# An error of an unexpected shape in adrpy's answer ended the app, after a write too

**Front:** Resilience (Sonnet 5.5) | **Severity:** Medium | **Resolution:** Direct | **Round:** 3

A code of 12, a file of 5 or related_files of 5 raised inside ErrorList's compose, which no screen contains: on a write's result screen the app ended after the write ran. ErrorList normalises every field to text. Swept every use of adrpy's data in ui/: the rest runs inside read, whose failures are shown. Covered by tests/test_ui.py::test_an_error_of_an_unexpected_shape_is_shown_not_fatal.
