# The Updates screen's title and description named one of its two settings

**Front:** Usability and docs against code (Fable) | **Severity:** Low | **Resolution:** Direct | **Round:** 10

menu.updates.description and updates.title spoke only of the check, not of pre-releases, in all 11 packs, unlike editor.title which covers its whole list. Both now name both settings (74102ac); key and placeholder parity checked by tests/test_i18n.py.
