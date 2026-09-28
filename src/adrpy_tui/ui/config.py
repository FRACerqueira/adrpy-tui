"""The editor of a config: the repository's (`config`) or the per-user
install-level one (`installconfig`). The fields in groups with their
current value; `Enter` edits one, and saving runs one command with only the
fields that changed. An install-level config that does not exist yet is
created first, from a language pack or a config file."""

from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, LoadingIndicator, RadioButton, RadioSet, Select, Static, Switch, TextArea

from adrpy_tui.core import i18n, keys
from adrpy_tui.core.config_fields import CONFIG_FIELDS, GROUPS
from adrpy_tui.ui.base import AdrpyScreen
from adrpy_tui.ui.confirm import ConfirmScreen
from adrpy_tui.ui.paged import PagedList, row
from adrpy_tui.ui.running import CommandRunner

CHANGED = "•"


def shown_value(field, value):
    """A value as one line of the list."""
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value)
    first = text.strip().splitlines()[0] if text.strip() else ""
    return first + " …" if "\n" in text.strip() or len(first) > 60 else first


def as_flag_value(field, value):
    if field.kind == "bool":
        return "true" if value in (True, "true") else "false"
    return str(value)


class FieldEditScreen(ModalScreen):
    """Edits one field with the editor of its type; dismisses the new value,
    or None."""

    BINDINGS = [Binding("escape", "cancel", show=False)]

    def __init__(self, field, value, description):
        super().__init__()
        self._field = field
        self._value = value
        self._description = description

    def compose(self):
        texts, field, value = self.app.texts, self._field, self._value
        with Vertical(id="dialog"):
            yield Static(texts(f"config.field.{field.flag}"), classes="title")
            yield Static(self._description, classes="info", markup=False)
            if field.kind == "select":
                yield Select([(choice, choice) for choice in field.choices], value=str(value) if str(value) in
                             field.choices else field.choices[0], allow_blank=False, id="editor")
            elif field.kind == "bool":
                yield Switch(value=value in (True, "true"), id="editor")
            elif field.kind == "multiline":
                yield TextArea(str(value or ""), id="editor")
            else:
                yield Input(str(value or ""), max_length=field.max_length or 0, id="editor")
            with Horizontal(id="buttons"):
                yield Button(texts("edit.ok"), id="ok", variant="primary")
                yield Button(texts("edit.cancel"), id="cancel")

    def on_mount(self):
        self.query_one("#editor").focus()

    def _current(self):
        editor = self.query_one("#editor")
        return editor.text if isinstance(editor, TextArea) else editor.value

    def on_input_submitted(self, event):
        self.dismiss(self._current())

    def on_button_pressed(self, event):
        self.dismiss(self._current() if event.button.id == "ok" else None)

    def action_cancel(self):
        self.dismiss(None)


class ConfigScreen(CommandRunner, AdrpyScreen):
    HINTS = (("arrows", "move"), ("enter", "edit"), ("@run", "save"), ("escape", "back"))
    BINDINGS = [Binding("escape", "back", show=False), Binding(keys.ACTIONS["run"], "save", id=keys.binding_id("run"), show=False)]

    def __init__(self, command):
        super().__init__(command)
        self._saved = {}     # the values as read
        self._changed = {}   # flag -> new value
        self._descriptions = {}
        self._fields = {field.flag: field for field in CONFIG_FIELDS}

    @property
    def _is_install(self):
        return self.command == "installconfig"

    def _read_flags(self):
        return () if self._is_install else ("--path", str(self.app.repo))

    def compose_body(self):
        yield LoadingIndicator()

    def on_mount(self):
        command, flags = self.command, self._read_flags()
        self.read(lambda app: (app.client.run(command, flags), app.client.help(command)),
                  lambda both: self._show(*both))

    async def _show(self, result, contract):
        if not self.is_attached:
            return
        try:
            await self._mount_editor(result, contract)
        finally:
            self.focus_first()

    async def _mount_editor(self, result, contract):
        commands = contract.data.get("commands") if contract.success else None
        arguments = commands[0].get("arguments", []) if commands else []
        self._descriptions = {argument["name"]: " ".join(argument.get("description", "").split())
                              for argument in arguments}
        body = self.query_one("#body")
        await body.remove_children()
        texts = self.app.texts
        await body.mount(Static(texts(f"config.title.{self.command}"), classes="title"))
        if not result.success:
            await body.mount(Static(result.detail or result.code or "", classes="error", markup=False))
            return
        if self._is_install and not result.data.get("configured"):
            await body.mount_all(self._create_widgets())
            return
        self._saved = dict(result.data.get("config") or {})
        await body.mount(PagedList(*self._options(), list_id="fields"))
        await body.mount(Static("", id="field-description", classes="info", markup=False))
        options = self.query_one("#fields")
        options.highlighted = next(i for i in range(options.option_count) if not options.get_option_at_index(i).disabled)
        options.focus()

    def _options(self):
        texts = self.app.texts
        for group in GROUPS:
            yield row(f"— {texts(f'config.group.{group}')} —", id=f"group-{group}", disabled=True)
            for field in CONFIG_FIELDS:
                if field.group == group:
                    yield self._option(field)

    def _option(self, field):
        texts = self.app.texts
        changed = field.flag in self._changed
        value = self._changed[field.flag] if changed else self._saved.get(field.flag)
        mark = f" {CHANGED}" if changed else ""
        return row(f"  {texts(f'config.field.{field.flag}')}: {shown_value(field, value)}{mark}", id=field.flag)

    def _description(self, field):
        description = self._descriptions.get(field.flag, "")
        if field.guarded:
            description = f"{description}\n{self.app.texts('config.guarded')}".strip()
        return description

    def on_option_list_option_highlighted(self, event):
        field = self._fields.get(event.option.id)
        if field:
            self.query_one("#field-description", Static).update(self._description(field))

    def on_option_list_option_selected(self, event):
        field = self._fields.get(event.option.id)
        if not field:
            return
        current = self._changed.get(field.flag, self._saved.get(field.flag))
        self.app.push_screen(FieldEditScreen(field, current, self._description(field)),
                             lambda value: self._edited(field, value))

    def _edited(self, field, value):
        if value is None:
            return
        saved = self._saved.get(field.flag, "")
        if field.kind == "multiline" and "\r\n" in str(saved):
            # The text area hands back what was typed with LF: a template
            # stored with CRLF keeps its line endings.
            value = value.replace("\r\n", "\n").replace("\n", "\r\n")
        if as_flag_value(field, value) == as_flag_value(field, saved):
            self._changed.pop(field.flag, None)
        else:
            self._changed[field.flag] = value
        options = self.query_one("#fields")
        options.replace_option_prompt(field.flag, self._option(field).prompt)

    def _save_flags(self):
        flags = list(self._read_flags())
        for field in CONFIG_FIELDS:
            if field.flag in self._changed:
                flags += [f"--{field.flag}", as_flag_value(field, self._changed[field.flag])]
        return flags

    def action_save(self):
        if self.command_running:
            return
        if not self._changed:
            self.app.notify(self.app.texts("config.unchanged"), markup=False)
            return
        self.confirm_and_run([(self.command, self._save_flags())])

    def action_back(self):
        if self.command_running:
            return
        if not self._changed:
            self.app.pop_screen()
            return
        self.app.push_screen(ConfirmScreen("", question=self.app.texts("config.discard")),
                             lambda yes: yes and self.app.pop_screen())

    # An install-level config that does not exist yet --------------------

    def _create_widgets(self):
        texts = self.app.texts
        yield Static(texts("config.install_missing"), id="install-missing", classes="info")
        yield RadioSet(RadioButton(texts("choice.source.language"), value=True, id="create-language"),
                       RadioButton(texts("choice.source.seed"), id="create-seed"), id="create-source")
        yield Select([(i18n.load(code)("language.name"), code) for code in i18n.LANGUAGES],
                     value=self.app.texts.language, allow_blank=False, id="create-language-value")
        yield Input(placeholder=texts("field.seed"), id="create-seed-value")
        yield Button(texts("config.create"), id="create", variant="primary")

    def on_button_pressed(self, event):
        if event.button.id != "create":
            return
        if self.query_one("#create-seed").value:
            flags = ["--seed", self.query_one("#create-seed-value", Input).value]
        else:
            flags = ["--language", self.query_one("#create-language-value", Select).value]
        self.confirm_and_run([(self.command, flags)])
