# A confirmation with no command drew an empty command box

**Front:** Usability and docs against code (Sonnet) | **Severity:** Low | **Resolution:** Direct | **Round:** 9

Leave without saving your changes? passed an empty command line, drawn as an empty box above the buttons; it is not drawn then (1532a2e). Red then green: test_a_question_with_no_command_draws_no_empty_command_box.
