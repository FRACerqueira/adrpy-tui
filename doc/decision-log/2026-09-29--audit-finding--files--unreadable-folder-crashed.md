# A folder that could not be read ended the app

**Front:** Resilience (Sonnet 5.5) | **Severity:** Medium | **Resolution:** Direct | **Round:** 3

PermissionError from is_dir, is_file or a listing reached a screen uncaught. core/files returns False for is_dir/is_file and skips an unreadable folder in a listing; inside_repository refuses on any OSError but a missing path. Covered by tests/test_files.py and tests/test_ui.py (a denied folder in the log browser).
