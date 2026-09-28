"""A decision's or a log entry's content, rendered: the preview key (F3 by
default, core/keys.py) opens it from any list of them. A link to another
.md opens that file's preview; Esc goes back, as a browser does."""

import os
from pathlib import Path

from textual.binding import Binding
from textual.widgets import Markdown, Static

from adrpy_tui.core import keys
from adrpy_tui.core.text import printable, visible
from adrpy_tui.ui.base import AdrpyScreen

PREVIEW_BINDING = Binding(keys.ACTIONS["preview"], "preview", id=keys.binding_id("preview"), show=False)
# The lines of a file a preview renders: past them the rest is left out and
# a line says so. Rendering costs about 5.5 ms a line (headless), so a file
# of thousands of lines would freeze the screen for tens of seconds.
PREVIEW_LINES = 500


def excerpt(app, path):
    """(content to render, the note saying it was cut, or None)."""
    try:
        content = printable(Path(path).read_text(encoding="utf-8", errors="replace"))
    except OSError as error:
        return f"`{error}`", None
    lines = content.splitlines()
    if len(lines) <= PREVIEW_LINES:
        return content, None
    note = app.texts("preview.excerpt", shown=PREVIEW_LINES, total=len(lines), path=visible(str(path)))
    return "\n".join(lines[:PREVIEW_LINES]), note


def open_preview(app, path):
    """Opens the preview of `path` when it is a file; says so otherwise."""
    if path and Path(path).is_file():
        app.push_screen(PreviewScreen(Path(path)))
    elif path:
        app.notify(app.texts("preview.missing", path=visible(str(path))), severity="warning", markup=False)


def follow_link(app, source, href):
    """A link in `source`'s content: another .md inside the repository,
    relative to it, opens its preview; anything else (a web page, a missing
    file) is only named -- never opened in a browser from a file the TUI did
    not write. An absolute or network path, or one leading outside the
    repository, is refused before the file system is touched: a network path
    would make the machine connect to another host (ADR006V01)."""
    relative = href.split("#", 1)[0]
    if not relative or "://" in relative or Path(relative).suffix.lower() != ".md":
        app.notify(visible(href), markup=False)
        return
    root = os.path.normpath(os.path.abspath(app.repo))
    target = os.path.normpath(os.path.join(os.path.abspath(Path(source).parent), relative))
    if Path(relative).is_absolute() or Path(relative).drive or relative[0] in "/\\" \
            or os.path.commonpath([root, target]) != root:
        app.notify(app.texts("preview.outside", path=visible(relative)), severity="warning", markup=False)
        return
    open_preview(app, Path(target))


class PreviewScreen(AdrpyScreen):
    READS = True
    HINTS = (("escape", "back"),)
    BINDINGS = [Binding("escape", "back", show=False)]

    def __init__(self, path):
        super().__init__()
        self.path = Path(path)

    def compose_body(self):
        yield Static(visible(self.path.name), classes="title", markup=False)
        content, note = excerpt(self.app, self.path)
        if note:
            yield Static(note, id="excerpt", classes="warning", markup=False)
        yield Markdown(content, open_links=False)

    def on_markdown_link_clicked(self, event):
        follow_link(self.app, self.path, event.href)

    def action_back(self):
        self.app.pop_screen()
