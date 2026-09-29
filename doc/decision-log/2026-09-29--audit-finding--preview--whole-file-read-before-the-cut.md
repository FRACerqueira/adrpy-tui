# A preview read the whole file before showing its start

**Front:** Resilience (Sonnet 5.5) | **Severity:** Low | **Resolution:** Direct | **Round:** 3

A very large file was read and decoded in full, then cut. core/files.read_start decodes in 1 MiB chunks and stops past PREVIEW_LINES and PREVIEW_CHARACTERS, still counting the totals. Covered by tests/test_files.py.
