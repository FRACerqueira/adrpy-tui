# A result replacing an unrelated screen is no longer reachable

The async pass found that a result whose screen left the stack replaced whatever was in front. It needed the runner screen popped during a run, reachable only through two queued presses on the confirmation; with every action handler guarded by on_top, Esc refused while running and the palette off, nothing pops it. Left as is; its test was removed.
