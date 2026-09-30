# A link in a decision crashed the TUI through its notification, which read markup

**Front:** Command fidelity and untrusted input (Opus and Fable, independently) | **Severity:** High | **Resolution:** Direct | **Round:** 1

`app.notify` renders markup by default; Textual unquotes a link's href, so `[t](<foo[/]>)` in a decision raised MarkupError on one click, and `[@click=...]` made a clickable action. Fixed: `markup=False` on every notify (preview.py, config.py, help.py). Reproduced; covered by tests/test_untrusted_text.py. Class: every `notify(` in src/.
