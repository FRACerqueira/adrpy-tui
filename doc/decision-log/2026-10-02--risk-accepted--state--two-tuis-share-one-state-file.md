# Two TUIs open at once overwrite each other's settings

Each running TUI holds the whole state.json in memory and writes all of it on every change, so with two open the last to save wins, and both use the same state.json.partial, which can interleave on POSIX (on Windows a failed os.replace is skipped). Older than the update check, which only adds two save sites; raised as out of scope by the round 10 stability pass and accepted by the owner: losing it only means choosing a setting again.
