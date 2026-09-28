"""The language choice: the first screen of the first run, and the main
menu's "Language" item (ADR005V01)."""

from textual.binding import Binding
from textual.widgets import OptionList, Static

from adrpy_tui.core import i18n
from adrpy_tui.ui.base import HINTS_MAIN, HINTS_MENU, AdrpyScreen
from adrpy_tui.ui.menu import BACK
from adrpy_tui.ui.paged import PagedList, row


class LanguageScreen(AdrpyScreen):
    BINDINGS = [Binding("escape", "back", show=False)]

    def __init__(self, first_run):
        super().__init__()
        self._first_run = first_run
        self.HINTS = HINTS_MAIN if first_run else HINTS_MENU

    def compose_body(self):
        texts = self.app.texts
        yield Static(texts("language.title"), classes="title")
        # On the first run there is no menu yet to go back to.
        back = [] if self._first_run else [row(texts("menu.back"), id=BACK)]
        yield PagedList(
            *back, *(row(i18n.load(code)("language.name"), id=code) for code in i18n.LANGUAGES), list_id="languages"
        )

    def on_mount(self):
        options = self.query_one("#languages", OptionList)
        options.highlighted = options.get_option_index(self.app.texts.language)
        options.focus()

    def on_option_list_option_selected(self, event):
        if event.option.id == BACK:
            self.action_back()
        else:
            self.app.choose_language(event.option.id)

    def action_back(self):
        if self._first_run:
            self.app.exit()
        else:
            self.app.pop_screen()
