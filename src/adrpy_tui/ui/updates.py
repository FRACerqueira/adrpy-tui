"""Whether the TUI checks PyPI for a newer adrpy-tui on every start, and
whether pre-releases count, chosen in the main menu's "Updates" item
(ADR0008V01)."""

from textual.binding import Binding
from textual.widgets import OptionList, Static

from adrpy_tui.ui.base import HINTS_MENU, AdrpyScreen, on_top
from adrpy_tui.ui.menu import BACK
from adrpy_tui.ui.paged import PagedList, row

CHECK = "check"
PRERELEASES = "prereleases"


class UpdatesScreen(AdrpyScreen):
    HINTS = HINTS_MENU
    BINDINGS = [Binding("escape", "back", show=False)]

    def compose_body(self):
        yield Static(self.app.texts("updates.title"), classes="title")
        yield PagedList(row(self.app.texts("menu.back"), id=BACK), self._row(CHECK), self._row(PRERELEASES),
                        list_id="settings")

    def _row(self, setting):
        on = self.app.user_state.update_check if setting == CHECK else self.app.user_state.prereleases
        return row(f"{'[x]' if on else '[ ]'} {self.app.texts(f'updates.{setting}')}", id=setting)

    def on_mount(self):
        options = self.query_one("#settings", OptionList)
        options.highlighted = options.get_option_index(CHECK)
        options.focus()

    def on_option_list_option_selected(self, event):
        if not on_top(self):
            return
        if event.option.id == BACK:
            self.action_back()
            return
        state = self.app.user_state
        if event.option.id == CHECK:
            state.set_update_check(not state.update_check)
            self.app.check_for_update()
        else:
            state.set_prereleases(not state.prereleases)
        options = self.query_one("#settings", OptionList)
        options.replace_option_prompt(event.option.id, self._row(event.option.id).prompt)

    def action_back(self):
        self.app.pop_screen()
