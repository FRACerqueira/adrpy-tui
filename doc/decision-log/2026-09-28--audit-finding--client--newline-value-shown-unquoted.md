# On Windows a value with a line break read as extra command lines on the confirmation

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 1

list2cmdline quotes only for a space or a tab. The display now quotes such a value; the argv is unchanged. Covered by tests/test_client.py::test_a_value_holding_a_line_break_is_shown_quoted_on_windows.
