# The log browser hid cycles.md and a subfolder's index.md, files adrpy counts as strays that block log

**Front:** TUI adherence to the current CLI contract (round 6 confirmation) | **Severity:** Low | **Resolution:** Retraction | **Round:** 6

Round 5 made the log browser leave out INDEX.md and CYCLES.md case-blind at any depth. adrpy leaves out only INDEX.md at the log's root case-blind, and INDEX.md or CYCLES.md by their exact name anywhere; any other file makes check warn and log refuse, so the browser hid the very file blocking the user.

Fix: the browser mirrors adrpy's two rules. Red then green in tests/test_ui.py; the second opinion checked the browser against adrpy check's stray list on twelve names, all matching.
