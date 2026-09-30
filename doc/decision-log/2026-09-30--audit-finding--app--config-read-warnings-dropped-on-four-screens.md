# The warnings of reading the configuration did not show on the menu, the config editor and migrate

**Front:** TUI adherence to the current CLI contract (round 5) | **Severity:** Low | **Resolution:** Direct | **Round:** 5

adrpy merges the config-read warnings (a retired field) into every answer, but the start-up read (main menu), the configuration editor's read and migrate's config and explore reads dropped them; explore's unrecognized-files warning was lost on migrate too.

Fix: the main menu, the config editor and migrate show them. The decision picker's read does not: the menu shows the same warning when the repository opens, and every run's result shows its own. Red then green in tests/test_ui.py.
