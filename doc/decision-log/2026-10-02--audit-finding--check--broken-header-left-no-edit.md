# After an edit broke the header, the decision could not be edited again from the TUI

**Front:** Usability and docs against code (Sonnet) | **Severity:** Medium | **Resolution:** Escalated | **Round:** 9

Check after an edit said Edit opens it again, and ADR0007V01 item 4 that the editor can be opened again; but a broken header makes explore report is_valid false (confirmed with the real adrpy: invalid-header), the TUI reads it as invalid, not Proposed, and its detail offers no Edit. The owner chose (b): Check after a failed edit offers Edit it again for the file just edited (1532a2e). Red then green: tests/test_hints.py::test_check_after_an_edit_that_broke_the_header_offers_to_edit_it_again.
