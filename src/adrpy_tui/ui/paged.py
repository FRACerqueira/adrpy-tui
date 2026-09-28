"""The interface's list: eight rows a page, with the page the cursor is on
below it once there is more than one (doc/forms.md, "Lists"). Every
screen's OptionList sits in one; tests/test_ui.py checks it."""

from rich.text import Text
from textual.containers import Vertical
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

PAGE_SIZE = 8


def page_of(highlighted, total, page_size=PAGE_SIZE):
    """(first, last, page, pages) of the page the cursor is on, counting
    from 1."""
    pages = max(1, -(-total // page_size))
    page = (highlighted or 0) // page_size + 1
    return (page - 1) * page_size + 1, min(page * page_size, total), page, pages


def row(text, **options):
    """A list's option showing `text` as it is: a string prompt would be read
    as markup, and a name from a file ("use-[beta]-api") lose its brackets.
    Every option of the interface is made here."""
    return Option(Text(text), **options)


class PagedList(Vertical):
    DEFAULT_CSS = "PagedList { height: auto; }"

    def __init__(self, *options, list_id, page_id=None):
        super().__init__()
        self._options = options
        self._list_id = list_id
        self._page_id = page_id or f"{list_id}-page"
        self.empty_text = ""  # shown when the list has no option

    @property
    def option_list(self):
        return self.query_one(OptionList)

    def compose(self):
        options = OptionList(*self._options, id=self._list_id)
        # A page of rows plus the list's top and bottom border.
        options.styles.max_height = PAGE_SIZE + 2
        yield options
        yield Static("", id=self._page_id, classes="info", markup=False)

    def on_mount(self):
        self.update_page()

    def on_option_list_option_highlighted(self, event):
        # Not stopped: the screen handles the highlight too.
        self.update_page()

    def update_page(self):
        options = self.option_list
        total = options.option_count
        if not total:
            text = self.empty_text
        elif total <= PAGE_SIZE:
            text = ""
        else:
            first, last, page, pages = page_of(options.highlighted, total)
            text = self.app.texts("list.page", first=first, last=last, total=total, page=page, pages=pages)
        self.query_one(f"#{self._page_id}", Static).update(text)
