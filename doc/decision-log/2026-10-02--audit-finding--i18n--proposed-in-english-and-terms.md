# The editor's texts left Proposed in English and used other words than each pack

**Front:** Usability and docs against code (Fable) | **Severity:** Medium | **Resolution:** Direct | **Round:** 8

menu.editor.description and editor.title kept the English 'Proposed' in all 10 translated packs, which name the status otherwise everywhere; approve, Check, Esc and mark differed from each pack's own words in some new texts (fr, de, it, zh, ru, ja, ko, pt). All now use the pack's own terms (e66085c). Test: tests/test_hints.py::test_the_editor_s_texts_name_the_status_as_each_pack_does.
