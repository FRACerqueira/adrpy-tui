"""A decision's or a log entry's content, rendered: the preview key (F3 by
default, core/keys.py) opens it from any list of them. A link to another
.md opens that file's preview; Esc goes back, as a browser does."""

import os
from pathlib import Path

from textual.binding import Binding
from textual.widgets import Markdown, Static

from adrpy_tui.core import keys
from adrpy_tui.core.files import inside_repository, is_file, read_start
from adrpy_tui.core.text import printable, visible
from adrpy_tui.ui.base import AdrpyScreen, on_top

PREVIEW_BINDING = Binding(keys.ACTIONS["preview"], "preview", id=keys.binding_id("preview"), show=False)
# The lines of a file a preview renders: past them the rest is left out and
# a line says so. Rendering costs about 5.5 ms a line (headless), so a file
# of thousands of lines would freeze the screen for tens of seconds.
PREVIEW_LINES = 500
# And its characters: one line of megabytes (1 MB: 2 s) passes any line limit.
PREVIEW_CHARACTERS = 100_000


def excerpt(app, path):
    """(content to render, the note saying it was cut or refused, or None).
    Every reader of a decision's or entry's file comes here: the preview and
    a decision's detail alike."""
    if not inside_repository(app.repo, path):
        return "", app.texts("preview.outside", path=visible(str(path)))
    try:
        content, total_lines, total_characters = read_start(path, PREVIEW_LINES, PREVIEW_CHARACTERS)
    except (OSError, ValueError) as error:  # ValueError: a path no system call takes (a NUL in it)
        return f"`{visible(str(error))}`", None
    note = None
    if total_lines > PREVIEW_LINES:
        note = app.texts("preview.excerpt", shown=PREVIEW_LINES, total=total_lines, path=visible(str(path)))
    if len(content) == PREVIEW_CHARACTERS < total_characters:
        note = app.texts("preview.excerpt_characters", shown=PREVIEW_CHARACTERS, total=total_characters,
                         path=visible(str(path)))
    return printable(content), note


def open_preview(app, path):
    """Opens the preview of `path` when it is a file inside the repository;
    says so otherwise. Whoever names it -- a link, adrpy, a result. The path
    checked is the path opened: normalized once."""
    if not path:
        return
    path = Path(os.path.normpath(os.path.abspath(path)))
    if not inside_repository(app.repo, path):
        app.notify(app.texts("preview.outside", path=visible(str(path))), severity="warning", markup=False)
    elif is_file(path):
        app.push_screen(PreviewScreen(path))
    else:
        app.notify(app.texts("preview.missing", path=visible(str(path))), severity="warning", markup=False)


def follow_link(app, source, href):
    """A link in `source`'s content: another .md, relative to it, opens its
    preview if it lies inside the repository (open_preview checks it, before
    the file system is touched); anything else (a web page) is only named --
    never opened in a browser from a file the TUI did not write
    (ADR006V02)."""
    relative = href.split("#", 1)[0]
    if not relative or "://" in relative or Path(relative).suffix.lower() != ".md":
        app.notify(visible(href), markup=False)
        return
    open_preview(app, Path(os.path.join(os.path.abspath(Path(source).parent), relative)))


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
        if not on_top(self):
            return
        follow_link(self.app, self.path, event.href)

    def action_back(self):
        self.app.pop_screen()
