"""`check`: runs as the screen opens, and again when it comes back to the
top; shows that the repository is consistent, or every inconsistency with
adrpy's repair hint."""

from pathlib import Path

from textual.binding import Binding
from textual.widgets import Button, LoadingIndicator, Static

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
            left = self._writing or self.app.client.still_writing()
            title = "check.edited_open" if left else "check.edited"
            await body.mount(Static(texts(title, file=name), id="edited", classes="title", markup=False))
            next_step = self._next_step(result)
            if next_step:
                await body.mount(Static(texts(next_step), id="next-step", classes="info", markup=False))
            if next_step == "check.edited_repair":
                # Its broken header makes it no longer Proposed: its detail offers no Edit (ADR0007V01, item 4).
                await body.mount(Button(texts("check.edit_again"), id="edit-again", action="screen.edit_again"))
        await body.mount_all(result_widgets(self.app.texts, result, self.app.texts("check.ok", count=count)))
        self.refresh_hints()
        self.focus_first()

    def action_preview(self):
        for errors in self.query(ErrorList).results(ErrorList):
            open_preview(self.app, errors.highlighted_path())

    def _next_step(self, result):
        """What comes after an edit: with the editor left open, nothing is
        approved or edited until it closes; a check that could not run lists
        nothing to repair."""
        if self._writing or self.app.client.still_writing():
            return "check.edited_left"
        if result.success:
            return "check.edited_next"
        return "check.edited_repair" if result.data.get("errors") else None

    def action_edit_again(self):
        from adrpy_tui.ui.editing import edit_decision  # editing imports this module

        app, path = self.app, str(self._edited)
        # Not awaited: this screen's own action would wait for its own removal.
        app.pop_screen()
        app.call_later(edit_decision, app, path)

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

