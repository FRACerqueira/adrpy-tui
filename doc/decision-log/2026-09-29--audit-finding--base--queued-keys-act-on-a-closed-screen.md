# Keys queued while the app was busy acted from a screen already closed

**Front:** Async event ordering in one session (Opus) | **Severity:** Medium | **Resolution:** Direct | **Round:** 2

The second of two keys reached a closed screen's handler, which closed or opened whatever was in front: an empty app, a crash, a config edit lost. Every action handler first checks on_top (ui/base.py); an AST test checks all 29. Covered by tests/test_textual_names.py and two tests in tests/test_async_screens.py.
