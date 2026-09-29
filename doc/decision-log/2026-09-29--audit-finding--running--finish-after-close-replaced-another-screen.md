# A run finishing after its screen closed put its result over another screen

**Front:** Async event ordering in one session (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 4

At quit a left write's thread still handed its result back; _finish then raised on the empty stack. With the screen gone from a live stack, the result replaced whatever was in front. _finish returns when its screen is detached or off the stack. Covered by tests/test_async_screens.py::test_a_run_finishing_after_its_screen_closed_changes_nothing.
