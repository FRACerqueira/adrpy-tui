# A failure showed only code, detail and data.errors, dropping the data that names its files

**Front:** TUI adherence to the current CLI contract (round 5) | **Severity:** Medium | **Resolution:** Direct | **Round:** 5

result_widgets showed a failure's code, detail and data.errors only. folderadr-change-would-adopt-unrelated-files, the prefix/separator/folderlog adopt codes, migration-write-failed and the *-scan-incomplete codes give a count in detail and the files only in data (adopted_files, results, unreadable), so the user could not tell which files block the change. The gap predates this cycle.

Fix: the rest of data is shown as key: value lines, as a success's is. Red then green in tests/test_ui.py.
