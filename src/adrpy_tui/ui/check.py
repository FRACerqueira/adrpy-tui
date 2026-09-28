"""`check`: runs as the screen opens, and again when it comes back to the
top; shows that the repository is consistent, or every inconsistency with
adrpy's repair hint."""

from textual.binding import Binding
from textual.widgets import LoadingIndicator

from adrpy_tui.ui.base import AdrpyScreen
from adrpy_tui.ui.result import result_widgets


class CheckScreen(AdrpyScreen):
    BINDINGS = [Binding("escape", "back", show=False)]

    def __init__(self):
        super().__init__("check")

    def compose_body(self):
        yield LoadingIndicator()

    def on_screen_resume(self):
        # Also sent when the screen first opens.
        self.run_worker(self._run, thread=True)

    def _run(self):
        result = self.app.client.run("check", ("--path", str(self.app.repo)))
        self.app.call_from_thread(self._show, result)

    async def _show(self, result):
        if not self.is_attached:
            return
        body = self.query_one("#body")
        await body.remove_children()
        count = result.data.get("decisions", 0)
        await body.mount_all(result_widgets(self.app.texts, result, self.app.texts("check.ok", count=count)))

    def action_back(self):
        self.app.pop_screen()
