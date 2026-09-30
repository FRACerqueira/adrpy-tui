"""The decision log, browsed: every entry under the decision-log folder
(subfolders too, as adrpy reads them; its INDEX.md and CYCLES.md left out),
with its date, classification, scope and slug read from its name; Enter or
the preview key opens it."""

from pathlib import Path

from rich.text import Text
from textual.binding import Binding
from textual.widgets import Input, Select, Static

from adrpy_tui.core.files import is_dir, markdown_files, repository_folder, same_name
from adrpy_tui.core.text import visible
from adrpy_tui.ui.base import HINTS_LIST, AdrpyScreen, on_top
from adrpy_tui.ui.explore import _cells
from adrpy_tui.ui.paged import FilterInput, PagedList, row
from adrpy_tui.ui.preview import PREVIEW_BINDING, open_preview, refusal

ALL = "*"
_WIDTHS = (12, 22, 18, 0)


def entry_parts(name):
    """(date, classification, scope, slug) of an entry's file name
    (2026-02-05--audit-finding--security--no-expiry.md), or the name as the
    slug when it does not have that shape."""
    parts = Path(name).stem.split("--")
    if len(parts) == 4:
        return tuple(parts)
    return ("", "", "", Path(name).stem)


class LogScreen(AdrpyScreen):
    HINTS = HINTS_LIST
    BINDINGS = [Binding("escape", "back", show=False), PREVIEW_BINDING]

    def __init__(self):
        super().__init__()
        self._entries = []

    def compose_body(self):
        texts = self.app.texts
        yield Static(texts("logs.title"), classes="title")
        yield FilterInput("entries", placeholder=texts("picker.filter"), id="logs-filter")
        yield Select([(texts("logs.all_classifications"), ALL)], value=ALL, allow_blank=False, id="logs-classification")
        yield Static(_cells([texts(f"column.{name}") for name in ("date", "classification", "scope", "slug")],
                            _WIDTHS), classes="info", markup=False)
        yield PagedList(list_id="entries")
        # The classification and scope columns are cut to their width: the
        # highlighted entry's file name, which holds every column, is shown whole.
        yield Static("", id="logs-current", classes="summary", markup=False)
        yield Static("", id="logs-count", classes="info", markup=False)
        yield Static("", id="logs-unreadable", classes="warning", markup=False)

    def on_mount(self):
        texts = self.app.texts
        # A configuration naming a folder outside the repository (adrpy reads
        # one back from a hand-edited file) lists nothing there; nor one that is,
        # holds or lies in the decisions folder (`doc/adr.` on Windows), which adrpy refuses.
        folder, reason = repository_folder(self.app.repo, self.app.folderlog)
        decisions, decisions_reason = repository_folder(self.app.repo, self.app.folderadr)
        aliased = not reason and not decisions_reason and (
            folder.is_relative_to(decisions) or decisions.is_relative_to(folder))
        self._folder = folder
        unreadable = []
        # adrpy's own pages only, their names compared as its scan compares them: INDEX.md and
        # CYCLES.md anywhere. Any other file blocks `adrpy log`, so it is shown.
        self._entries = [path for path in markdown_files(folder, unreadable=unreadable)
                         if not same_name(path.name, "INDEX.md", "CYCLES.md")] if not (reason or aliased) else []
        # A folder not created yet has no entries, as adrpy reads it; one that cannot be listed is named.
        if unreadable and is_dir(folder):
            self.query_one("#logs-unreadable", Static).update(texts("logs.unreadable", folders=", ".join(
                visible(self.app.folderlog if path == folder else
                        str(path.relative_to(folder)) if path.is_relative_to(folder) else str(path))
                for path in unreadable)))
        classifications = sorted({entry_parts(path.name)[1] for path in self._entries} - {""})
        self.query_one("#logs-classification", Select).set_options(
            [(self.app.texts("logs.all_classifications"), ALL), *((Text(visible(c)), c) for c in classifications)])
        self.query_one(PagedList).empty_text = (
            refusal(self.app, reason, self.app.folderlog) if reason
            else texts("logs.aliased", path=visible(self.app.folderlog), folderadr=visible(self.app.folderadr)) if aliased
            else texts("logs.empty", folder=visible(str(folder))))
        self._fill()
        self.query_one("#entries").focus()

    def _fill(self):
        options = self.query_one("#entries")
        folded = self.query_one("#logs-filter", Input).value.casefold()
        wanted = self.query_one("#logs-classification", Select).value
        options.clear_options()
        for index, path in enumerate(self._entries):
            parts = entry_parts(path.name)
            if wanted not in (ALL, parts[1]) or folded not in path.name.casefold():
                continue
            options.add_option(row(_cells([visible(part) for part in parts], _WIDTHS), id=str(index)))
        if options.option_count:
            options.highlighted = 0
        self.query_one(PagedList).update_page()
        self._show_current()
        self.query_one("#logs-count", Static).update(
            self.app.texts("logs.count", shown=options.option_count, total=len(self._entries)))

    def on_input_changed(self, event):
        self._fill()

    def on_option_list_option_highlighted(self, event):
        if event.option_list.id == "entries":
            self._show_current()

    def _show_current(self):
        options = self.query_one("#entries")
        text = ""
        if options.highlighted is not None and options.option_count:
            path = self._entries[int(options.get_option_at_index(options.highlighted).id)]
            folder = path.parent.relative_to(self._folder).as_posix()
            text = f"{visible(path.name)}  ·  {visible(folder)}"
        self.query_one("#logs-current", Static).update(text)

    def on_input_submitted(self, event):
        if not on_top(self):
            return
        self.query_one("#entries").focus()

    def on_select_changed(self, event):
        if self._entries:
            self._fill()

    def _highlighted(self):
        options = self.query_one("#entries")
        if options.highlighted is None or not options.option_count:
            return None
        return self._entries[int(options.get_option_at_index(options.highlighted).id)]

    def on_option_list_option_selected(self, event):
        if not on_top(self):
            return
        open_preview(self.app, self._entries[int(event.option.id)])

    def action_preview(self):
        open_preview(self.app, self._highlighted())

    def action_back(self):
        self.app.pop_screen()
