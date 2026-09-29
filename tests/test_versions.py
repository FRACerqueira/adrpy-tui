import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.version import Version

from adrpy_tui.core import versions

PYPROJECT = Path(__file__).parent.parent / "pyproject.toml"


def _declared():
    dependencies = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["dependencies"]
    return next(Requirement(d) for d in dependencies if Requirement(d).name == "adrpy-ai")


def test_the_start_up_check_reads_the_range_pyproject_declares():
    """One range (ADR0003V01): the installed package's metadata is
    pyproject's, as of the last install -- reinstall after changing it."""
    assert Requirement(f"adrpy-ai{versions.adrpy_range()}").specifier == _declared().specifier


def test_the_declared_range_is_the_validated_series():
    assert str(_declared().specifier) in {">=0.1.dev0,<0.2", "<0.2,>=0.1.dev0"}


@pytest.mark.parametrize("found", [
    "0.1.dev0", "0.1.dev335+g6e69e7573", "0.1.0", "0.1.5", "0.1.10.dev2", "0.1.0rc1",
    "0.0.9", "0.2.0.dev3", "0.2.0", "0.2", "1.0.0", "0.10.0",
])
def test_within_range_agrees_with_pep_440(found):
    specifier = _declared().specifier
    assert versions.within(found, str(specifier)) == specifier.contains(Version(found), prereleases=True)


def test_an_adrpy_outside_the_range_is_named_with_the_range(monkeypatch):
    monkeypatch.setattr(versions, "installed_version", lambda name: "0.2.0" if name == "adrpy-ai" else "1")
    monkeypatch.setattr(versions, "adrpy_range", lambda: "<0.2,>=0.1.dev0")
    assert versions.adrpy_outside_range() == ("0.2.0", ">=0.1.dev0, <0.2")


def test_an_adrpy_within_the_range_or_not_installed_is_not_named(monkeypatch):
    monkeypatch.setattr(versions, "adrpy_range", lambda: "<0.2,>=0.1.dev0")
    monkeypatch.setattr(versions, "installed_version", lambda name: "0.1.dev335+g6e69e7573")
    assert versions.adrpy_outside_range() is None
    monkeypatch.setattr(versions, "installed_version", lambda name: versions.NOT_INSTALLED)
    assert versions.adrpy_outside_range() is None  # the header already says it is not installed


@pytest.mark.parametrize("found", ["v0.1", "", None, "unknown", "local-build"])
def test_an_installed_version_that_cannot_be_read_is_named_not_a_crash(monkeypatch, found):
    """ADR0003V01: the check warns, it never refuses -- a damaged dist-info
    (None, "") or a version with no leading number raised AttributeError
    in the app's constructor, before any screen."""
    monkeypatch.setattr(versions, "installed_version", lambda name: found)
    monkeypatch.setattr(versions, "adrpy_range", lambda: "<0.2,>=0.1.dev0")
    assert versions.adrpy_outside_range() == (found or "unknown", ">=0.1.dev0, <0.2")



@pytest.mark.parametrize("failure", [UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid"), None])
def test_damaged_metadata_reads_as_not_installed(monkeypatch, failure):
    """A dist-info whose METADATA is not UTF-8 raised in the app's constructor
    and in --version; one with no Version header gave None, shown as "None"."""
    def version(name):
        if failure is None:
            return None
        raise failure

    monkeypatch.setattr(versions, "version", version)
    assert versions.installed_version("adrpy-ai") == versions.NOT_INSTALLED



def test_damaged_metadata_of_adrpy_tui_itself_is_no_range(monkeypatch):
    """adrpy_range read adrpy-tui's own requirements: metadata that is not
    UTF-8 raised in the app's constructor, like installed_version did."""
    def requires(name):
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid")

    monkeypatch.setattr(versions, "requires", requires)
    assert versions.adrpy_range() == ""


def test_version_with_damaged_metadata_still_prints(monkeypatch, capsys):
    """--version read adrpy-tui's Summary catching only a missing package:
    metadata that is not UTF-8 ended it with a traceback."""
    from adrpy_tui import __main__

    def metadata(name):
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid")

    monkeypatch.setattr(__main__, "metadata", metadata)
    assert __main__.main(["--version"]) == 0
    assert capsys.readouterr().out.startswith("adrpy-tui ")


def test_what_package_metadata_says_never_acts_on_the_terminal(monkeypatch, capsys):
    """Versions, the declared range and the summary came from package
    metadata as it was: an escape sequence in them reached the header, the
    main menu's warning and --version's output."""
    from adrpy_tui import __main__

    monkeypatch.setattr(versions, "version", lambda name: "1.0\x1b[2J\x1b]0;x\x07")
    monkeypatch.setattr(versions, "requires", lambda name: ["adrpy-ai>=0.1\x1b[2J,<0.2"])
    monkeypatch.setattr(__main__, "metadata", lambda name: {"Summary": "A TUI\x1b[31m"})
    assert "\x1b" not in versions.installed_version("adrpy-ai")
    assert "\x1b" not in versions.adrpy_range()
    assert __main__.main(["--version"]) == 0
    assert "\x1b" not in capsys.readouterr().out


def test_version_without_a_summary_prints_no_none(monkeypatch, capsys):
    from adrpy_tui import __main__

    monkeypatch.setattr(__main__, "metadata", lambda name: {"Summary": None})
    assert __main__.main(["--version"]) == 0
    assert "None" not in capsys.readouterr().out
