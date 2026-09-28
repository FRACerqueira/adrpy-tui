# A long command pushed its start and the Yes button off the confirmation screen

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Medium | **Resolution:** Direct | **Round:** 1

A 60-line log body made the dialog taller than the screen; the keyboard could not bring the command's start back, and Enter still ran it. Fixed: the command line scrolls in its own box with the list keys. Covered by tests/test_ui.py::test_a_long_command_fits_the_confirmation_and_scrolls_by_keyboard.
