"""The appearance presets: highlighting one previews it, Enter keeps it,
Back or Esc restores the saved one. "Customize colors" sets a role's own
color on top of the preset, shown at once and kept."""

from textual.binding import Binding
from textual.color import Color, ColorParseError
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, OptionList, Static

from adrpy_tui.core import contrast, themes
from adrpy_tui.ui.base import HINTS_MENU, AdrpyScreen, on_top
from adrpy_tui.ui.inputs import SafeInput
from adrpy_tui.ui.menu import BACK
from adrpy_tui.ui.paged import PagedList, row

CUSTOMIZE = "colors"
RESET_ALL = "reset-all"
CHANGED = "•"


class AppearanceScreen(AdrpyScreen):
    HINTS = HINTS_MENU
    BINDINGS = [Binding("escape", "back", show=False)]

    def compose_body(self):
        texts = self.app.texts
        yield Static(texts("appearance.title"), classes="title")
        yield PagedList(
            row(texts("menu.back"), id=BACK),
            *(row(texts(f"appearance.preset.{preset}"), id=preset) for preset in themes.PRESETS),
            row(texts("appearance.customize"), id=CUSTOMIZE),
            list_id="presets",
        )

    def on_mount(self):
        options = self.query_one("#presets", OptionList)
        options.highlighted = options.get_option_index(self.app.preset)
        options.focus()

    def on_option_list_option_highlighted(self, event):
        if event.option.id in themes.PRESETS:
            self.app.apply_preset(event.option.id)

    def on_option_list_option_selected(self, event):
        if not on_top(self):
            return
        if event.option.id == BACK:
            self.action_back()
        elif event.option.id == CUSTOMIZE:
            self.app.apply_preset(self.app.preset)
            self.app.push_screen(ColorsScreen())
        else:
            self.app.choose_preset(event.option.id)
            self.app.pop_screen()

    def action_back(self):
        self.app.apply_preset(self.app.preset)
        self.app.pop_screen()


def _rgb(value):
    return Color.parse(value).rgb


def contrast_of(app, role, value):
    """The contrast a role's color would have: a text role on the screen's
    background; the highlighted item's row (tui-highlight) and its text
    (tui-cursor), each against the other."""
    colors = app.effective_colors()
    if role == "tui-cursor":
        other = colors["tui-highlight"]
    elif role == "tui-highlight":
        other = colors["tui-cursor"]
    else:
        other = app.get_css_variables()["background"]
    return contrast.ratio(_rgb(value), _rgb(other))


class ColorsScreen(AdrpyScreen):
    HINTS = HINTS_MENU
    BINDINGS = [Binding("escape", "back", show=False)]

    def compose_body(self):
        texts = self.app.texts
        yield Static(texts("appearance.customize"), classes="title")
        yield PagedList(row(texts("menu.back"), id=BACK), *(self._option(role) for role in themes.ROLES),
                        row(texts("appearance.reset_all"), id=RESET_ALL), list_id="roles")

    def _option(self, role):
        value = self.app.effective_colors()[role]
        mark = f" {CHANGED}" if role in self.app.custom_colors else ""
        return row(f"{self.app.texts(f'color.role.{role}')}: {value}{mark}", id=role)

    def on_mount(self):
        options = self.query_one("#roles", OptionList)
        options.highlighted = 1
        options.focus()

    def _refresh(self):
        options = self.query_one("#roles", OptionList)
        for role in themes.ROLES:
            options.replace_option_prompt(role, self._option(role).prompt)

    def on_option_list_option_selected(self, event):
        if not on_top(self):
            return
        if event.option.id == BACK:
            self.action_back()
        elif event.option.id == RESET_ALL:
            self.app.reset_colors()
            self._refresh()
        else:
            role = event.option.id
            self.app.push_screen(ColorEditScreen(role), lambda value: self._edited(role, value))

    def _edited(self, role, value):
        if value is None:  # cancelled
            return
        self.app.set_color(role, value or None)  # "" is back to the preset
        self._refresh()

    def action_back(self):
        self.app.pop_screen()


class ColorEditScreen(ModalScreen):
    """One role's color, as #RRGGBB or a CSS name; dismisses the color, ""
    for the preset's, or None."""

    BINDINGS = [Binding("escape", "cancel", show=False)]

    def __init__(self, role):
        super().__init__()
        self._role = role

    def compose(self):
        texts = self.app.texts
        with Vertical(id="dialog"):
            yield Static(texts(f"color.role.{self._role}"), classes="title")
            yield SafeInput(self.app.effective_colors()[self._role], id="color")
            yield Static("", id="color-note", classes="warning", markup=False)
            with Horizontal(id="buttons"):
                yield Button(texts("edit.ok"), id="ok", variant="primary")
                yield Button(texts("color.reset"), id="reset")
                yield Button(texts("edit.cancel"), id="cancel")

    def on_mount(self):
        self.query_one("#color", Input).focus()
        self._check(self.query_one("#color", Input).value)

    def _check(self, value):
        """The note under the color: why it can't be used, or a contrast
        below WCAG AA (a warning, not a refusal: the choice is the
        person's). True when the color can be used."""
        note = self.query_one("#color-note", Static)
        try:
            ratio = contrast_of(self.app, self._role, value)
        except ColorParseError:
            note.update(self.app.texts("color.invalid", value=value))
            return False
        low = ratio < contrast.WCAG_AA
        note.update(self.app.texts("color.low_contrast", ratio=f"{ratio:.2f}") if low else "")
        return True

    def on_input_changed(self, event):
        self._check(event.value)

    def _ok(self):
        value = self.query_one("#color", Input).value.strip()
        if self._check(value):
            self.dismiss(value)

    def on_input_submitted(self, event):
        if not on_top(self):
            return
        self._ok()

    def on_button_pressed(self, event):
        if not on_top(self):
            return
        if event.button.id == "ok":
            self._ok()
        elif event.button.id == "reset":
            self.dismiss("")
        else:
            self.dismiss(None)

    def action_cancel(self):
        self.dismiss(None)
