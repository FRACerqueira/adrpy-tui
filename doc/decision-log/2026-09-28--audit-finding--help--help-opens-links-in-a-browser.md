# A link in a command's help opened the browser, where every other preview only names it

**Front:** Command fidelity and untrusted input (Fable) | **Severity:** Low | **Resolution:** Escalated | **Round:** 1

The user chose the same rule as the previews: `open_links=False`, the link named. Covered by tests/test_ui.py::test_a_link_in_a_command_s_help_is_never_opened.
