"""A repository's inconsistencies, as `check` and every lifecycle command
report them (`data.errors`): one row per error, the highlighted one's repair
hint below, in adrpy's own words."""

from pathlib import PureWindowsPath

from textual.containers import Vertical
from textual.widgets import Static

from adrpy_tui.core.text import visible
from adrpy_tui.ui.paged import PagedList, row


def _name(path):
    # adrpy reports the path of the machine it runs on; PureWindowsPath
    # splits on both separators.
    return PureWindowsPath(path).name if path else ""


def error_row(error):
    return "  ·  ".join(visible(part) for part in (_name(error.get("file")), error.get("code")) if part)


class ErrorList(Vertical):
    DEFAULT_CSS = "ErrorList { height: auto; }"

    def __init__(self, errors, id="errors"):
        super().__init__(id=id)
        self._errors = errors

    def compose(self):
        yield PagedList(*(row(error_row(error), id=str(i)) for i, error in enumerate(self._errors)),
                        list_id=f"{self.id}-options")
        yield Static("", id=f"{self.id}-hint", classes="warning", markup=False)

    def on_mount(self):
        options = self.query_one(f"#{self.id}-options")
        if options.option_count:
            options.highlighted = 0

    def highlighted_path(self):
        options = self.query_one(f"#{self.id}-options")
        if options.highlighted is None or not options.option_count:
            return None
        return self._errors[int(options.get_option_at_index(options.highlighted).id)].get("file")

    def on_option_list_option_highlighted(self, event):
        event.stop()
        error = self._errors[int(event.option.id)]
        lines = [text for text in (error.get("detail"), error.get("hint")) if text]
        related = [_name(path) for path in error.get("related_files") or []]
        if related:
            lines.append(self.app.texts("errors.related", files=", ".join(related)))
        self.query_one(f"#{self.id}-hint", Static).update("\n".join(lines))
