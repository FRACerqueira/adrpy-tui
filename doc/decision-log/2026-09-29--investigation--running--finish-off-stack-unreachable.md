# A run finishing after its screen left the stack is not reachable

Every action handler is guarded by on_top, Esc is refused while running and the command palette is off: nothing pops the runner screen during a run.
