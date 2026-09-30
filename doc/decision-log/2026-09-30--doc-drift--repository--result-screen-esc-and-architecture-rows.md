# The result screen's Esc, two architecture rows and the CHANGELOG's round order did not match the code

**Front:** Documentation versus code (round 6 confirmation) | **Severity:** Low | **Resolution:** Direct | **Round:** 6

doc/forms.md said Esc returns to the screen the command ran from; the result replaces the form, so it returns to where the form was opened, and to the rebuilt main menu after init, config or migrate. doc/architecture.md left argv out of Result and the changed keys out of state.py. The CHANGELOG listed round five before four. Fixed, with round 6's line added; tests/test_docs.py passes.
