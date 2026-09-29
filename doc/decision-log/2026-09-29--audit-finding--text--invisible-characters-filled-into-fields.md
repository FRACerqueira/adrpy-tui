# Suggestions, prefill and configuration values put invisible characters into fields

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 3

A scope, domain or configuration value holding a bidirectional override or a zero-width character filled a field as it was. Filling goes through the same SafeInput/SafeTextArea path; form suggestions are passed through field_text. Covered by tests/test_ui.py (the config editor with a hostile value, filled fields).
