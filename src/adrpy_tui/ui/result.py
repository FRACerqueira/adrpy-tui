"""What a command returned: its data and warnings, or its failure with
adrpy's own explanation, shown as adrpy sent it (ADR005V01)."""

import json

from textual.binding import Binding
from textual.widgets import Button, Static

from adrpy_tui.core import keys
from adrpy_tui.core.client import ABANDONED
from adrpy_tui.core.registry import FORMS
from adrpy_tui.ui.base import AdrpyScreen
from adrpy_tui.ui.errors import ErrorList
from adrpy_tui.ui.preview import open_preview


def _text(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


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
            yield Static(result.detail, classes="error", markup=False)
        errors = result.data.get("errors")
        if isinstance(errors, list) and errors and all(isinstance(error, dict) for error in errors):
            yield ErrorList(errors)
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
        if self.result.code == ABANDONED:  # the repository's state is unknown: Check says it
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
            open_preview(self.app, path)

    def action_back(self):
        form = FORMS.get(self.command)
        if self.result.success and getattr(form, "RELOADS_REPOSITORY", False):
            # The menus depend on the repository this command just changed.
            self.app.call_later(self.app.reload_repository)
        else:
            self.app.pop_screen()
