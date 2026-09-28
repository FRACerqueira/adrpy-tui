"""The screen every other one extends: the header, a scrolling body and a
line of key hints."""

from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Static

from adrpy_tui.core.registry import command_name
from adrpy_tui.ui.header import AppHeader


class AdrpyScreen(Screen):
    HINTS = "hints.back"  # language-pack key of the key-hints line

    def __init__(self, command=None, finished=False):
        super().__init__()
        self.command = command
        self._finished = finished

    def compose(self):
        line = None
        if self.command:
            key = "app.command_finished" if self._finished else "app.command_started"
            line = self.app.texts(key, command=command_name(self.command))
        yield AppHeader(line)
        with VerticalScroll(id="body"):
            yield from self.compose_body()
        yield Static(self.app.texts(self.HINTS), id="hints", markup=False)

    def compose_body(self):
        yield from ()
