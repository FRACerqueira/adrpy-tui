"""Asks before a command runs, showing the exact command line."""

from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmScreen(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", show=False)]

    def __init__(self, command_line, question=None):
        super().__init__()
        self._command_line = command_line
        self._question = question

    def compose(self):
        texts = self.app.texts
        with Vertical(id="dialog"):
            yield Static(self._question or texts("confirm.question"), markup=False)
            yield Static(self._command_line, id="command-line", classes="summary", markup=False)
            with Horizontal(id="buttons"):
                yield Button(texts("confirm.yes"), id="yes", variant="primary")
                yield Button(texts("confirm.no"), id="no")

    def on_mount(self):
        self.query_one("#yes", Button).focus()

    def on_button_pressed(self, event):
        self.dismiss(event.button.id == "yes")

    def action_cancel(self):
        self.dismiss(False)
