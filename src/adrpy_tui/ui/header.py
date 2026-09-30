"""The header every screen shows: the banner between two double rules, the
versions, the repository and, on a command's screens, the command line."""

from importlib import resources

from textual.containers import Vertical
from textual.widgets import Rule, Static

from adrpy_tui.core.text import visible
from adrpy_tui.core.versions import installed_version

BANNER = resources.files("adrpy_tui.resources").joinpath("banner.txt").read_text(encoding="utf-8").rstrip("\n")
BANNER_WIDTH = max(len(line) for line in BANNER.splitlines())


def _double_rule():
    rule = Rule(line_style="double")
    rule.styles.width = BANNER_WIDTH
    return rule


class AppHeader(Vertical):
    def __init__(self, line=None):
        super().__init__()
        self._line = line

    def compose(self):
        texts = self.app.texts
        yield _double_rule()
        yield Static(BANNER, classes="banner", markup=False)
        yield _double_rule()
        yield Static(
            texts("app.welcome", tui=installed_version("adrpy-tui"), adrpy=installed_version("adrpy-ai")),
            classes="info",
            markup=False,
        )
        yield Static(texts("app.repo", path=visible(str(self.app.repo))), classes="info", markup=False)
        if self._line:
            yield Static(self._line, classes="banner", markup=False)
