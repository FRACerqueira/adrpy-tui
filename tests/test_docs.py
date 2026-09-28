"""The documentation's pages: each opens with the application's icon and a
line to every other page, and no relative link points to a missing file."""

import re
import tomllib
from pathlib import Path
from urllib.parse import unquote

import pytest

ROOT = Path(__file__).parent.parent
ICON = "src/adrpy_tui/icon.png"
ICON_URL = f"https://raw.githubusercontent.com/FRACerqueira/adrpy-tui/main/{ICON}"
REPOSITORY = "https://github.com/FRACerqueira/adrpy-tui/blob/main/"
PAGES = sorted((ROOT / "doc").glob("*.md"))
# The order a reader goes through them: using it, how it is built, releasing it.
READING_ORDER = [("forms.md", "Screens and forms"), ("architecture.md", "Architecture"),
                 ("manual-test-checklist.md", "Manual test checklist")]
ROOT_PAGES = [ROOT / name for name in ("CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md", "CHANGELOG.md")]
LINKED = [ROOT / "README.md", *ROOT_PAGES, *PAGES]
_LINK = re.compile(r"\]\(([^)\s]+)\)")


def _build_targets():
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["hatch"]["build"]["targets"]


def test_the_icon_is_in_the_repository_but_not_in_the_wheel():
    assert (ROOT / ICON).is_file()
    assert ICON in _build_targets()["wheel"]["exclude"]


def test_the_sdist_leaves_out_what_only_the_repository_needs():
    """The CI workflows and the release's manual checklist; the tests stay,
    for whoever packages adrpy-tui from its source."""
    assert set(_build_targets()["sdist"]["exclude"]) == {".github/", "doc/manual-test-checklist.md"}


def test_the_readme_links_only_by_absolute_url():
    """The README is also the package's page on PyPI, where a relative link
    goes nowhere; each link into the repository names a file that exists."""
    targets = _LINK.findall((ROOT / "README.md").read_text(encoding="utf-8"))
    relative = [target for target in targets if not target.startswith(("http://", "https://", "#"))]
    assert relative == []
    tree = REPOSITORY.replace("/blob/", "/tree/")  # a folder's
    missing = [target for target in targets for prefix in (REPOSITORY, tree) if target.startswith(prefix)
               and not (ROOT / unquote(target[len(prefix):].split("#")[0])).exists()]
    assert missing == []


def test_the_readme_opens_with_the_icon_and_links_every_page():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    # An absolute URL: the README is also the package's page on PyPI.
    assert text.splitlines()[0] == f'<img src="{ICON_URL}" width="160" alt="adrpy-tui icon">'
    missing = [page.name for page in PAGES if f"]({REPOSITORY}doc/{page.name})" not in text]
    assert missing == []


def _navigation(current):
    """The line to the README, every page in reading order (the current one
    in bold, not a link) and the decisions."""
    pages = [f"**{title}**" if name == current else f"[{title}]({name})" for name, title in READING_ORDER]
    return " · ".join(["[← README](../README.md)", *pages, "[Decisions](adr/)"])


def test_the_reading_order_is_every_page():
    assert sorted(name for name, _ in READING_ORDER) == [page.name for page in PAGES]


@pytest.mark.parametrize("page", PAGES, ids=lambda page: page.name)
def test_every_page_opens_with_the_icon_and_the_navigation_and_ends_with_it(page):
    lines = page.read_text(encoding="utf-8").strip().splitlines()
    assert lines[0] == f'<img src="../{ICON}" width="160" alt="adrpy-tui icon">'
    assert (lines[2], lines[-1]) == (_navigation(page.name), _navigation(page.name))
    assert lines[4] == f"# {dict(READING_ORDER)[page.name]}"


@pytest.mark.parametrize("page", ROOT_PAGES, ids=lambda page: page.name)
def test_every_root_page_opens_with_a_line_back_to_the_readme(page):
    assert page.read_text(encoding="utf-8").splitlines()[0] == "[← README](README.md)"


@pytest.mark.parametrize("document", LINKED, ids=lambda document: document.name)
def test_every_relative_link_points_to_a_file_that_exists(document):
    targets = [target for target in _LINK.findall(document.read_text(encoding="utf-8"))
               if not target.startswith(("http://", "https://", "#", "mailto:"))]
    broken = [target for target in targets if not (document.parent / unquote(target.split("#")[0])).exists()]
    assert broken == []
