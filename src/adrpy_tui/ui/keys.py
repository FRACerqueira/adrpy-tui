"""The keys of the configurable actions (core/keys.py): each with the key
it has; Enter waits for a new one, kept at once. A key another action has,
or one every screen relies on, is refused with the reason."""

from textual import events
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import OptionList, Static

from adrpy_tui.core import keys
from adrpy_tui.ui.base import HINTS_MENU, AdrpyScreen, on_top
from adrpy_tui.ui.confirm import ConfirmScreen
from adrpy_tui.ui.menu import BACK
from adrpy_tui.ui.paged import PagedList, row

RESET_ALL = "reset-all"
CHANGED = "•"


class KeysScreen(AdrpyScreen):
    HINTS = HINTS_MENU
    BINDINGS = [Binding("escape", "back", show=False)]

    def compose_body(self):
        texts = self.app.texts
        yield Static(texts("keys.title"), classes="title")
        yield PagedList(row(texts("menu.back"), id=BACK), *(self._option(action) for action in keys.ACTIONS),
                        row(texts("keys.reset_all"), id=RESET_ALL), list_id="actions")
        yield Static(texts("keys.fixed"), classes="info", markup=False)

    def _option(self, action):
        texts = self.app.texts
        mark = f" {CHANGED}" if action in self.app.chosen_keys else ""
        key = keys.display(self.app.key_of(action), texts)
        return row(f"{texts(f'keys.action.{action}')}: {key}{mark}", id=action)

    def on_mount(self):
        options = self.query_one("#actions", OptionList)
        options.highlighted = 1
        options.focus()

    def _reset_all(self):
        self.app.reset_keys()
        self._refresh()

    def _refresh(self):
        options = self.query_one("#actions", OptionList)
        for action in keys.ACTIONS:
            options.replace_option_prompt(action, self._option(action).prompt)

    def on_option_list_option_selected(self, event):
        if not on_top(self):
            return
        if event.option.id == BACK:
            self.action_back()
        elif event.option.id == RESET_ALL:
            self.app.push_screen(ConfirmScreen("", question=self.app.texts("keys.reset_all_confirm"), danger=True),
                                 lambda yes: yes and self._reset_all())
        else:
            action = event.option.id
            self.app.push_screen(KeyCaptureScreen(action), lambda key: self._captured(action, key))

    def _captured(self, action, key):
        if key is None:  # cancelled
            return
        self.app.set_key(action, key or None)  # "" is back to the default
        self._refresh()

    def action_back(self):
        self.app.pop_screen()


class KeyCaptureScreen(ModalScreen):
    """Waits for the next key; dismisses it, "" for the default, or None.
    Esc cancels; Backspace goes back to the default."""

    def __init__(self, action):
        super().__init__()
        self._action = action

    def compose(self):
        texts = self.app.texts
        with Vertical(id="dialog"):
            yield Static(texts(f"keys.action.{self._action}"), classes="title")
            yield Static(texts("keys.press"), classes="info", markup=False)
            yield Static("", id="key-problem", classes="error", markup=False)

    def on_key(self, event: events.Key):
        if not on_top(self):
            return
        event.stop()
        event.prevent_default()
        key = event.key
        if key == "escape":
            self.dismiss(None)
            return
        if key == "backspace":
            self.dismiss("")
            return
        reason = keys.problem(key)
        taken = next((other for other in keys.ACTIONS if other != self._action and self.app.key_of(other) == key),
                     None)
        texts = self.app.texts
        if reason:
            self.query_one("#key-problem", Static).update(texts(reason, key=keys.display(key, texts)))
        elif taken:
            self.query_one("#key-problem", Static).update(
                texts("keys.taken", key=keys.display(key, texts), action=texts(f"keys.action.{taken}")))
        else:
            self.dismiss(key)
