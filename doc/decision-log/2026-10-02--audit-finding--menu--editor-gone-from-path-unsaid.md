# An editor chosen and gone from PATH vanished with no word

**Front:** Usability and docs against code (Fable) | **Severity:** Low | **Resolution:** Direct | **Round:** 8

When the chosen editor was no longer found, app.editor became None and Edit and the editor's field disappeared with nothing said, unlike a saved key or color that cannot be used. The main menu now names it (e66085c). Red then green: tests/test_hints.py::test_the_main_menu_says_when_the_editor_chosen_is_no_longer_on_path.
