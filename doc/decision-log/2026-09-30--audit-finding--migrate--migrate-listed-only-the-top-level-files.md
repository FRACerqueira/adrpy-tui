# The migrate screen listed only the decisions folder's top level, while adrpy's migrate rewrites every subfolder

**Front:** TUI adherence to the current CLI contract (round 6 confirmation) | **Severity:** Medium | **Resolution:** Direct | **Round:** 6

migrate.py listed markdown_files(folder, recursive=False): a legacy file in a subfolder was never shown, a repository holding only such files could not be adopted from the TUI, and in a mixed one adrpy migrated files the screen never listed.

Fix: the whole folder is listed, by the path in the folder, and the preview rows name files the same way (two subfolders may hold one name). Only the root INDEX.md is left out, as adrpy's scan does. Red then green in tests/test_ui.py.
