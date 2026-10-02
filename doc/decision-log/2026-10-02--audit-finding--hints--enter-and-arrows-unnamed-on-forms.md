# The key line did not name Enter and the arrows where they act on a form

**Front:** Usability and docs against code (Fable) | **Severity:** Medium | **Resolution:** Direct | **Round:** 8

Found from two sides: the usability pass (the decision picker's Enter, the only way to choose, was unnamed) and the test-adequacy pass (the guard checked only that a key named acts, never that a key acting is named). The guard now checks both directions; fixed: the picker's Enter and arrows, Enter on a focused button, the install-level config's radio buttons, migrate's list arrows (3693e5d).
