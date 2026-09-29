# A file field the system refuses to look at ended the app

**Front:** Resilience (Sonnet 5.5) | **Severity:** Medium | **Resolution:** Direct | **Round:** 4

core/fields.py checked a file field with a bare Path.is_file, which raises PermissionError for a file access is denied to. It uses files.is_file. This also retracts a remark of round 3 (never logged) that the check was dead code: installconfig's --seed uses it. Swept: no other file access outside core/files.py but packaged resources and the state file. Covered by tests/test_files.py.
