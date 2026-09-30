# The decision and log listings followed folder links, looping on a circular junction

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 3

rglob followed a junction inside the decisions or log folder, reading outside the repository and looping on a circular one. Listings go through core/files.markdown_files, which prunes folder links. Also found by the resilience front, independently. Covered by tests/test_files.py and tests/test_ui.py (a junction).
