# Result values showed Windows paths with doubled backslashes, and a bare file name was previewed from the wrong folder

**Front:** TUI adherence to the current CLI contract (round 6 confirmation) | **Severity:** Low | **Resolution:** Direct | **Round:** 6

Lists and records in data were shown as JSON, doubling every backslash of a path; a preview of data.file holding only a name (file-already-exists, log-entry-already-exists) resolved against the process's working folder.

Fix: a list is shown item by item and a record field by field (an empty one as [] or {}, a null as null); a bare name is previewed in the log folder for a log code and in the decisions folder otherwise, any other relative path in the repository, decided without touching the disk. Red then green in tests/test_ui.py. Accepted as Low (second opinion): an item holding '; ' or a line feed reads ambiguously, and a log file in a log subfolder named only by its name is looked for at the log's root.
