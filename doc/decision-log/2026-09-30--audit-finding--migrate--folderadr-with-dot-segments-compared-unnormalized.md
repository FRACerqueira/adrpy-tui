# migrate compared a folderadr with dot segments unnormalized and offered a decision that has a header

**Front:** TUI adherence to the current CLI contract (round 5) | **Severity:** Low | **Resolution:** Direct | **Round:** 5

adrpy accepts a folderadr such as doc/./x/../adr. migrate joined it to the repository without normalizing, so its paths never matched explore's normalized ones, and a decision with a header was offered for migration; decisions.folder_of had the same gap for explore's folder column.

Fix: both normalize with os.path.normpath. Red then green in tests/test_ui.py.
