# The first test of Esc on the start-up screen passed whatever the code did

**Front:** Calibration (no dedicated audit front -- found re-running the round's mutations) | **Severity:** Low | **Resolution:** Direct | **Round:** 2

run_app's settle waited out the held read, so the main menu -- whose Esc quits too -- answered. Rewritten without run_app; it fails with the binding removed and runs in 0.6 s instead of 16 s.
