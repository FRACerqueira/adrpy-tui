"""What a command returned: its data and warnings, or its failure with
adrpy's own explanation, shown as adrpy sent it (ADR0005V01)."""

import json
from pathlib import Path

from textual.binding import Binding
from textual.widgets import Button, Static

from adrpy_tui.core import keys
from adrpy_tui.core.client import ABANDONED, WRITE_STILL_RUNNING
from adrpy_tui.core.registry import FORMS
from adrpy_tui.core.text import visible
from adrpy_tui.ui.base import AdrpyScreen
from adrpy_tui.ui.errors import ErrorList
from adrpy_tui.ui.preview import open_preview


def _plain(value):
    """A value as a person reads it: a list item by item, a record field by
    field, so a Windows path keeps its single backslashes; JSON below that."""
    if isinstance(value, str):
        return value
    if value and isinstance(value, list) and all(isinstance(item, (str, dict)) for item in value):
        return "; ".join(_plain(item) for item in value)
    if value and isinstance(value, dict) and all(isinstance(item, str) or item is None for item in value.values()):
        return ", ".join(f"{key}: {'null' if item is None else item}" for key, item in value.items())
    return json.dumps(value, ensure_ascii=False)  # an empty list or record reads as [] or {}


def _text(value):
    return visible(_plain(value))


def result_widgets(texts, result, success_text=None):
    """The widgets showing a result; `success_text` replaces the listing of
    a success's data (the check screen's own summary)."""
    if result.success:
        yield Static(success_text or texts("result.success"), classes="result title", markup=False)
        if success_text is None:
            for key, value in result.data.items():
                if key != "warnings":
                    yield Static(f"{key}: {_text(value)}", classes="result", markup=False)
    else:
        yield Static(texts("result.failure", code=result.code), classes="error title", markup=False)
        if result.detail:
            yield Static(visible(result.detail), classes="error", markup=False)
        errors = result.data.get("errors")
        if isinstance(errors, list) and errors and all(isinstance(error, dict) for error in errors):
            yield ErrorList(errors)
        # The rest of `data` is what names the files a failure is about (the detail may give only a count).
        for key, value in result.data.items():
            if key not in ("errors", "warnings"):
                yield Static(f"{key}: {_text(value)}", classes="error", markup=False)
    if result.warnings:
        yield Static(texts("result.warnings"), classes="warning title")
        for warning in result.warnings:
            yield Static(_text(warning), classes="warning", markup=False)


class ResultScreen(AdrpyScreen):
    HINTS = (("@preview", "preview"), ("escape", "back"))
    BINDINGS = [Binding("escape", "back", show=False),
                Binding(keys.ACTIONS["preview"], "preview", id=keys.binding_id("preview"), show=False)]

    def __init__(self, command, result):
        super().__init__(command, finished=True)
        self.result = result

    def compose_body(self):
        yield from result_widgets(self.app.texts, self.result)
        if self.result.code in (ABANDONED, WRITE_STILL_RUNNING):  # the repository's state is unknown: Check says it
            yield Button(self.app.texts("result.run_check"), id="run-check", variant="primary",
                         action="screen.run_check")

    def action_run_check(self):
        from adrpy_tui.ui.check import CheckScreen  # check.py shows results through this module

        self.app.push_screen(CheckScreen())

    def action_preview(self):
        """The file the command wrote (created, file), else the highlighted
        error's."""
        written = self.result.data.get("created") or self.result.data.get("file")
        errors = list(self.query(ErrorList).results(ErrorList))
        path = errors[0].highlighted_path() if errors else written
        if isinstance(path, str):
            open_preview(self.app, self._where(path))

    def _where(self, path):
        """A log code names a file by its path in the log folder; another code
        by its name only in the decisions folder, else by a path in the
        repository. Decided without touching the disk: open_preview's guard
        is the first to look."""
        if Path(path).is_absolute():
            return path
        if str(self.result.code or "").startswith("log-"):
            return str(self.app.repo / self.app.folderlog / path)
        if len(Path(path).parts) > 1:
            return str(self.app.repo / path)
        return str(self.app.repo / self.app.folderadr / path)

    def action_back(self):
        form = FORMS.get(self.command)
        if self.result.success and getattr(form, "RELOADS_REPOSITORY", False):
            # The menus depend on the repository this command just changed.
            self.app.call_later(self.app.reload_repository)
        else:
            self.app.pop_screen()
