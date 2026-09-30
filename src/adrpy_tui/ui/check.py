"""`check`: runs as the screen opens, and again when it comes back to the
top; shows that the repository is consistent, or every inconsistency with
adrpy's repair hint."""

from textual.binding import Binding
from textual.widgets import LoadingIndicator, Static

from adrpy_tui.ui.base import HINTS_LIST, AdrpyScreen
from adrpy_tui.ui.errors import ErrorList
from adrpy_tui.ui.preview import PREVIEW_BINDING, open_preview
from adrpy_tui.ui.result import result_widgets


class CheckScreen(AdrpyScreen):
    HINTS = HINTS_LIST
    BINDINGS = [Binding("escape", "back", show=False), PREVIEW_BINDING]

    def __init__(self):
        super().__init__("check")

    def compose_body(self):
        yield LoadingIndicator()

    def on_screen_resume(self):
        # Also sent when the screen first opens. Whether a left write runs is
        # asked as the read begins: one that ends while check reads may have
        # left the repository half-written in what check saw.
        self._writing = self.app.client.still_writing()
        self.read(lambda app: app.client.run("check", ("--path", str(app.repo))), self._show)

    async def _show(self, result):
        if not self.is_attached:
            return
        body = self.query_one("#body")
        await body.remove_children()
        count = result.data.get("decisions", 0)
        if self._writing or self.app.client.still_writing():  # ADR0006V02R02: may be half-written
            await body.mount(Static(self.app.texts("check.write_still_running"), id="write-still-running",
                                    classes="warning", markup=False))
        await body.mount_all(result_widgets(self.app.texts, result, self.app.texts("check.ok", count=count)))
        self.focus_first()

    def action_preview(self):
        for errors in self.query(ErrorList).results(ErrorList):
            open_preview(self.app, errors.highlighted_path())

    def action_back(self):
        self.app.pop_screen()
