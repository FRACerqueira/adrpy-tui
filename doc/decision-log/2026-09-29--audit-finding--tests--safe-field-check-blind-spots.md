# The safe-field check missed a second base, widgets.Input and an alias

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 4

test_every_screen_field_is_a_safe_one read only a class's first base and only a plain name. It now uses _bare_fields, which sees every base, attribute access and import aliases; the old logic found nothing in three of the four samples of tests/test_ui.py::test_the_safe_field_check_sees_every_way_to_a_bare_field.
