# Any exception in a read or its handler ended the TUI with a traceback

**Front:** Resilience (Sonnet 5.5) | **Severity:** High | **Resolution:** Escalated | **Round:** 1

An OSError starting adrpy, warnings of the wrong type, a decision without filename: each raised in a worker or its handler and ended the app, sometimes after a write had run. The user chose one wrapper: AdrpyScreen.read shows any failure on its screen and writes the traceback to error.log; the client normalises code, detail and warnings and never raises. Covered by tests/test_async_screens.py and tests/test_client.py. Class: `run_worker|call_from_thread` now only in base.py and running.py.
