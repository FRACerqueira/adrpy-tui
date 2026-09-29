"""Change repository: a folder's path, typed or chosen in a tree of
folders that starts above the current repository. The folder must exist;
it need not be initialized (Repository > Initialize does that)."""

from pathlib import Path

from rich.text import Text
from textual.binding import Binding
from textual.widgets import DirectoryTree, Input, Static

from adrpy_tui.core import keys
from adrpy_tui.core.files import is_dir
from adrpy_tui.core.text import visible
from adrpy_tui.ui.base import AdrpyScreen, on_top
from adrpy_tui.ui.inputs import SafeInput
from adrpy_tui.ui.paged import PAGE_SIZE


class FoldersTree(DirectoryTree):
    def filter_paths(self, paths):
        return [path for path in paths if is_dir(path) and not path.name.startswith(".")]

    def process_label(self, label):
        # A folder's name as plain text: Textual would read it as markup
        # ("[red]x"), and draw an escape sequence in it as is.
        return Text(visible(label)) if isinstance(label, str) else label


class RepositoryScreen(AdrpyScreen):
    HINTS = (("tab", "tree"), ("enter", "open_choose"), ("@run", "use"), ("escape", "back"))
    BINDINGS = [Binding("escape", "back", show=False), Binding(keys.ACTIONS["run"], "use", id=keys.binding_id("run"), show=False)]

    def compose_body(self):
        texts = self.app.texts
        yield Static(texts("repository.title"), classes="title")
        yield SafeInput(str(self.app.repo), id="repository-path")
        yield Static("", id="problem-path", classes="error", markup=False)
        tree = FoldersTree(self.app.repo.parent, id="folders")
        tree.styles.max_height = PAGE_SIZE + 2
        yield tree

    def on_directory_tree_directory_selected(self, event):
        if not on_top(self):
            return
        self.query_one("#repository-path", Input).value = str(event.path)

    def on_input_submitted(self, event):
        if not on_top(self):
            return
        self.action_use()

    def action_use(self):
        value = self.query_one("#repository-path", Input).value.strip()
        try:
            # An empty value would be "." -- the folder the TUI was started in.
            path = Path(value).expanduser() if value else None
        except RuntimeError:  # "~name" of a user this machine does not know
            path = None
        if path is None or not is_dir(path):
            self.query_one("#problem-path", Static).update(self.app.texts("repository.not_a_folder", path=value))
            return
        self.app.use_repository(path)

    def action_back(self):
        self.app.pop_screen()
