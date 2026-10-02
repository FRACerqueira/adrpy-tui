# An answer reaching the Updates screen before it was mounted ended the app

**Front:** Stability and concurrency (Opus) -- round 11, on round 10's fixes | **Severity:** Low | **Resolution:** Direct | **Round:** 11

say_the_status used query_one("#update-status"), but a screen is on the stack before its widgets exist: PyPI's answer landing in that window raised NoMatches and ended the app. Not hit with real thread timing in 95 runs, reproduced by posting the answer in the same tick as the push. It now updates through query().results, as the main menu's notice does, and on_mount says the status (a73cdcb). Red then green: tests/test_update_notice.py::test_an_answer_while_the_updates_screen_is_being_built_does_not_crash. Class closed by the pass: a grep of screen_stack in src/ found no other query_one on a screen that may not be mounted.
