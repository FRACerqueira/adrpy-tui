# Bidirectional and invisible characters in names could make a name read as another

**Front:** Command fidelity and untrusted input (Opus and Fable, independently) | **Severity:** Low | **Resolution:** Escalated | **Round:** 1

The user chose: names, paths and command lines show Unicode Cf/Zl/Zp as <U+XXXX>; a decision's own text keeps them. core/text.py visible(); covered by tests/test_untrusted_text.py.
