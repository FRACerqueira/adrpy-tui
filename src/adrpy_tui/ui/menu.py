"""A menu: the main one or a group's, each item with its description below.

An item that can't be used here is shown disabled, with the reason next to
its title.
"""

from textual.binding import Binding
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option, OptionDoesNotExist

from adrpy_tui.core.registry import FORMS, MAIN_MENU, command_name
from adrpy_tui.ui.base import AdrpyScreen

# Items that open no form but are available.
_ACTIONS = ("language", "exit")
# The first option of every submenu: back to the menu it was opened from.
BACK = "back"


class MenuScreen(AdrpyScreen):
    BINDINGS = [Binding("escape", "back", show=False)]

    def __init__(self, menu=MAIN_MENU):
        super().__init__()
        self.menu = menu
        self.HINTS = "hints.main" if menu is MAIN_MENU else "hints.menu"

    def compose_body(self):
        texts = self.app.texts
        yield Static(texts("menu.main" if self.menu is MAIN_MENU else f"menu.{self.menu.id}"), classes="title")
        problem = self.app.repo_problem
        if self.menu is MAIN_MENU and problem is not None:
            yield Static(texts("menu.repo_problem", detail=problem.detail or problem.code), classes="error", markup=False)
        back = [] if self.menu is MAIN_MENU else [Option(texts("menu.back"), id=BACK)]
        yield OptionList(*back, *(self._option(item) for item in self.menu.submenu), id="options")
        yield Static("", id="description", classes="info", markup=False)

    def _option(self, item):
        reason = self._unavailable(item)
        title = self._title(item)
        if reason:
            title = f"{title}  ({self.app.texts(reason)})"
        return Option(title, id=item.id, disabled=reason is not None)

    def _title(self, item):
        return command_name(item.command) if item.shows_help else self.app.texts(f"menu.{item.id}")

    def _description(self, item):
        if item.shows_help:
            return self.app.texts("menu.help.item", name=command_name(item.command))
        return self.app.texts(f"menu.{item.id}.description")

    def _unavailable(self, item):
        """The language-pack key of why an item can't be used, or None."""
        if item.needs_repo and not self.app.configured:
            return "menu.unavailable.repo"
        if item.submenu or item.shows_help or item.id in _ACTIONS or item.command in FORMS:
            return None
        return "menu.unavailable.pending"

    def on_mount(self):
        options = self.query_one("#options", OptionList)
        options.highlighted = self._initial_index(options)
        options.focus()

    def _initial_index(self, options):
        """The remembered item when it is still there and usable, else the
        first usable item other than Back, else Back."""
        enabled = [i for i in range(options.option_count) if not options.get_option_at_index(i).disabled]
        remembered = self.app.user_state.last(self.menu.id)
        if remembered:
            try:
                index = options.get_option_index(remembered)
            except OptionDoesNotExist:  # an item of an older version
                index = None
            if index in enabled:
                return index
        return next((i for i in enabled if options.get_option_at_index(i).id != BACK), 0)

    def on_option_list_option_highlighted(self, event):
        if event.option.id == BACK:
            description = self.app.texts("menu.back.description")
        else:
            description = self._description(self._item(event.option.id))
        self.query_one("#description", Static).update(description)

    def on_option_list_option_selected(self, event):
        if event.option.id == BACK:
            self.action_back()
            return
        item = self._item(event.option.id)
        self.app.user_state.remember(self.menu.id, item.id)
        self.app.open_item(item)

    def _item(self, item_id):
        return next(item for item in self.menu.submenu if item.id == item_id)

    def action_back(self):
        if self.menu is MAIN_MENU:
            self.app.exit()
        else:
            self.app.pop_screen()
