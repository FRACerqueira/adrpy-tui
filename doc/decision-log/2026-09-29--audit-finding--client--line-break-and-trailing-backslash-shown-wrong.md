# The confirmation showed a value with a line break and a trailing backslash wrongly on Windows

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 2

The added quotes did not double the trailing backslashes, so the closing quote read as escaped. Quoted now by the Windows rules; the argv never changed. Covered by tests/test_client.py.
