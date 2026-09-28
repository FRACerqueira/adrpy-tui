# A result replaced whatever screen was on top, leaving the form stuck as running

**Front:** Async event ordering in one session (Opus); also Command fidelity and untrusted input (Opus) (rated Low there) | **Severity:** High | **Resolution:** Escalated | **Round:** 1

`switch_screen` replaced the top screen: Ctrl+P (the command palette) opened over a running form made the result replace the palette, and the form came back running with no key working. The user chose: the command palette off, preview and show-all ignored while a command runs, and the result popping what is above its own screen. Reproduced with Ctrl+P (not with F3); covered by tests/test_async_screens.py.
