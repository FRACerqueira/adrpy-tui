# Quitting during a write once held the app about 60 s

**Front:** Test adequacy (Fable) | **Severity:** Medium | **Resolution:** Direct | **Round:** 3

test_quitting_during_a_write_leaves_it stalled once in 77 runs: a Textual timer sleeps in an executor thread on Windows, and the still-running timer (READ_TIMEOUT) still sleeping held the quit. It is now the loop's own call_later, cancelled when the run ends. Red is not achievable: the stall is a thread-timing race seen once in 77 runs; the fix removes the thread that held it.
