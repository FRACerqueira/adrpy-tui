# The decision picker matched a decision's path with ==

**Front:** Test adequacy by mutation (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 8

AdrPicker.choose compared paths with ==: a detail spelling the path otherwise than explore (case, separators, a '.' step) opened its form with nothing chosen. It uses same_path, as the detail and check do (17882c5; the test made portable to POSIX in ea32d77). Red then green: tests/test_ui.py::test_a_detail_opened_with_its_path_spelled_otherwise_chooses_it_in_the_form.
