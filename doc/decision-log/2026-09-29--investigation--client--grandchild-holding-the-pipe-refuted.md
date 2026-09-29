# A read whose grandchild holds the pipe ends as a timeout, as it should

After the kill, _stop waits at most 2 s for the output; a process adrpy started that holds it open makes the read end as tui-timeout, never a hang.
