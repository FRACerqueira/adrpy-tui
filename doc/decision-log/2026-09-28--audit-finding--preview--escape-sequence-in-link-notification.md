# An escape sequence in a link reached the terminal through the Not a file notification

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** High | **Resolution:** Direct | **Round:** 1

Textual unquotes an href, so `%1b` in a link became ESC in the path of the missing-file notification, which was shown raw. Fixed: every path and href shown through `visible()`. Covered by tests/test_untrusted_text.py::test_a_hostile_link_in_a_decision_is_only_named.
