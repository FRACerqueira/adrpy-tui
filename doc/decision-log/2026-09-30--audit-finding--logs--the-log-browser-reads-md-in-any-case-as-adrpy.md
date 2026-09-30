# The log browser now reads the log's .md and own pages in any case, as adrpy does

**Front:** Mirror of adrpy-ai round 53 (the log's .md in any case) | **Severity:** Low | **Resolution:** Escalated | **Round:** 7

adrpy-ai round 53 reads the decision log's `.md`, INDEX.md and CYCLES.md in any case on every system (the owner's choice). The log browser listed them by the system's rule, so on POSIX it would have left out an entry adrpy counts: markdown_files takes any_case for the log, and the log's own pages are compared lowercased.
