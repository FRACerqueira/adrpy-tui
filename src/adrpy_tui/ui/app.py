"""The Textual app: the repository, the client, the language and the
navigation between screens."""

from dataclasses import replace
from pathlib import Path

from textual.app import App
from textual.color import Color, ColorParseError

from adrpy_tui.core import decisions, i18n, themes
from adrpy_tui.core.client import Client
from adrpy_tui.core.registry import FORMS
from adrpy_tui.core.state import UserState, default_state_path
from adrpy_tui.ui.appearance import AppearanceScreen
from adrpy_tui.ui.check import CheckScreen
from adrpy_tui.ui.config import ConfigScreen
from adrpy_tui.ui.explore import ExploreScreen
from adrpy_tui.ui.form import FormScreen
from adrpy_tui.ui.help import HelpScreen
from adrpy_tui.ui.language import LanguageScreen
from adrpy_tui.ui.menu import MenuScreen
from adrpy_tui.ui.migrate import MigrateScreen
from adrpy_tui.ui.repository import RepositoryScreen
from adrpy_tui.ui.skills import SkillsListScreen
from adrpy_tui.ui.startup import StartupScreen


def _is_color(value):
    try:
        Color.parse(value)
    except ColorParseError:
        return False
    return True


class AdrpyTui(App):
    CSS_PATH = Path(__file__).parent.parent / "resources" / "app.tcss"
    TITLE = "adrpy-tui"

    def __init__(self, repo, client=None, user_state=None):
        super().__init__()
        self.repo = Path(repo).resolve()
        self.client = client or Client()
        self.user_state = user_state or UserState(default_state_path())
        stored = self.user_state.language
        self.texts = i18n.load(stored if stored in i18n.LANGUAGES else i18n.system_language())
        self.configured = False
        # A failed read of the repository's config other than "there is
        # none", shown on the main menu.
        self.repo_problem = None
        # Each decision state's label in this repository, for display.
        self.labels = decisions.labels({})
        self._themes_built = 0
        # The customized colors this app can read; the others are ignored
        # and named on the main menu.
        self.custom_colors, self.ignored_colors = {}, []
        for role, value in self.user_state.colors.items():
            if role in themes.ROLES and _is_color(value):
                self.custom_colors[role] = value
            else:
                self.ignored_colors.append(role)
        self.preset = themes.preset_or_default(self.user_state.appearance)
        self.apply_preset(self.preset)

    def _theme(self, preset):
        """A theme of `preset` with the customized colors on top."""
        spec = themes.PRESETS[preset]
        base = self.get_theme(spec["base"])
        colors = {**spec["colors"], **self.custom_colors}
        # The cursor of menus and tables draws the highlight role on the
        # cursor role, never on the theme's own cursor color.
        cursor = {
            "block-cursor-foreground": colors["tui-highlight"],
            "block-cursor-background": colors["tui-cursor"],
            "block-cursor-blurred-foreground": colors["tui-highlight"],
            "block-cursor-blurred-background": colors["tui-cursor"],
        }
        # A new name each time: setting the app's theme to the name it already
        # has would not repaint it.
        self._themes_built += 1
        name = f"{themes.theme_name(preset)}-{self._themes_built}"
        self.register_theme(replace(base, name=name, primary=spec.get("primary", base.primary),
                                    variables={**base.variables, **colors, **cursor}))
        return name

    def set_color(self, role, color):
        """Keeps a role's own color (None: the preset's) and shows it."""
        if color is None:
            self.custom_colors.pop(role, None)
        else:
            self.custom_colors[role] = color
        self.user_state.set_color(role, color)
        self.apply_preset(self.preset)

    def reset_colors(self):
        self.custom_colors = {}
        self.user_state.reset_colors()
        self.apply_preset(self.preset)

    def effective_colors(self):
        return {**themes.PRESETS[self.preset]["colors"], **self.custom_colors}

    def get_theme_variable_defaults(self):
        # Read while the stylesheet is parsed, before any theme applies.
        return dict(themes.PRESETS[themes.DEFAULT_PRESET]["colors"])

    def apply_preset(self, preset):
        """Shows a preset without saving it (a preview)."""
        self.theme = self._theme(preset)

    def choose_preset(self, preset):
        self.preset = preset
        self.user_state.set_appearance(preset)
        self.apply_preset(preset)

    def on_mount(self):
        if self.user_state.language in i18n.LANGUAGES:
            self.push_screen(StartupScreen())
        else:
            self.push_screen(LanguageScreen(first_run=True))

    def choose_language(self, language):
        self.user_state.set_language(language)
        self.texts = i18n.load(language)
        self.call_later(self._restart)

    def use_repository(self, path):
        """Works on another repository from now on: reads it and rebuilds
        every screen."""
        self.repo = Path(path).resolve()
        self.call_later(self._restart)

    async def reload_repository(self):
        """Reads the repository again and rebuilds every screen from the
        main menu (after init, config or migrate)."""
        await self._restart()

    async def _restart(self):
        """Rebuilds every screen, so all of them speak the new language."""
        while len(self.screen_stack) > 1:
            await self.pop_screen()
        await self.push_screen(StartupScreen())

    def repository_read(self, result):
        self.configured = result.success
        self.labels = decisions.labels(result.data.get("config") or {})
        self.repo_problem = None if result.success or result.code == "config-not-found" else result
        self.switch_screen(MenuScreen())

    def open_item(self, item):
        if item.id == "exit":
            self.exit()
        elif item.id == "language":
            self.push_screen(LanguageScreen(first_run=False))
        elif item.id == "appearance":
            self.push_screen(AppearanceScreen())
        elif item.id == "change-repository":
            self.push_screen(RepositoryScreen())
        elif item.submenu:
            self.push_screen(MenuScreen(item))
        elif item.shows_help:
            self.push_screen(HelpScreen(item.command))
        elif getattr(FORMS[item.command], "VIEW", None) == "explore":
            self.push_screen(ExploreScreen())
        elif getattr(FORMS[item.command], "VIEW", None) == "check":
            self.push_screen(CheckScreen())
        elif getattr(FORMS[item.command], "VIEW", None) in ("config", "installconfig"):
            self.push_screen(ConfigScreen(item.command))
        elif getattr(FORMS[item.command], "VIEW", None) == "migrate":
            self.push_screen(MigrateScreen())
        elif getattr(FORMS[item.command], "VIEW", None) == "skills-list":
            self.push_screen(SkillsListScreen())
        else:
            self.push_screen(FormScreen(item.command))
