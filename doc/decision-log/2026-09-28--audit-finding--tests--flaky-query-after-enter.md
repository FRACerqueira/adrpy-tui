# UI tests queried a screen right after Enter and failed about once in ten parallel runs

**Front:** Test adequacy (Fable) | **Severity:** Medium | **Resolution:** Direct | **Round:** 1

3 failures in 28 CI-mode runs, in tests through `_open_appearance`. Class: every `press("enter")` not followed by a wait in tests/test_ui.py (a script listed 12); each now settles.
