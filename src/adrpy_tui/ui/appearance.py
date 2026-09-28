"""The appearance presets: highlighting one previews it, Enter keeps it,
Back or Esc restores the saved one."""

from textual.binding import Binding
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from adrpy_tui.core import themes
from adrpy_tui.ui.base import AdrpyScreen
from adrpy_tui.ui.menu import BACK


class AppearanceScreen(AdrpyScreen):
    HINTS = "hints.menu"
    BINDINGS = [Binding("escape", "back", show=False)]

    def compose_body(self):
        texts = self.app.texts
        yield Static(texts("appearance.title"), classes="title")
        yield OptionList(
            Option(texts("menu.back"), id=BACK),
            *(Option(texts(f"appearance.preset.{preset}"), id=preset) for preset in themes.PRESETS),
            id="presets",
        )

    def on_mount(self):
        options = self.query_one("#presets", OptionList)
        options.highlighted = options.get_option_index(self.app.preset)
        options.focus()

    def on_option_list_option_highlighted(self, event):
        if event.option.id != BACK:
            self.app.apply_preset(event.option.id)

    def on_option_list_option_selected(self, event):
        if event.option.id == BACK:
            self.action_back()
        else:
            self.app.choose_preset(event.option.id)
            self.app.pop_screen()

    def action_back(self):
        self.app.apply_preset(self.app.preset)
        self.app.pop_screen()
