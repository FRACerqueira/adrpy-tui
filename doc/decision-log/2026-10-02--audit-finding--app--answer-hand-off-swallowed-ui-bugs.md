# A bug showing the update check's answer was swallowed by the thread

**Front:** Stability and concurrency (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 10

_ask_pypi called call_from_thread inside except Exception: pass, so a failure in the UI's own handling of the answer (the notice, the texts) was raised back in the thread and dropped -- no notice, no error log -- while the same bug on a menu resume crashed visibly. The answer is now posted as a message (Textual's thread-safe post_message), only RuntimeError from a loop closed as the app quits is caught, and a failure handling it is the app's, as any handler's (74102ac). Red then green: tests/test_update_notice.py::test_a_failure_showing_the_answer_is_not_swallowed, its answer held until the main menu is shown so only the hand-off can meet the bug.
