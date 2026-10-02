# A failed update check could not be seen anywhere

**Front:** Usability and docs against code (Fable) | **Severity:** Low | **Resolution:** Escalated | **Round:** 10

ADR0008V01's "a failed check shows nothing" is a decision not to act on a failure, which needs a visibility plan: a check failing on every start looked the same as being up to date. The owner chose a status line on the Updates screen -- off, asking, failed, a newer version, or none newer -- the main menu still saying nothing on failure (74102ac, ADR0008 983a5a5). Red then green: tests/test_update_notice.py::test_the_updates_screen_says_what_the_check_found and ::test_the_updates_screen_says_while_pypi_is_asked_and_when_the_check_is_off.
