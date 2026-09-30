# The install-level editor called fields guarded, and an unreadable config left no hint how to recover

**Front:** TUI adherence to the current CLI contract (round 5) | **Severity:** Low | **Resolution:** Direct | **Round:** 5

The config editor added the guarded note on the install-level editor too, where installconfig guards nothing. A configuration adrpy refuses to read (a folder outside the repository) disabled every item that needs a repository, the config editor included, and nothing said the file had to be repaired by hand. version's switch said it starts from the empty template, where --empty starts from the default template.

Fix: the note on the repository's editor only; the menu adds menu.repo_problem_fix; field.empty says what --empty does. Both texts are in all eleven packs. Red then green in tests/test_ui.py.
