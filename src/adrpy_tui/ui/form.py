"""A command's form: one editor per field, checked before running, then the
confirmation, the command and its result."""

import re
from datetime import date

from textual.binding import Binding
from textual.suggester import Suggester
from textual.widgets import Button, Input, Label, MaskedInput, Static, Switch

from adrpy_tui.core.client import display_command
from adrpy_tui.core.fields import build_flags, problem
from adrpy_tui.core.registry import FORMS
from adrpy_tui.core.suggest import prefix_suggestion, similar
from adrpy_tui.ui.base import AdrpyScreen
from adrpy_tui.ui.confirm import ConfirmScreen
from adrpy_tui.ui.result import ResultScreen

_SIMILAR_SHOWN = 8


class RepositorySuggester(Suggester):
    """Continues what was typed with a value the repository already uses."""

    def __init__(self):
        super().__init__(use_cache=False, case_sensitive=True)
        self.candidates = []

    async def get_suggestion(self, value):
        return prefix_suggestion(value, self.candidates)


class FormScreen(AdrpyScreen):
    HINTS = "hints.form"
    BINDINGS = [Binding("escape", "back", show=False), Binding("ctrl+r", "run", show=False)]

    def __init__(self, command):
        super().__init__(command)
        self.form = FORMS[command]
        self._candidates = {}
        # Set once the command starts: the result replaces this screen when
        # it ends, so nothing may leave it or start the command again
        # meanwhile (`loading` does not stop key bindings).
        self._command_running = False

    def compose_body(self):
        texts = self.app.texts
        yield Static(texts(f"form.{self.command}"), classes="title")
        for field in self.form.FIELDS:
            yield Label(texts(f"field.{field.flag}") + (" *" if field.required else ""))
            yield self._editor(field)
            if field.suggest_from:
                yield Static("", id=f"similar-{field.flag}", classes="info", markup=False)
            yield Static("", id=f"problem-{field.flag}", classes="error", markup=False)
        yield Button(texts("form.run"), id="run", variant="primary")

    def _editor(self, field):
        widget_id = f"field-{field.flag}"
        if field.kind == "date":
            return MaskedInput(template="9999-99-99", value=date.today().isoformat(), id=widget_id)
        if field.kind == "switch":
            return Switch(id=widget_id)
        restrict = f"[^{re.escape(field.forbidden)}]*" if field.forbidden else None
        suggester = RepositorySuggester() if field.suggest_from else None
        return Input(id=widget_id, restrict=restrict, suggester=suggester)

    def on_mount(self):
        if any(field.suggest_from for field in self.form.FIELDS):
            self.run_worker(self._read_existing_values, thread=True)

    def _read_existing_values(self):
        result = self.app.client.run("explore", ("--path", str(self.app.repo)))
        if not result.success:
            return
        headers = [decision.get("header") or {} for decision in result.data.get("decisions", [])]
        values = {
            field.flag: sorted({header[field.suggest_from] for header in headers if header.get(field.suggest_from)})
            for field in self.form.FIELDS
            if field.suggest_from
        }
        self.app.call_from_thread(self._set_candidates, values)

    def _set_candidates(self, values):
        if not self.is_attached:  # the person left the form meanwhile
            return
        self._candidates = values
        for flag, candidates in values.items():
            editor = self.query_one(f"#field-{flag}", Input)
            editor.suggester.candidates = candidates
            self._show_similar(flag, editor.value)

    def on_input_changed(self, event):
        flag = event.input.id.removeprefix("field-")
        self.query_one(f"#problem-{flag}", Static).update("")
        if flag in self._candidates:
            self._show_similar(flag, event.value)

    def _show_similar(self, flag, value):
        found = similar(value, self._candidates[flag])[:_SIMILAR_SHOWN]
        text = self.app.texts("form.similar", values=", ".join(found)) if found else ""
        self.query_one(f"#similar-{flag}", Static).update(text)

    def on_button_pressed(self, event):
        if event.button.id == "run":
            self.action_run()

    def action_run(self):
        if self._command_running:
            return
        values = {field.flag: self.query_one(f"#field-{field.flag}").value for field in self.form.FIELDS}
        first_problem = None
        for field in self.form.FIELDS:
            found = problem(field, values[field.flag])
            if found:
                key, params = found
                self.query_one(f"#problem-{field.flag}", Static).update(self.app.texts(key, **params))
                first_problem = first_problem or field
        if first_problem:
            self.query_one(f"#field-{first_problem.flag}").focus()
            return
        flags = build_flags(self.form, self.app.repo, values)
        self.app.push_screen(ConfirmScreen(display_command(self.command, flags)), lambda yes: self._confirmed(yes, flags))

    def _confirmed(self, yes, flags):
        if yes and not self._command_running:
            self._command_running = True
            self.query_one("#body").loading = True
            # The app's worker, not this screen's: switching to the result
            # removes this screen, which would cancel a worker it owns.
            self.app.run_worker(lambda: self._execute(flags), thread=True)

    def _execute(self, flags):
        result = self.app.client.run(self.command, flags)
        self.app.call_from_thread(self.app.switch_screen, ResultScreen(self.command, result))

    def action_back(self):
        if not self._command_running:
            self.app.pop_screen()
