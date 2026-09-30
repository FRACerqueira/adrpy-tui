"""Reads the repository's configuration once the language is known, then
opens the main menu."""

from textual.binding import Binding
from textual.widgets import LoadingIndicator, Static

from adrpy_tui.ui.base import AdrpyScreen


class StartupScreen(AdrpyScreen):
    HINTS = (("escape", "exit"),)
    BINDINGS = [Binding("escape", "app.quit", show=False)]

    def compose_body(self):
        yield Static(self.app.texts("startup.loading"), classes="info")
        yield LoadingIndicator()

    def on_mount(self):
        # The main menu replaces this screen when it ends; a start-up screen a
        # second restart replaced meanwhile gets nothing.
        self.read(lambda app: app.client.run("config", ("--path", str(app.repo))), self.app.repository_read)
