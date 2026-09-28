"""What a command returned: its data and warnings, or its failure with
adrpy's own explanation, shown as adrpy sent it (ADR005V01)."""

import json

from textual.binding import Binding
from textual.widgets import DataTable, Static

from adrpy_tui.ui.base import AdrpyScreen


def _text(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


class ResultScreen(AdrpyScreen):
    BINDINGS = [Binding("escape", "back", show=False)]

    def __init__(self, command, result):
        super().__init__(command, finished=True)
        self.result = result

    def compose_body(self):
        texts, result = self.app.texts, self.result
        if result.success:
            yield Static(texts("result.success"), classes="result title")
            for key, value in result.data.items():
                if key != "warnings":
                    yield Static(f"{key}: {_text(value)}", classes="result", markup=False)
        else:
            yield Static(texts("result.failure", code=result.code), classes="error title", markup=False)
            if result.detail:
                yield Static(result.detail, classes="error", markup=False)
            errors = result.data.get("errors")
            if isinstance(errors, list) and errors and all(isinstance(error, dict) for error in errors):
                yield DataTable(id="errors")
        if result.warnings:
            yield Static(texts("result.warnings"), classes="warning title")
            for warning in result.warnings:
                yield Static(_text(warning), classes="warning", markup=False)

    def on_mount(self):
        for table in self.query("#errors").results(DataTable):
            errors = self.result.data["errors"]
            columns = list(dict.fromkeys(key for error in errors for key in error))
            table.add_columns(*columns)
            for error in errors:
                table.add_row(*(_text(error.get(column, "")) for column in columns))

    def action_back(self):
        self.app.pop_screen()
