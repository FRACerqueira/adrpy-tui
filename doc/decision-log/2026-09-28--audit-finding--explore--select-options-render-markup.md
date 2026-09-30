# A folder or log classification named like markup crashed the filter lists or became a clickable action

**Front:** Command fidelity and untrusted input (Opus and Fable, independently) -- Fable rated it High, Opus Medium | **Severity:** High | **Resolution:** Direct | **Round:** 1

Select turns a str prompt into markup: a folder `[/x]` crashed explore's folder filter, `[@click=app.quit]` in a log classification ran the action on click. Fixed: `Text(visible(...))` prompts in explore.py and logs.py. Reproduced; covered by tests/test_untrusted_text.py. Class: every `Select(`/`set_options(` in ui/; the others take fixed values.
