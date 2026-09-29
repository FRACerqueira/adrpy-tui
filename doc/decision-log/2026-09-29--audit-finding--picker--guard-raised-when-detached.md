# The decision picker's guard raised when its form had closed

**Front:** Async event ordering in one session (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 3

on_top(self.screen) raised NoScreen once the picker was removed: the guard meant to drop a late event ended the app. on_top takes a widget and answers False when it is detached; the picker calls on_top(self). Swept: no other widget called on_top with .screen. Covered by tests/test_ui.py.
