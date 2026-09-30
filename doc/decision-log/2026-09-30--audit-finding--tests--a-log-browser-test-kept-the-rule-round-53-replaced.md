# A log browser test still expected the case-sensitive rule on POSIX

**Front:** Calibration (no dedicated audit front -- found by the first POSIX CI run since round 50) | **Severity:** Low | **Resolution:** Direct | **Round:** 7

The round 7 test of the log browser's own pages expected cycles.md and sub/index.md listed where names are case-sensitive; adrpy-ai round 53 reads the log in any case on every system, and the browser with it. The first CI run on ubuntu and macOS failed it. Fixed and run on ext4 (WSL, a venv as CI's): 611 passed.
