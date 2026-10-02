# Check after Stop waiting said to approve or edit while both are refused

**Front:** Usability and docs against code (Fable) | **Severity:** Medium | **Resolution:** Direct | **Round:** 8

After Stop waiting, Check showed 'Esc goes to its detail, to approve it or edit it again' beside its own still-running warning, while approve and Edit are refused until the editor closes. It now says the editor is still open and to approve or edit once it has closed; a check that could not run offers no repair line (e66085c). Red then green: tests/test_hints.py::test_check_after_stopping_the_wait_says_the_editor_is_still_open, test_check_after_an_edit_that_could_not_run_offers_no_repair.
