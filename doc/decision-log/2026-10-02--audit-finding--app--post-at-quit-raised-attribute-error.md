# Posting the update check's answer as the app quit could raise AttributeError in the thread

**Front:** Stability and concurrency (Opus) -- round 11, on round 10's fixes | **Severity:** Low | **Resolution:** Direct | **Round:** 11

Textual's post_message reads app._loop twice from a foreign thread; run_async setting it to None in between raised AttributeError, which the except RuntimeError around the post let through to threading.excepthook (a traceback after quitting). Reproduced only synthetically. The post now catches both (a73cdcb); the handler still runs on the app thread, so its own failures are not swallowed. Red then green: tests/test_update_notice.py::test_an_answer_posted_as_the_app_ends_leaves_no_thread_error. Out of scope, noted by the pass: call_from_thread has the same double read in base.py, editing.py and running.py, older code run from Textual workers.
