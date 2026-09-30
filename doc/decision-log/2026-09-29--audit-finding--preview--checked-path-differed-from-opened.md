# open_preview checked one spelling of a path and opened another

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 3

The check ran on the path as given and the open on its normalised form. The path is normalised once (normpath of abspath), then checked, then opened. Covered by tests/test_ui.py (open_preview normalised).
