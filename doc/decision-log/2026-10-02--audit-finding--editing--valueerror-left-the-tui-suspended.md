# A ValueError starting an editor left the TUI suspended or the wait open

**Front:** Stability and concurrency (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 8

Only OSError was caught around starting an editor; Client.run treats ValueError too. In the terminal path Textual's suspend() resumes only after a body that returned, so the TUI stayed suspended; in the window path the worker died and the wait never closed. Both catch ValueError now (de33e9a). Red then green: tests/test_editing.py::test_an_editor_that_cannot_start_is_said_and_nothing_is_checked[*-error1].
