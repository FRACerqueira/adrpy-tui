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
    """One range (ADR003V01): the installed package's metadata is
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
    """ADR003V01: the check warns, it never refuses -- a damaged dist-info
    (None, "") or a version with no leading number raised AttributeError
    in the app's constructor, before any screen."""
    monkeypatch.setattr(versions, "installed_version", lambda name: found)
    monkeypatch.setattr(versions, "adrpy_range", lambda: "<0.2,>=0.1.dev0")
    assert versions.adrpy_outside_range() == (found or "unknown", ">=0.1.dev0, <0.2")
