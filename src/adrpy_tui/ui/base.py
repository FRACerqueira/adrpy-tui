"""The screen every other one extends: the header, a scrolling body and a
line of key hints, built from the keys in use (core/keys.py)."""

import inspect

from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import LoadingIndicator, Static

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


def on_top(screen):
    """Whether `screen` is the one in front. Keys that reach the app before
    the first is handled are all queued on the screen in front then: a later
    one must not act from a screen already closed -- it would close or open
    whatever is in front by then."""
    return screen.is_attached and screen.app.screen is screen


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
        self._reads = 0  # the latest read's number: an older one's answer is dropped

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

    def read(self, work, show):
        """Runs `work(app)` -- adrpy calls -- in a thread and hands what it
        returns to `show` on this screen, once it answers. Only while this
        screen is still open and only the latest read: the person may have
        left, or asked again, meanwhile. A failure of either becomes a note
        on the screen, never the end of the app."""
        self._reads += 1
        number, app = self._reads, self.app  # the thread never reaches the app through this screen

        def thread():
            try:
                outcome = work(app)
            except Exception as error:  # noqa: BLE001 -- shown, never lost
                outcome = _Failed(error)
            app.call_from_thread(self._deliver, number, show, outcome)

        self.run_worker(thread, thread=True)

    def is_open(self):
        return self.is_attached and self in self.app.screen_stack

    async def _deliver(self, number, show, outcome):
        if number != self._reads or not self.is_open():
            return
        try:
            if isinstance(outcome, _Failed):
                raise outcome.error
            shown = show(outcome)
            if inspect.isawaitable(shown):
                await shown
        except Exception as error:  # noqa: BLE001
            if self.is_open():  # a screen left half-way through is not a failure
                await self.show_internal_error(error)

    async def show_internal_error(self, error):
        note = self.app.internal_error_text(error)
        body = self.query_one("#body")
        await body.query(LoadingIndicator).remove()
        await body.query("#internal-error").remove()
        await body.mount(Static(note, id="internal-error", classes="error", markup=False), before=0)
        self.focus_first()

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


class _Failed:
    """What a read's thread returns when its work raised."""

    def __init__(self, error):
        self.error = error
