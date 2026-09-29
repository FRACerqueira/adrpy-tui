"""Asks before a command runs, showing the exact command line."""

from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from adrpy_tui.ui.base import on_top


class ConfirmScreen(ModalScreen[bool]):
    # The command line scrolls in a box of its own, so a long one (a log
    # body, a template) never pushes its start or the buttons off the
    # screen; the keys a list uses scroll it while Yes keeps the focus.
    BINDINGS = [Binding("escape", "cancel", show=False),
                *(Binding(key, f"scroll('{way}')", show=False) for key, way in (
                    ("up", "up"), ("down", "down"), ("pageup", "page_up"), ("pagedown", "page_down"),
                    ("home", "home"), ("end", "end")))]

    def __init__(self, command_line, question=None):
        super().__init__()
        self._command_line = command_line
        self._question = question

    def compose(self):
        texts = self.app.texts
        with Vertical(id="dialog"):
            yield Static(self._question or texts("confirm.question"), markup=False)
            with VerticalScroll(id="command-scroll"):
                yield Static(self._command_line, id="command-line", classes="summary", markup=False)
            with Horizontal(id="buttons"):
                yield Button(texts("confirm.yes"), id="yes", variant="primary")
                yield Button(texts("confirm.no"), id="no")

    def on_mount(self):
        self.query_one("#yes", Button).focus()

    def on_button_pressed(self, event):
        if not on_top(self):
            return
        self.dismiss(event.button.id == "yes")

    def action_scroll(self, way):
        getattr(self.query_one("#command-scroll"), f"scroll_{way}")(animate=False)

    def action_cancel(self):
        self.dismiss(False)
