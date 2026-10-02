# The main menu's notice of an editor gone from PATH stayed after another was chosen

**Front:** Usability and docs against code (Sonnet) | **Severity:** Medium | **Resolution:** Direct | **Round:** 9

The notice was built once when the main menu was composed: after choosing None, another editor or installing it, it still said the editor chosen is not on PATH until a restart. It is said again as the menu comes back to the top (1532a2e). Red then green: test_the_menu_s_editor_notice_goes_once_the_editor_is_back_or_another_is_chosen.
