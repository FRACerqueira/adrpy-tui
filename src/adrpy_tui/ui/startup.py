"""Reads the repository's configuration once the language is known, then
opens the main menu."""

from textual.widgets import LoadingIndicator, Static

from adrpy_tui.ui.base import AdrpyScreen


class StartupScreen(AdrpyScreen):
    def compose_body(self):
        yield Static(self.app.texts("startup.loading"), classes="info")
        yield LoadingIndicator()

    def on_mount(self):
        # The app's worker: the main menu replaces this screen when it ends.
        self.app.run_worker(self._read_config, thread=True)

    def _read_config(self):
        result = self.app.client.run("config", ("--path", str(self.app.repo)))
        self.app.call_from_thread(self.app.repository_read, result)
