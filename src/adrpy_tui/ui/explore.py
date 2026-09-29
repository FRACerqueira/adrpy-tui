"""`explore`: every decision of the repository in the interface's paged
list, then one decision's detail -- its header, its content, and the
commands its state allows, each opening its form with the decision chosen.
Both read the repository again when they come back to the top, so they show
what a command just changed."""


from rich.cells import cell_len
from rich.text import Text
from textual.binding import Binding
from textual.widgets import Input, LoadingIndicator, Markdown, Select, Static

from adrpy_tui.core.decisions import folder_of, state
from adrpy_tui.core.registry import commands_taking
from adrpy_tui.core.text import visible
from adrpy_tui.ui.base import HINTS_LIST, AdrpyScreen, on_top
from adrpy_tui.ui.form import FormScreen
from adrpy_tui.ui.preview import PREVIEW_BINDING, excerpt, follow_link, open_preview
from adrpy_tui.ui.paged import FilterInput, PagedList, row

_WIDTHS = (40, 18, 14, 14, 14)
ALL_FOLDERS = "*"


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
    HINTS = HINTS_LIST
    BINDINGS = [Binding("escape", "back", show=False), PREVIEW_BINDING]

    def __init__(self):
        super().__init__("explore")
        self._decisions = []
        self._folders = {}  # path -> folder, relative to the decisions folder

    def compose_body(self):
        texts = self.app.texts
        yield FilterInput("decisions", placeholder=texts("explore.filter"), id="explore-filter")
        yield Select([(texts("explore.all_folders"), ALL_FOLDERS)], value=ALL_FOLDERS, allow_blank=False,
                     id="explore-folder")
        yield Static(_cells([texts(f"column.{name}") for name in ("file", "folder", "status", "scope", "domain")]),
                     classes="info", markup=False)
        yield PagedList(list_id="decisions")
        # Every column but the last is cut to its width: the highlighted row's
        # values are shown here whole.
        yield Static("", id="explore-current", classes="summary", markup=False)
        yield Static("", id="explore-count", classes="info", markup=False)
        yield Static("", id="explore-notes", classes="warning", markup=False)

    def on_screen_resume(self):
        # Also sent when the screen first opens.
        self.read(_read_explore, self._show)

    def _show(self, result):
        if not self.is_attached:
            return
        paged, texts = self.query_one(PagedList), self.app.texts
        if not result.success:
            self._decisions = []
            paged.empty_text = texts("picker.failed", detail=visible(result.detail or result.code or ""))
        else:
            self._decisions = sorted(result.data.get("decisions", []), key=lambda decision: decision["filename"])
            paged.empty_text = texts("picker.empty")
        notes = [texts("explore.inconsistent", count=len(errors))
                 for errors in [(result.data.get("consistency") or {}).get("errors") or []] if errors]
        notes += [visible(str(warning)) for warning in result.warnings]
        self.query_one("#explore-notes", Static).update("\n".join(notes))
        root = self.app.repo / self.app.folderadr
        self._folders = {decision["path"]: folder_of(decision["path"], root) for decision in self._decisions}
        chosen = self.query_one("#explore-folder", Select)
        keep = chosen.value
        folders = sorted(set(self._folders.values()))
        # A folder's name as it is: a str prompt would be read as markup.
        chosen.set_options([(texts("explore.all_folders"), ALL_FOLDERS),
                            *((Text(visible(folder)), folder) for folder in folders)])
        chosen.value = keep if keep in folders else ALL_FOLDERS
        self._fill()

    def _fill(self):
        """The decisions of the chosen folder whose name or folder holds the
        filter's text."""
        options, labels = self.query_one("#decisions"), self.app.labels
        folded = self.query_one("#explore-filter", Input).value.casefold()
        wanted = self.query_one("#explore-folder", Select).value
        options.clear_options()
        for index, decision in enumerate(self._decisions):
            folder = self._folders.get(decision["path"], "")
            if wanted not in (ALL_FOLDERS, folder):
                continue
            if folded in decision["filename"].casefold() or folded in folder.casefold():
                header = decision.get("header") or {}
                cells = tuple(visible(str(cell)) if cell else cell for cell in (
                    decision["filename"], folder, labels.get(state(decision), "?"), header.get("scope"),
                    header.get("domain")))
                options.add_option(row(_cells(cells), id=str(index)))
        if options.option_count:
            options.highlighted = 0
            if not isinstance(self.app.focused, (Input, Select)):
                options.focus()  # the arrows move the list, not the page
        self.query_one(PagedList).update_page()
        self._show_current()
        self.query_one("#explore-count", Static).update(
            self.app.texts("explore.count", shown=options.option_count, total=len(self._decisions)))

    def on_select_changed(self, event):
        if event.select.id == "explore-folder" and self._decisions:
            self._fill()

    def on_input_changed(self, event):
        self._fill()

    def on_input_submitted(self, event):
        if not on_top(self):
            return
        self.query_one("#decisions").focus()

    def on_option_list_option_highlighted(self, event):
        if event.option_list.id == "decisions":
            self._show_current()

    def _show_current(self):
        options = self.query_one("#decisions")
        text = ""
        if options.highlighted is not None and options.option_count:
            decision = self._decisions[int(options.get_option_at_index(options.highlighted).id)]
            header = decision.get("header") or {}
            values = (decision["filename"], self._folders.get(decision["path"], ""),
                      self.app.labels.get(state(decision), "?"), header.get("scope"), header.get("domain"))
            text = "  ·  ".join(visible(str(value)) for value in values if value)
        self.query_one("#explore-current", Static).update(text)

    def on_option_list_option_selected(self, event):
        if not on_top(self):
            return
        self.app.push_screen(DetailScreen(self._decisions[int(event.option.id)]))

    def action_preview(self):
        options = self.query_one("#decisions")
        if options.highlighted is not None and options.option_count:
            open_preview(self.app, self._decisions[int(options.get_option_at_index(options.highlighted).id)]["path"])

    def action_back(self):
        self.app.pop_screen()


class DetailScreen(AdrpyScreen):
    HINTS = HINTS_LIST
    BINDINGS = [Binding("escape", "back", show=False), PREVIEW_BINDING]

    def __init__(self, decision):
        super().__init__("explore")
        self.decision = decision

    def compose_body(self):
        yield LoadingIndicator()

    def on_screen_resume(self):
        # Also sent when the screen first opens: read again, since a command
        # run from here may have changed this decision. Meanwhile its actions
        # are those of the state read before: none is offered until it answers.
        for actions in self.query("#actions"):
            actions.disabled = True
        self.read(_read_explore, self._show)

    async def _show(self, result):
        if not self.is_attached:
            return
        gone = False
        if result.success:
            again = [d for d in result.data.get("decisions", []) if d["path"] == self.decision["path"]]
            if again:
                self.decision = again[0]
            gone = not again  # renamed, deleted, or moved behind a link: nothing of it to offer
        body = self.query_one("#body")
        await body.remove_children()
        if gone:
            await body.mount(Static(self.app.texts("detail.gone"), id="read-failed", classes="error", markup=False))
            return
        if not result.success:
            # What is on screen may no longer be so: say it, and offer no action on it.
            await body.mount(Static(self.app.texts("detail.read_failed", detail=visible(result.detail or result.code or "")),
                                    id="read-failed", classes="error", markup=False))
        await body.mount_all(self._widgets(actions=result.success))
        actions = self.query("#actions")
        if actions:
            actions.first().focus()
        else:
            self.focus_first()  # no action to take: the arrows scroll its content

    def _widgets(self, actions=True):
        texts, decision = self.app.texts, self.decision
        header = decision.get("header") or {}
        decision_state = state(decision)
        yield Static(visible(decision["filename"]), classes="title", markup=False)
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
                yield Static(f"{texts(key)}: {visible(str(value))}", classes="info", markup=False)
        commands = commands_taking(decision_state) if actions else []
        if commands:
            yield Static(texts("detail.actions"), classes="title")
            yield PagedList(*(row(texts(f"menu.decisions.{command}"), id=command) for command in commands),
                            list_id="actions")
        content, note = excerpt(self.app, self.decision["path"])
        if note:
            yield Static(note, id="excerpt", classes="warning", markup=False)
        yield Markdown(content, open_links=False)

    def on_option_list_option_selected(self, event):
        if not on_top(self):
            return
        self.app.push_screen(FormScreen(event.option.id, decision=self.decision["path"]))

    def action_preview(self):
        open_preview(self.app, self.decision["path"])

    def on_markdown_link_clicked(self, event):
        if not on_top(self):
            return
        follow_link(self.app, self.decision["path"], event.href)

    def action_back(self):
        self.app.pop_screen()
