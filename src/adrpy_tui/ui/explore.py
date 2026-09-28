"""`explore`: every decision of the repository in the interface's paged
list, then one decision's detail -- its header, its content, and the
commands its state allows, each opening its form with the decision chosen.
Both read the repository again when they come back to the top, so they show
what a command just changed."""

from pathlib import Path

from rich.cells import cell_len
from textual.binding import Binding
from textual.widgets import Input, LoadingIndicator, Markdown, Static

from adrpy_tui.core.decisions import state
from adrpy_tui.core.registry import commands_taking
from adrpy_tui.core.text import printable
from adrpy_tui.ui.base import AdrpyScreen
from adrpy_tui.ui.form import FormScreen
from adrpy_tui.ui.paged import PagedList, row

_WIDTHS = (46, 14, 14, 14)


def _cells(values, widths=_WIDTHS):
    """Values padded to their column, by terminal cells (a CJK label takes
    two per character); only the last column, with nothing after it, is
    never cut."""
    padded = []
    last = len(values) - 1
    for index, (value, width) in enumerate(zip(values, widths)):
        value = value or ""
        if index == last:
            padded.append(value)
            break
        while cell_len(value) > width - 1:
            value = value[:-1]
        padded.append(value + " " * (width - cell_len(value)))
    return "".join(padded).rstrip()


def _read_explore(app):
    return app.client.run("explore", ("--path", str(app.repo)))


class ExploreScreen(AdrpyScreen):
    HINTS = "hints.menu"
    BINDINGS = [Binding("escape", "back", show=False)]

    def __init__(self):
        super().__init__("explore")
        self._decisions = []

    def compose_body(self):
        texts = self.app.texts
        yield Input(placeholder=texts("picker.filter"), id="explore-filter")
        yield Static(_cells([texts(f"column.{name}") for name in ("file", "status", "scope", "domain")]),
                     classes="info", markup=False)
        yield PagedList(list_id="decisions")
        yield Static("", id="explore-notes", classes="warning", markup=False)

    def on_screen_resume(self):
        # Also sent when the screen first opens.
        self.run_worker(lambda: self.app.call_from_thread(self._show, _read_explore(self.app)), thread=True)

    def _show(self, result):
        if not self.is_attached:
            return
        paged, texts = self.query_one(PagedList), self.app.texts
        if not result.success:
            self._decisions = []
            paged.empty_text = texts("picker.failed", detail=result.detail or result.code)
        else:
            self._decisions = sorted(result.data.get("decisions", []), key=lambda decision: decision["filename"])
            paged.empty_text = texts("picker.empty")
        notes = [texts("explore.inconsistent", count=len(errors))
                 for errors in [(result.data.get("consistency") or {}).get("errors") or []] if errors]
        notes += [str(warning) for warning in result.warnings]
        self.query_one("#explore-notes", Static).update("\n".join(notes))
        self._fill()

    def _fill(self):
        options, labels = self.query_one("#decisions"), self.app.labels
        folded = self.query_one("#explore-filter", Input).value.casefold()
        options.clear_options()
        for index, decision in enumerate(self._decisions):
            if folded in decision["filename"].casefold():
                header = decision.get("header") or {}
                cells = (decision["filename"], labels.get(state(decision), "?"), header.get("scope"), header.get("domain"))
                options.add_option(row(_cells(cells), id=str(index)))
        if options.option_count:
            options.highlighted = 0
        self.query_one(PagedList).update_page()

    def on_input_changed(self, event):
        self._fill()

    def on_input_submitted(self, event):
        self.query_one("#decisions").focus()

    def on_option_list_option_selected(self, event):
        self.app.push_screen(DetailScreen(self._decisions[int(event.option.id)]))

    def action_back(self):
        self.app.pop_screen()


class DetailScreen(AdrpyScreen):
    HINTS = "hints.menu"
    BINDINGS = [Binding("escape", "back", show=False)]

    def __init__(self, decision):
        super().__init__("explore")
        self.decision = decision

    def compose_body(self):
        yield LoadingIndicator()

    def on_screen_resume(self):
        # Also sent when the screen first opens: read again, since a command
        # run from here may have changed this decision.
        self.run_worker(lambda: self.app.call_from_thread(self._show, _read_explore(self.app)), thread=True)

    async def _show(self, result):
        if not self.is_attached:
            return
        if result.success:
            again = [d for d in result.data.get("decisions", []) if d["path"] == self.decision["path"]]
            if again:
                self.decision = again[0]
        body = self.query_one("#body")
        await body.remove_children()
        await body.mount_all(self._widgets())
        actions = self.query("#actions")
        if actions:
            actions.first().focus()

    def _widgets(self):
        texts, decision = self.app.texts, self.decision
        header = decision.get("header") or {}
        decision_state = state(decision)
        yield Static(decision["filename"], classes="title", markup=False)
        rows = [
            ("detail.status", self.app.labels.get(decision_state, "?")),
            ("detail.scope", header.get("scope")),
            ("detail.domain", header.get("domain")),
            ("detail.created", header.get("date_create")),
            ("detail.changed", header.get("date_update")),
            ("detail.superseded", header.get("superseded_by_file")),
        ]
        for key, value in rows:
            if value:
                yield Static(f"{texts(key)}: {value}", classes="info", markup=False)
        commands = commands_taking(decision_state)
        if commands:
            yield Static(texts("detail.actions"), classes="title")
            yield PagedList(*(row(texts(f"menu.decisions.{command}"), id=command) for command in commands),
                            list_id="actions")
        yield Markdown(self._content())

    def _content(self):
        try:
            return printable(Path(self.decision["path"]).read_text(encoding="utf-8", errors="replace"))
        except OSError as error:
            return f"`{error}`"

    def on_option_list_option_selected(self, event):
        self.app.push_screen(FormScreen(event.option.id, decision=self.decision["path"]))

    def action_back(self):
        self.app.pop_screen()
