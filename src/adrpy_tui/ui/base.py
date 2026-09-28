"""The screen every other one extends: the header, a scrolling body and a
line of key hints, built from the keys in use (core/keys.py)."""

from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Static

from adrpy_tui.core import keys
from adrpy_tui.core.registry import command_name
from adrpy_tui.ui.header import AppHeader

# A key line: (key, hint) pairs. A key is a fixed one's name (keyname.<key>)
# or "@<action>", the key the person gave that action (core/keys.py).
HINTS_MAIN = (("arrows", "move"), ("enter", "select"), ("escape", "exit"))
HINTS_MENU = (("arrows", "move"), ("enter", "select"), ("escape", "back"))
HINTS_BACK = (("escape", "back"),)
HINTS_LIST = (("arrows", "move"), ("enter", "select"), ("@preview", "preview"), ("escape", "back"))
HINTS_FORM = (("tab", "next_field"), ("right", "accept_suggestion"), ("@run", "run"), ("escape", "back"))
HINTS_PICKER_FORM = (("tab", "next_field"), ("@preview", "preview"), ("@toggle", "show_all"), ("@run", "run"),
                     ("escape", "back"))


def key_line(app, hints):
    parts = []
    for key, hint in hints:
        name = keys.display(app.key_of(key[1:]), app.texts) if key.startswith("@") else app.texts(f"keyname.{key}")
        parts.append(f"{name} {app.texts(f'hint.{hint}')}")
    return " · ".join(parts)


class AdrpyScreen(Screen):
    HINTS = HINTS_BACK
    # A screen of text to read (help, preview): its body takes the focus, and
    # the arrows scroll it. On every other screen the body never takes it --
    # it would be the first focusable widget, ahead of the list or the first
    # field, and the arrows would scroll the page instead of moving the list.
    READS = False

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
        body = VerticalScroll(id="body")
        body.can_focus = self.READS
        with body:
            yield from self.compose_body()
        yield Static(key_line(self.app, self.HINTS), id="hints", markup=False)

    def compose_body(self):
        yield from ()

    def focus_first(self):
        """Gives the focus to the first widget that takes keys, once content
        mounted after the screen opened is there; to the body, to scroll it,
        when there is none. After the next refresh: the focus order follows
        where widgets sit, and what was just mounted has no place yet."""
        self.call_after_refresh(self._focus_first)

    def _focus_first(self):
        if not self.is_attached or self.focused is not None:
            return
        self.focus_next()
        if self.focused is None:
            body = self.query_one("#body")
            body.can_focus = True
            body.focus()
