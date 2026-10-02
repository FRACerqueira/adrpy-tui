# The update notice tests reused their PyPI fakes across re-runs

**Front:** Stability and concurrency (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 10

The Published fakes were built once in a parametrize, so a re-run in the same session (pytest-repeat, rerunfailures) inherited their call count and stopped waiting before the answer came; the after-quit test never checked the thread ended cleanly. Each test now builds its own, waits on the app's own status, and a thread_errors fixture asserts no thread ended with an exception (74102ac).
