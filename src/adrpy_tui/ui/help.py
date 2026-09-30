"""A command's full contract, as `help <command>` returns it; the
descriptions are adrpy's own, in English (ADR0005V01)."""

from textual.binding import Binding
from textual.widgets import LoadingIndicator, Markdown, Static

from adrpy_tui.core.registry import command_name
from adrpy_tui.core.text import visible
from adrpy_tui.ui.base import AdrpyScreen, on_top


def _cell(text):
    return " ".join(str(text).split()).replace("|", "\\|")


def contract_markdown(texts, command, contract):
    lines = [f"# {command_name(command)}", "", _cell(contract.get("summary", "")), ""]
    if contract.get("description"):
        lines += [contract["description"], ""]
    arguments = contract.get("arguments") or []
    if arguments:
        lines += [
            f"## {texts('help.arguments')}",
            "",
            f"| {texts('help.flag')} | {texts('help.type')} | {texts('help.required')} | {texts('help.description')} |",
            "|---|---|---|---|",
        ]
        for argument in arguments:
            flag = argument["name"] if argument.get("positional") else f"--{argument['name']}"
            required = texts("help.yes") if argument.get("required") else texts("help.no")
            lines.append(f"| `{flag}` | {argument.get('type', '')} | {required} | {_cell(argument.get('description', ''))} |")
        lines.append("")
    failure_codes = contract.get("failure_codes") or []
    if failure_codes:
        lines += [f"## {texts('help.failure_codes')}", "", f"| {texts('help.code')} | {texts('help.condition')} |", "|---|---|"]
        lines += [f"| `{code['code']}` | {_cell(code.get('condition', ''))} |" for code in failure_codes]
    return "\n".join(lines)


class HelpScreen(AdrpyScreen):
    READS = True
    BINDINGS = [Binding("escape", "back", show=False)]

    def compose_body(self):
        yield Static(self.app.texts("help.note"), classes="info")
        yield LoadingIndicator()

    def on_mount(self):
        command = self.command
        self.read(lambda app: app.client.help(command), self._show)

    def _show(self, result):
        if not self.is_attached:  # the person left meanwhile
            return
        body = self.query_one("#body")
        body.query(LoadingIndicator).remove()
        commands = result.data.get("commands") if result.success else None
        if commands:
            # Like every other Markdown here, a link is named, never opened in a browser.
            body.mount(Markdown(contract_markdown(self.app.texts, self.command, commands[0]), open_links=False))
        else:
            body.mount(Static(visible(result.detail or result.code or ""), classes="error", markup=False))

    def on_markdown_link_clicked(self, event):
        if not on_top(self):
            return
        self.app.notify(visible(event.href), markup=False)

    def action_back(self):
        self.app.pop_screen()
