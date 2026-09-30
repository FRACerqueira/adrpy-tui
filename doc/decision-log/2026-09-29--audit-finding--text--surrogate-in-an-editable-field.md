# A lone surrogate in an editable field reached the confirmation and adrpy

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Medium | **Resolution:** Direct | **Round:** 3

A value holding a lone surrogate (a pasted name that is not valid UTF-8) stayed in an Input or TextArea, could not be encoded on the way to adrpy, and drew wrongly. Closed as a class: every text field is a SafeInput or SafeTextArea (ui/inputs.py), which keeps only field_text (core/text.py); an AST test forbids a bare Input or TextArea in ui/. Covered by tests/test_text.py and tests/test_ui.py (typed, pasted, filled).
