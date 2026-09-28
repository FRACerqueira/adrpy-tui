"""`adrpy-skills list`: every skill of every provider, in the project and
(claude) the user's home, with whether it is installed or changed by hand."""

from pathlib import PureWindowsPath

from textual.binding import Binding
from textual.widgets import LoadingIndicator, Static

from adrpy_tui.ui.base import HINTS_BACK, AdrpyScreen
from adrpy_tui.ui.explore import _cells
from adrpy_tui.ui.paged import PagedList, row

_WIDTHS = (20, 12, 10, 26)


class SkillsListScreen(AdrpyScreen):
    HINTS = HINTS_BACK
    BINDINGS = [Binding("escape", "back", show=False)]

    def __init__(self):
        super().__init__("skills:list")

    def compose_body(self):
        yield LoadingIndicator()

    def on_screen_resume(self):
        # Also sent when the screen first opens.
        self.run_worker(self._read, thread=True)

    def _read(self):
        result = self.app.client.run("skills:list", ("--path", str(self.app.repo)))
        self.app.call_from_thread(self._show, result)

    def _state(self, entry):
        if not entry.get("installed"):
            return self.app.texts("skills.state.missing")
        return self.app.texts("skills.state.drifted" if entry.get("drifted") else "skills.state.installed")

    async def _show(self, result):
        if not self.is_attached:
            return
        try:
            await self._mount_rows(result)
        finally:
            self.focus_first()

    async def _mount_rows(self, result):
        texts, body = self.app.texts, self.query_one("#body")
        await body.remove_children()
        if not result.success:
            await body.mount(Static(result.detail or result.code or "", classes="error", markup=False))
            return
        header = [texts(f"skills.column.{name}") for name in ("skill", "provider", "scope", "state", "file")]
        await body.mount(Static(_cells(header, _WIDTHS + (0,)), classes="info", markup=False))
        rows = result.data.get("skills", [])
        await body.mount(PagedList(
            *(row(_cells((entry["skill"], entry["provider"], entry["scope"], self._state(entry),
                             PureWindowsPath(str(entry.get("file", ""))).as_posix()), _WIDTHS + (0,)), id=str(i))
              for i, entry in enumerate(rows)),
            list_id="skills",
        ))
        for warning in result.warnings:
            await body.mount(Static(str(warning), classes="warning", markup=False))

    def action_back(self):
        self.app.pop_screen()
