"""`check`: runs as the screen opens, and again when it comes back to the
top; shows that the repository is consistent, or every inconsistency with
adrpy's repair hint."""

from pathlib import Path

from textual.binding import Binding
from textual.widgets import LoadingIndicator, Static

from adrpy_tui.core.files import same_path
from adrpy_tui.core.text import visible
from adrpy_tui.ui.base import HINTS_BACK, AdrpyScreen
from adrpy_tui.ui.errors import ErrorList
from adrpy_tui.ui.preview import PREVIEW_BINDING, open_preview
from adrpy_tui.ui.result import ResultScreen, result_widgets

# Enter does nothing on the list of errors: its highlight shows each one.
HINTS_ERRORS = (("arrows", "move"), ("@preview", "preview"), ("escape", "back"))


class CheckScreen(AdrpyScreen):
    BINDINGS = [Binding("escape", "back", show=False), PREVIEW_BINDING]

    def __init__(self, edited=None):
        """`edited`: the decision just closed in the editor (ADR0007V01) --
        said at the top, with what comes next, and Esc goes to its detail."""
        super().__init__("check")
        self._edited = edited

    def hints(self):
        hints = HINTS_ERRORS if self.query(ErrorList) else HINTS_BACK
        if self._edited is not None:
            return (*hints[:-1], ("escape", "back_to_decision"))
        return hints

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
        if self._edited is not None:
            texts, name = self.app.texts, visible(Path(self._edited).name)
            await body.mount(Static(texts("check.edited", file=name), id="edited", classes="title", markup=False))
            await body.mount(Static(texts("check.edited_next" if result.success else "check.edited_repair"),
                                    id="next-step", classes="info", markup=False))
        await body.mount_all(result_widgets(self.app.texts, result, self.app.texts("check.ok", count=count)))
        self.refresh_hints()
        self.focus_first()

    def action_preview(self):
        for errors in self.query(ErrorList).results(ErrorList):
            open_preview(self.app, errors.highlighted_path())

    async def action_back(self):
        app = self.app
        await app.pop_screen()
        if self._edited is None:
            return
        from adrpy_tui.ui.explore import DetailScreen  # explore imports editing, which imports this

        path = str(self._edited)
        below = app.screen
        if isinstance(below, DetailScreen) and same_path(below.decision["path"], path):
            return  # read again as it comes back to the top
        detail = DetailScreen({"path": path, "filename": Path(path).name, "header": {}})
        if isinstance(below, ResultScreen):  # the result of the command that created it: its detail instead
            await app.switch_screen(detail)
        else:
            await app.push_screen(detail)

