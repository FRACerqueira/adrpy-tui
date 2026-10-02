# An editor could start after the wait was left or the TUI was quitting

**Front:** Stability and concurrency (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 8

Client.edit called Popen before looking at the leave/closing events, unlike _run: the editor's window would open after the person left or the TUI was gone. It now starts nothing then (de33e9a). Red then green: tests/test_client.py::test_no_editor_starts_once_the_wait_is_left_or_the_tui_quits.
