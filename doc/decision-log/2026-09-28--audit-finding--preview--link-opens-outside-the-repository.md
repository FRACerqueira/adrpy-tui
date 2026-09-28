# A link in a decision opened any file, including a network share

**Front:** Command fidelity and untrusted input (Fable) -- the Opus pass judged it not a bug, reading only | **Severity:** Medium | **Resolution:** Escalated | **Round:** 1

`follow_link` resolved any path: `//host/share/x.md` made the machine connect to another host, and `../../x.md` opened files outside the repository. The user chose: only .md inside the repository, refused before the file system is touched (ADR006V01). Covered by tests/test_ui.py::test_a_link_opens_only_a_file_inside_the_repository, with an inside link as positive control.
