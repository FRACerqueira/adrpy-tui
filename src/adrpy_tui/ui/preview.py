"""A decision's or a log entry's content, rendered: the preview key (F3 by
default, core/keys.py) opens it from any list of them. A link to another
.md opens that file's preview; Esc goes back, as a browser does."""

from pathlib import Path

from textual.binding import Binding
from textual.widgets import Markdown, Static

from adrpy_tui.core import keys
from adrpy_tui.core.text import printable
from adrpy_tui.ui.base import AdrpyScreen

PREVIEW_BINDING = Binding(keys.ACTIONS["preview"], "preview", id=keys.binding_id("preview"), show=False)


def open_preview(app, path):
    """Opens the preview of `path` when it is a file; says so otherwise."""
    if path and Path(path).is_file():
        app.push_screen(PreviewScreen(Path(path)))
    elif path:
        app.notify(app.texts("preview.missing", path=str(path)), severity="warning")


def follow_link(app, source, href):
    """A link in `source`'s content: another .md, relative to it, opens its
    preview; anything else (a web page, a missing file) is only named --
    never opened in a browser from a file the TUI did not write."""
    relative = href.split("#", 1)[0]
    target = (Path(source).parent / relative).resolve() if relative and "://" not in relative else None
    if target and target.suffix.lower() == ".md":
        open_preview(app, target)
    else:
        app.notify(printable(href))


class PreviewScreen(AdrpyScreen):
    HINTS = (("escape", "back"),)
    BINDINGS = [Binding("escape", "back", show=False)]

    def __init__(self, path):
        super().__init__()
        self.path = Path(path)

    def compose_body(self):
        yield Static(printable(self.path.name), classes="title", markup=False)
        try:
            content = printable(self.path.read_text(encoding="utf-8", errors="replace"))
        except OSError as error:
            content = f"`{error}`"
        yield Markdown(content, open_links=False)

    def on_markdown_link_clicked(self, event):
        follow_link(self.app, self.path, event.href)

    def action_back(self):
        self.app.pop_screen()
