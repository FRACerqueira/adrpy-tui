"""The interface's text fields. Whatever a field is given -- typed, pasted,
or filled in from a file, a header or the configuration -- it keeps only
printable text (core/text.py `field_text`): no control, no lone surrogate,
no character that hides itself. So what the confirmation shows is what
runs, and what is drawn can always be encoded. Every field of the interface
is one of these (tests/test_ui.py checks it)."""

from textual.widgets import Input, TextArea

from adrpy_tui.core.text import field_text


class SafeInput(Input):
    def validate_value(self, value):
        # Textual runs this on every assignment of `value`: a key, a paste,
        # the code filling the field in.
        return field_text(value)


class SafeTextArea(TextArea):
    """A multi-line field: its line breaks (CRLF too) and tabs are kept."""

    def __init__(self, text="", **options):
        super().__init__(field_text(text, multiline=True), **options)

    def load_text(self, text):
        super().load_text(field_text(text, multiline=True))

    def edit(self, edit):
        # Every change goes through here: a key, a paste, insert, replace.
        edit.text = field_text(edit.text, multiline=True)
        return super().edit(edit)
