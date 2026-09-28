"""`adrpy-skills list`: every skill of every provider, in the project and
(claude) the user's home, with whether it is installed or changed by hand."""

from pathlib import PureWindowsPath

from rich.cells import cell_len
from textual.binding import Binding
from textual.widgets import LoadingIndicator, Static

from adrpy_tui.core.text import visible
from adrpy_tui.ui.base import HINTS_BACK, AdrpyScreen
from adrpy_tui.ui.explore import _cells
from adrpy_tui.ui.paged import PagedList, row

_WIDTHS = (20, 12, 10, 12)  # the least each column takes; it grows to its longest text


class SkillsListScreen(AdrpyScreen):
    HINTS = HINTS_BACK
    BINDINGS = [Binding("escape", "back", show=False)]

    def __init__(self):
        super().__init__("skills:list")

    def compose_body(self):
        yield LoadingIndicator()

    def on_screen_resume(self):
        # Also sent when the screen first opens.
        self.read(lambda app: app.client.run("skills:list", ("--path", str(app.repo))), self._show)

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
        rows = [tuple(visible(str(value or "")) for value in (
                    entry["skill"], entry["provider"], entry["scope"], self._state(entry),
                    PureWindowsPath(str(entry.get("file", ""))).as_posix()))
                for entry in result.data.get("skills", [])]
        # Each column as wide as its longest text in this language: a fixed
        # width cut "installed, changed by hand" and most languages' labels.
        widths = tuple(max([least] + [cell_len(cells[i]) + 2 for cells in (header, *rows)])
                       for i, least in enumerate(_WIDTHS)) + (0,)
        await body.mount(Static(_cells(header, widths), classes="info", markup=False))
        await body.mount(PagedList(*(row(_cells(cells, widths), id=str(i)) for i, cells in enumerate(rows)),
                                   list_id="skills"))
        for warning in result.warnings:
            await body.mount(Static(str(warning), classes="warning", markup=False))

    def action_back(self):
        self.app.pop_screen()
