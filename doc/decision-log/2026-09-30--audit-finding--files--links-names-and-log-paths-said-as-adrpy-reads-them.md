# A folder behind a link was called outside, .md and the log's pages were compared unlike adrpy, and a log path previewed wrong

**Front:** TUI folders, links and exclusions (round 7) | **Severity:** Low | **Resolution:** Direct | **Round:** 7

A folder or file reached through a folder link (refused by ADR0006V02) was said to be outside the repository; outside_reason now tells the two apart and the screens say which. `.md` was matched case-blind everywhere where adrpy's scan uses os.path.normcase (so `x.MD` on Linux was offered to migrate); the log browser now hides INDEX.md and CYCLES.md as adrpy-ai round 52 compares them (normcase, anywhere). Explore's folder column read `adr` for a folderadr spelled `doc/adr.`. A result's log file named by its path in the log folder (`sub/notes.md`) was previewed at the repository's root.
