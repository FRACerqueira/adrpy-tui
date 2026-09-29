# A left write printing more than a pipe's buffer might block on Linux and macOS

**Reopen-when:** the first CI run on ubuntu or macos

Once a write is left, nobody reads its output; on POSIX, communicate has no background reader, so a child writing more than about 64 KB after Leave could block. Real adrpy writes a small JSON; not testable here (Windows only).
