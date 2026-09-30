# Enter on a migrate preview row crashed the TUI

**Front:** Async event ordering in one session (Opus) (outside its angle) | **Severity:** Medium | **Resolution:** Direct | **Round:** 2

The files list's handler took the preview's rows for files (IndexError). Checked by the main model; covered by tests/test_async_screens.py::test_enter_on_a_migrate_preview_row_is_not_taken_for_a_file.
