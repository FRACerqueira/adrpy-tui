"""Asks before a command runs, showing the exact command line."""

from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from adrpy_tui.ui.base import dialog_keys, key_line, on_top


class ConfirmScreen(ModalScreen[bool]):
    # The command line scrolls in a box of its own, so a long one (a log
    # body, a template) never pushes its start or the buttons off the
    # screen; the keys a list uses scroll it while Yes keeps the focus.
    BINDINGS = [Binding("escape", "cancel", show=False),
                *(Binding(key, f"scroll('{way}')", show=False) for key, way in (
                    ("up", "up"), ("down", "down"), ("pageup", "page_up"), ("pagedown", "page_down"),
                    ("home", "home"), ("end", "end")))]

    def __init__(self, command_line, question=None, note=None, danger=False):
        """`danger`: the command destroys something or is hard to undo, and
        Yes is red (core/registry.py `destroys`)."""
        super().__init__()
        self._command_line = command_line
        self._question = question
        self._note = note
        self._danger = danger

    def compose(self):
        texts = self.app.texts
        with Vertical(id="dialog"):
            yield Static(self._question or texts("confirm.question"), markup=False)
            box = VerticalScroll(id="command-scroll")
            box.display = bool(self._command_line)  # a question alone ("Leave without saving?")
            with box:
                yield Static(self._command_line, id="command-line", classes="summary", markup=False)
            if self._note:
                yield Static(self._note, id="crlf-note", classes="info", markup=False)
            with Horizontal(id="buttons"):
                yield Button(texts("confirm.yes"), id="yes", variant="error" if self._danger else "primary")
                yield Button(texts("confirm.no"), id="no")
            yield dialog_keys(self.app, self.hints())

    _scrolls = False

    def hints(self):
        hints = (("arrows", "scroll"),) if self._scrolls else ()
        return (*hints, ("tab", "other_button"), ("enter", "choose"), ("escape", "answer_no"))

    def on_mount(self):
        self.query_one("#yes", Button).focus()
        # Whether the command line scrolls is known once it is laid out.
        self.call_after_refresh(self._name_the_scroll)

    def _name_the_scroll(self):
        if self.is_attached and self.query_one("#command-scroll").max_scroll_y > 0:
            self._scrolls = True
            self.query_one("#dialog-keys", Static).update(key_line(self.app, self.hints()))

    def on_button_pressed(self, event):
        if not on_top(self):
            return
        self.dismiss(event.button.id == "yes")

    def action_scroll(self, way):
        getattr(self.query_one("#command-scroll"), f"scroll_{way}")(animate=False)

    def action_cancel(self):
        self.dismiss(False)
