# The confirmation drew a CRLF value with LF breaks and did not say so

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Low | **Resolution:** Escalated | **Round:** 4

A CR cannot be drawn, so a template kept with CRLF read differently from what ran. Owner's choice: a note below the command line says a value keeps CRLF line endings (confirm.crlf, 11 languages). Covered by tests/test_ui.py::test_the_confirmation_says_when_a_value_keeps_crlf_line_endings.
