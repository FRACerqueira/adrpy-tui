# The running_leaves set duplicated what Client.shutdown does

**Front:** Test adequacy (Fable) | **Severity:** Low | **Resolution:** Direct | **Round:** 3

Quitting set every running write's leave, then shut the client down, which ends them all. The set is removed; shutdown in on_unmount is the one path.
