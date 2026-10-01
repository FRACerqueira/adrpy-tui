"""A command's form: one editor per field, checked before running, then the
confirmation, the command and its result."""

import re
from datetime import date

from textual.binding import Binding
from textual.containers import Vertical
from textual.suggester import Suggester
from textual.widgets import (
    Button, Input, Label, MaskedInput, OptionList, RadioSet, Select, Static, Switch, TextArea,
)

from adrpy_tui.core import i18n, keys
from adrpy_tui.core.decisions import listed
from adrpy_tui.core.fields import build_flags, problem, shown
from adrpy_tui.core.registry import FORMS
from adrpy_tui.core.suggest import prefix_suggestion, similar
from adrpy_tui.core.text import field_text, visible
from adrpy_tui.ui.base import AdrpyScreen, on_top
from adrpy_tui.ui.editing import edit_decision
from adrpy_tui.ui.inputs import SafeInput, SafeTextArea
from adrpy_tui.ui.paged import PAGE_SIZE
from adrpy_tui.ui.picker import AdrPicker
from adrpy_tui.ui.preview import PREVIEW_BINDING, open_preview
from adrpy_tui.ui.running import CommandRunner
from adrpy_tui.ui.toggles import CheckList, ChoiceButton

_SIMILAR_SHOWN = 8


class RepositorySuggester(Suggester):
    """Continues what was typed with a value the repository already uses."""

    def __init__(self):
        super().__init__(use_cache=False, case_sensitive=True)
        self.candidates = []

    async def get_suggestion(self, value):
        return prefix_suggestion(value, self.candidates)


class FormScreen(CommandRunner, AdrpyScreen):
    BINDINGS = [
        Binding("escape", "back", show=False),
        Binding(keys.ACTIONS["run"], "run", id=keys.binding_id("run"), show=False),
        Binding(keys.ACTIONS["toggle"], "toggle_available", id=keys.binding_id("toggle"), show=False),
        PREVIEW_BINDING,
    ]

    def __init__(self, command, decision=None):
        super().__init__(command)
        self._prefilled = {}  # flag -> the value a chosen decision filled in
        self.form = FORMS[command]
        # The path of a decision to choose once the decisions are read.
        self._preselected = decision
        self._candidates = {}

    def hints(self):
        fields = self.form.FIELDS
        hints = [("tab", "next_field")]
        if any(field.suggest_from for field in fields):
            hints.append(("right", "accept_suggestion"))
        if any(field.kind == "decision" for field in fields):
            listed = any(picker.query(OptionList).first().option_count for picker in self.query(AdrPicker))
            hints += [("@preview", "preview")] * listed + [("@toggle", "show_all")]
        if isinstance(self.focused, (CheckList, RadioSet)):
            hints += [("arrows", "move"), ("space", "mark")]
        elif isinstance(self.focused, Switch):
            hints.append(("space", "mark"))
        return (*hints, ("@run", "run"), ("escape", "back"))

    def compose_body(self):
        texts = self.app.texts
        yield Static(texts(f"form.{self.command}"), classes="title")
        if self.command == "init" and self.app.configured:
            yield Static(texts("form.init_configured"), id="form-warning", classes="warning", markup=False)
        for field in self.form.FIELDS:
            with Vertical(id=f"row-{field.flag}", classes="field-row"):
                required = field.required or field.required_if_shown
                yield Label(texts(f"field.{field.flag}") + (" *" if required else ""))
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
        if field.kind == "decision":
            return AdrPicker(field, id=widget_id)
        if field.kind == "choice":
            texts = self.app.texts
            return RadioSet(
                *(ChoiceButton(texts(f"choice.{field.flag}.{choice}"), value=index == 0, id=f"{field.flag}-{choice}")
                  for index, choice in enumerate(field.choices)),
                id=widget_id,
            )
        if field.kind == "language":
            return Select([(i18n.load(code)("language.name"), code) for code in i18n.LANGUAGES],
                          value=self.app.texts.language, allow_blank=False, id=widget_id)
        if field.kind == "select":
            # adrpy's own vocabulary, shown as is (ADR0005V01).
            return Select([(choice, choice) for choice in field.choices], value=field.choices[0],
                          allow_blank=False, id=widget_id)
        if field.kind == "multiline":
            return SafeTextArea(id=widget_id)
        if field.kind == "multi":
            # A short, fixed list of choices: never more than a page
            # (doc/forms.md, "Lists").
            choices = CheckList(*((choice, choice) for choice in field.choices), id=widget_id)
            choices.styles.max_height = PAGE_SIZE + 2
            return choices
        restrict = field.restrict or (f"[^{re.escape(field.forbidden)}]*" if field.forbidden else None)
        suggester = RepositorySuggester() if field.suggest_from else None
        return SafeInput(id=widget_id, restrict=restrict, suggester=suggester)

    def _value(self, field):
        editor = self.query_one(f"#field-{field.flag}")
        if field.kind == "choice":
            pressed = editor.pressed_button
            return pressed.id.removeprefix(f"{field.flag}-") if pressed else field.choices[0]
        if field.kind == "multiline":
            return editor.text
        if field.kind == "multi":
            return ",".join(choice for choice in field.choices if choice in editor.selected)
        return editor.value

    def _values(self):
        return {field.flag: self._value(field) for field in self.form.FIELDS}

    def _show_rows(self):
        """Shows each field only while its condition holds."""
        values = self._values()
        for field in self.form.FIELDS:
            self.query_one(f"#row-{field.flag}").display = shown(field, values) and (
                not field.needs_editor or self.app.editor is not None)

    def on_radio_set_changed(self, event):
        self._show_rows()

    def on_select_changed(self, event):
        self._show_rows()

    def on_mount(self):
        self._show_rows()
        if any(field.suggest_from or field.kind == "decision" for field in self.form.FIELDS):
            self.read(lambda app: app.client.run("explore", ("--path", str(app.repo))), self._decisions_read)

    def _decisions_read(self, result):
        if result.success:
            self._set_decisions(listed(result.data))
        else:
            self._explore_failed(result)

    def _explore_failed(self, result):
        if not self.is_attached:
            return
        for picker in self.query(AdrPicker).results(AdrPicker):
            picker.show_failure(result.detail or result.code)

    def _set_decisions(self, decisions):
        if not self.is_attached:  # the person left the form meanwhile
            return
        headers = [decision.get("header") or {} for decision in decisions]
        self._candidates = {
            # As a field keeps them (ui/inputs.py): a suggestion is drawn in the field.
            field.flag: sorted({field_text(str(header[field.suggest_from])) for header in headers
                                if header.get(field.suggest_from)} - {""})
            for field in self.form.FIELDS
            if field.suggest_from
        }
        for field in self.form.FIELDS:
            if field.kind == "decision":
                picker = self.query_one(f"#field-{field.flag}", AdrPicker)
                picker.set_decisions(decisions, self.app.labels)
                if self._preselected:
                    picker.choose(self._preselected)
        self.refresh_hints()
        for flag, candidates in self._candidates.items():
            editor = self.query_one(f"#field-{flag}", Input)
            editor.suggester.candidates = candidates
            self._show_similar(flag, editor.value)

    def on_adr_picker_chosen(self, event):
        """Shows adrpy's defaults for the chosen decision: copies its
        scope/domain into fields still empty, and its title as a
        placeholder."""
        if not on_top(self):
            return
        header = event.decision.get("header") or {}
        for field in self.form.FIELDS:
            editor = self.query_one(f"#field-{field.flag}")
            # Filled from the previous choice and left as it was: the new one's
            # replaces it; what the person typed stays.
            untouched = not editor.value or editor.value == self._prefilled.get(field.flag)
            if field.prefill_from and untouched:
                editor.value = header.get(field.prefill_from) or ""
                self._prefilled[field.flag] = editor.value
            if field.default_from:
                editor.placeholder = self.app.texts("form.default",
                                                    value=visible(str(event.decision.get(field.default_from) or "")))

    def on_input_changed(self, event):
        flag = event.input.id.removeprefix("field-")
        self.query_one(f"#problem-{flag}", Static).update("")
        if flag in self._candidates:
            self._show_similar(flag, event.value)

    def _show_similar(self, flag, value):
        found = similar(value, self._candidates[flag])[:_SIMILAR_SHOWN]
        text = self.app.texts("form.similar", values=", ".join(visible(value) for value in found)) if found else ""
        self.query_one(f"#similar-{flag}", Static).update(text)

    def on_button_pressed(self, event):
        if not on_top(self):
            return
        if event.button.id == "run":
            self.action_run()

    def action_run(self):
        if self.command_running:
            return
        values = self._values()
        pickers = [self.query_one(f"#field-{field.flag}", AdrPicker) for field in self.form.FIELDS if field.kind == "decision"]
        decision = pickers[0].selected if pickers else None
        first_problem = None
        for field in self.form.FIELDS:
            if not shown(field, values):
                continue
            found = problem(field, values[field.flag], decision)
            if found:
                key, params = found
                self.query_one(f"#problem-{field.flag}", Static).update(self.app.texts(key, **params))
                if first_problem is None:
                    first_problem, first_message = field, self.app.texts(key, **params)
        if first_problem:
            self.query_one(f"#field-{first_problem.flag}").focus()
            # The field's own message can be off screen in a short terminal: this one is always seen.
            self.app.notify(self.app.texts("form.not_run", field=self.app.texts(f"field.{first_problem.flag}"),
                                           problem=first_message), severity="warning", markup=False)
            return
        commands = [(self.command, build_flags(self.form, self.app.repo, values))]
        editor = self.app.editor
        if editor and values.get("edit") and self.query("#row-edit") and self.query_one("#row-edit").display:
            self.confirm_and_run(commands, then=self._edit_created,
                                 also=self.app.texts("editing.then", editor=editor.name))
        else:
            self.confirm_and_run(commands)

    def _edit_created(self, result):
        """The decision the command created, opened in the editor: `created`
        -- for supersede, the successor, not the predecessor."""
        created = result.data.get("created")
        if isinstance(created, str):
            edit_decision(self.app, created)

    def action_toggle_available(self):
        if self.command_running:
            return
        for picker in self.query(AdrPicker).results(AdrPicker):
            picker.toggle_available()
        self.refresh_hints()

    def action_preview(self):
        if self.command_running:
            return
        for picker in self.query(AdrPicker).results(AdrPicker):
            open_preview(self.app, picker.highlighted_path())

    def action_back(self):
        if not self.command_running:
            self.app.pop_screen()
