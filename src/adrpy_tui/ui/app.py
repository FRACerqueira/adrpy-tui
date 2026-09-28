"""The Textual app: the repository, the client, the language and the
navigation between screens."""

from pathlib import Path

from textual.app import App

from adrpy_tui.core import i18n
from adrpy_tui.core.client import Client
from adrpy_tui.core.state import UserState, default_state_path
from adrpy_tui.ui.form import FormScreen
from adrpy_tui.ui.help import HelpScreen
from adrpy_tui.ui.language import LanguageScreen
from adrpy_tui.ui.menu import MenuScreen
from adrpy_tui.ui.startup import StartupScreen


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

    def on_mount(self):
        if self.user_state.language in i18n.LANGUAGES:
            self.push_screen(StartupScreen())
        else:
            self.push_screen(LanguageScreen(first_run=True))

    def choose_language(self, language):
        self.user_state.set_language(language)
        self.texts = i18n.load(language)
        self.call_later(self._restart)

    async def _restart(self):
        """Rebuilds every screen, so all of them speak the new language."""
        while len(self.screen_stack) > 1:
            await self.pop_screen()
        await self.push_screen(StartupScreen())

    def repository_read(self, result):
        self.configured = result.success
        self.repo_problem = None if result.success or result.code == "config-not-found" else result
        self.switch_screen(MenuScreen())

    def open_item(self, item):
        if item.id == "exit":
            self.exit()
        elif item.id == "language":
            self.push_screen(LanguageScreen(first_run=False))
        elif item.submenu:
            self.push_screen(MenuScreen(item))
        elif item.shows_help:
            self.push_screen(HelpScreen(item.command))
        else:
            self.push_screen(FormScreen(item.command))
