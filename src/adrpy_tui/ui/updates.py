"""Whether the TUI checks PyPI for a newer adrpy-tui on every start, and
whether pre-releases count, chosen in the main menu's "Updates" item, with
what the check found in this run (ADR0008V01)."""

from textual.binding import Binding
from textual.widgets import OptionList, Static

from adrpy_tui.core import updates, versions
from adrpy_tui.ui.base import HINTS_MENU, AdrpyScreen, on_top
from adrpy_tui.ui.menu import BACK
from adrpy_tui.ui.paged import PagedList, row

CHECK = "check"
PRERELEASES = "prereleases"
HINTS_SETTING = (("arrows", "move"), ("space_enter", "mark"), ("escape", "back"))


class UpdatesScreen(AdrpyScreen):
    BINDINGS = [Binding("escape", "back", show=False), Binding("space", "mark", show=False)]

    def compose_body(self):
        yield Static(self.app.texts("updates.title"), classes="title")
        yield PagedList(row(self.app.texts("menu.back"), id=BACK), self._row(CHECK), self._row(PRERELEASES),
                        list_id="settings")
        yield Static("", id="update-status", classes="info", markup=False)

    def _row(self, setting):
        on = self.app.user_state.update_check if setting == CHECK else self.app.user_state.prereleases
        return row(f"{'[x]' if on else '[ ]'} {self.app.texts(f'updates.{setting}')}", id=setting)

    def hints(self):
        return HINTS_SETTING if self._highlighted() in (CHECK, PRERELEASES) else HINTS_MENU

    def _highlighted(self):
        for options in self.query("#settings").results(OptionList):
            if options.highlighted is not None:
                return options.get_option_at_index(options.highlighted).id
        return None

    def say_the_status(self):
        status = self.app.update_status
        if status == "available":
            text = self.app.texts("updates.available", found=self.app.newer_version[0],
                                  installed=self.app.newer_version[1])
        else:
            text = self.app.texts(f"updates.status.{status}", installed=versions.installed_version("adrpy-tui"),
                                  seconds=updates.DEADLINE)
        # Not query_one: the answer can reach this screen before it is mounted, and on_mount says it then.
        for line in self.query("#update-status").results(Static):
            line.update(text)

    def on_mount(self):
        options = self.query_one("#settings", OptionList)
        options.highlighted = options.get_option_index(CHECK)
        options.focus()
        self.say_the_status()

    def on_option_list_option_highlighted(self, event):
        self.refresh_hints()

    def on_option_list_option_selected(self, event):
        if not on_top(self):
            return
        if event.option.id == BACK:
            self.action_back()
        else:
            self._toggle(event.option.id)

    def action_mark(self):
        if on_top(self) and self._highlighted() in (CHECK, PRERELEASES):
            self._toggle(self._highlighted())

    def _toggle(self, setting):
        state = self.app.user_state
        if setting == CHECK:
            state.set_update_check(not state.update_check)
            self.app.check_for_update()
        else:
            state.set_prereleases(not state.prereleases)
        self.query_one("#settings", OptionList).replace_option_prompt(setting, self._row(setting).prompt)
        self.say_the_status()

    def action_back(self):
        self.app.pop_screen()
