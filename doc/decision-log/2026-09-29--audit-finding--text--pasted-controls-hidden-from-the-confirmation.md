# Control characters pasted into a field ran, but the confirmation did not show them

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Medium | **Resolution:** Direct | **Round:** 3

The confirmation showed --scope scope while adrpy received sc\x1bope\x7f: the display filtered what the value kept. The field now drops control, Cf, Zl and Zp characters itself (a multi-line field keeps its line breaks and tabs), so what is shown is what runs. Same fix and tests as the surrogate entry.
