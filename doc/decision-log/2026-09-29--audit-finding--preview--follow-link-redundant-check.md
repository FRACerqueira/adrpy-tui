# follow_link repeated the check open_preview makes

**Front:** Test adequacy (Fable) | **Severity:** Low | **Resolution:** Direct | **Round:** 3

A second inside_repository check in follow_link could drift from the one in open_preview. follow_link now hands the joined path to open_preview, the one place it is checked.
