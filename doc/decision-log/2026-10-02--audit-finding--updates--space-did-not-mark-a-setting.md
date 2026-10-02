# Space did not mark a setting on the Updates screen

**Front:** Usability and docs against code (Fable) | **Severity:** Low | **Resolution:** Escalated | **Round:** 10

The Updates rows borrowed the [x]/[ ] mark of the multi-selects, where Space or Enter marks, but only Enter acted and the key line said "select". The owner chose Space and Enter both, the key line saying "Space/Enter mark" on a setting and "Enter select" on Back (74102ac). Red then green: tests/test_update_notice.py::test_space_marks_a_setting_as_enter_does_and_the_key_line_says_so; the screen is in the every-screen key-line guard.
