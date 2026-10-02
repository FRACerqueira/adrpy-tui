# Mutations of this release's code that no test caught

**Front:** Test adequacy by mutation (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 8

About 120 mutations of v0.1.0..develop; surviving ones now fail a test: the list after Restore every color/key, the yellow buttons' text from the warnings role, the exact notice of a refused edit, no exit code after a clean close, no Edit on a detail whose read failed, no next step after a failed command, an editor gone between choosing and opening, two fields wrong at once, same_path, the mark's columns, and the exit guards of the Editor screen and the editor's wait (17882c5, ea32d77, c9e4bd8). Each was checked by re-running its mutation. Left untested: cmd.exe's /v:off and /d (no effect on a default machine; testing them would mean changing the registry).
