# migrate compared a folderadr in another case, or with a trailing dot, with adrpy's resolved paths

**Front:** TUI adherence to the current CLI contract (round 6 confirmation) | **Severity:** Low | **Resolution:** Direct | **Round:** 6

Round 5 normalized . and .. only; adrpy's paths come from resolve(), which on Windows also fixes case and drops trailing dots and spaces, so a decision with a header was still offered.

Fix: the folder is checked lexically first (ADR0006V02: a folder link on the way is never followed, and a path is never resolved before that check), then resolved only to compare. The first version resolved before the check and so followed a folderadr that is a junction inside the repository: the independent second opinion found it before the commit, and tests/test_ui.py now covers a link at the folder and at its parent. The re-review's one Low, a \\?\ repository path with a trailing-dot junction, is closed by spelling the checked path with abspath. Accepted: explore's folder column keeps its lexical label.
