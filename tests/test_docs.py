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
LINKED = [ROOT / "README.md", ROOT / "CONTRIBUTING.md", *PAGES]
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


@pytest.mark.parametrize("page", PAGES, ids=lambda page: page.name)
def test_every_page_opens_with_the_icon_and_a_line_to_the_others(page):
    lines = page.read_text(encoding="utf-8").splitlines()
    assert lines[0] == f'<img src="../{ICON}" width="160" alt="adrpy-tui icon">'
    navigation = lines[2]
    assert navigation.startswith("[← README](../README.md)")
    missing = [other.name for other in PAGES if other != page and f"]({other.name})" not in navigation]
    assert missing == []


@pytest.mark.parametrize("document", LINKED, ids=lambda document: document.name)
def test_every_relative_link_points_to_a_file_that_exists(document):
    targets = [target for target in _LINK.findall(document.read_text(encoding="utf-8"))
               if not target.startswith(("http://", "https://", "#", "mailto:"))]
    broken = [target for target in targets if not (document.parent / unquote(target.split("#")[0])).exists()]
    assert broken == []
