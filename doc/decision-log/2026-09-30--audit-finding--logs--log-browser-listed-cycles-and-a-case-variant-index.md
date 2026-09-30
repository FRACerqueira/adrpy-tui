# The log browser listed CYCLES.md, and on Windows an index.md, as entries

**Front:** TUI adherence to the current CLI contract (round 5) | **Severity:** Low | **Resolution:** Direct | **Round:** 5

logs.py excluded only an exact INDEX.md; adrpy treats INDEX.md and CYCLES.md as the log's own pages and compares names with normcase. This repository's own CYCLES.md showed as an entry with an empty date; on Windows an index.md did too, and migrate offered one.

Fix: files.same_name compares as adrpy does, and both screens leave the pages out. Found by the documentation pass as well. Red then green in tests/test_ui.py.
