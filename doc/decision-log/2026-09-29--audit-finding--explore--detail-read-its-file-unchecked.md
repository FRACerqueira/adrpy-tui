# A decision's detail read its file without the preview's checks

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 3

The detail read the path adrpy named directly: outside the repository or through a folder link it still opened. It now reads through preview.excerpt, with the same checks and bounds. Covered by tests/test_ui.py (the detail through a junction).
