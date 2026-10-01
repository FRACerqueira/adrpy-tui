"""The editor a Proposed decision opens in, chosen in the main menu's
"Editor" item (ADR0007V01): None, the default, or one of the list found on
this system's PATH."""

from textual.binding import Binding
from textual.widgets import OptionList, Static

from adrpy_tui.core import editors
from adrpy_tui.ui.base import HINTS_MENU, AdrpyScreen, on_top
from adrpy_tui.ui.menu import BACK
from adrpy_tui.ui.paged import PagedList, row

NONE = "none"


class EditorScreen(AdrpyScreen):
    HINTS = HINTS_MENU
    BINDINGS = [Binding("escape", "back", show=False)]

    def compose_body(self):
        texts = self.app.texts
        yield Static(texts("editor.title"), classes="title")
        choices = [row(texts("menu.back"), id=BACK), row(texts("editor.none"), id=NONE)]
        for editor in editors.EDITORS:
            if editors.located(editor):
                choices.append(row(editor.name, id=editor.name))
            else:
                # Said in words, not only drawn quieter.
                choices.append(row(texts("editor.missing", name=editor.name), id=editor.name, disabled=True))
        yield PagedList(*choices, list_id="editors")

    def on_mount(self):
        options = self.query_one("#editors", OptionList)
        chosen = self.app.editor
        options.highlighted = options.get_option_index(chosen.name if chosen else NONE)
        options.focus()

    def on_option_list_option_selected(self, event):
        if not on_top(self):
            return
        if event.option.id != BACK:
            self.app.choose_editor(None if event.option.id == NONE else event.option.id)
        self.action_back()

    def action_back(self):
        self.app.pop_screen()
