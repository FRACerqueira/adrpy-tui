# Damaged adrpy-tui metadata stopped the start and --version

**Front:** Resilience (Sonnet 5.5) | **Severity:** Low | **Resolution:** Direct | **Round:** 3

adrpy_range and _print_version caught only PackageNotFoundError; metadata that is not UTF-8 raised. Both now also catch ValueError and OSError, as installed_version does. Covered by tests/test_versions.py.
