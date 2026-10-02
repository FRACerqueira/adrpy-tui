"""Installed versions, for the header and `adrpy-tui --version`, and the
start-up check of adrpy-ai against the range adrpy-tui declares (ADR0003V01)."""

import re
from importlib.metadata import PackageNotFoundError, requires, version

from adrpy_tui.core.text import visible

NOT_INSTALLED = "unknown (not installed)"


def installed_version(distribution):
    """Its version, or NOT_INSTALLED -- also when its metadata is damaged
    (not UTF-8, no Version): it is shown, never allowed to stop the TUI."""
    try:
        # Shown as it is (the header, --version): never acting on the terminal.
        return visible(version(distribution) or NOT_INSTALLED)
    except (PackageNotFoundError, ValueError, OSError):
        return NOT_INSTALLED


def adrpy_range():
    """The adrpy-ai range of this adrpy-tui's metadata -- pyproject.toml's,
    as installed ("<0.2,>=0.1.dev0"); "" when there is none."""
    try:
        declared = requires("adrpy-tui") or []
    except (PackageNotFoundError, ValueError, OSError):  # damaged metadata, as installed_version
        return ""
    for requirement in declared:
        name = re.match(r"[A-Za-z0-9._-]+", requirement)
        if name and name.group(0).lower().replace("_", "-") == "adrpy-ai" and ";" not in requirement:
            return visible(requirement[name.end():].strip().strip("()"))
    return ""


def _release(text):
    numbers = re.match(r"\d+(?:\.\d+)*", str(text or "").strip())
    if not numbers:
        raise ValueError(f"not a version: {text!r}")
    return tuple(int(part) for part in numbers.group(0).split("."))


def _compare(first, second):
    width = max(len(first), len(second))
    first, second = first + (0,) * (width - len(first)), second + (0,) * (width - len(second))
    return (first > second) - (first < second)


def within(found, specifier):
    """Whether version `found` is in `specifier`, made of ">=X.devN" and
    "<Y" only -- the range's own shape: a floor's development builds are
    in, a ceiling's are out (PEP 440), so the release numbers decide."""
    for clause in filter(None, (clause.strip() for clause in specifier.split(","))):
        if clause.startswith(">="):
            floor = clause[2:]
            if not re.fullmatch(r"\d+(\.\d+)*\.dev0", floor):
                raise ValueError(f"unsupported floor: {clause}")
            if _compare(_release(found), _release(floor)) < 0:
                return False
        elif clause.startswith("<") and not clause.startswith("<="):
            if _compare(_release(found), _release(clause[1:])) >= 0:
                return False
        else:
            raise ValueError(f"unsupported clause: {clause}")
    return True


_PEP440 = re.compile(r"(\d+(?:\.\d+)*)(?:(a|b|rc)(\d+))?(?:\.post(\d+))?(?:\.dev(\d+))?(?:\+[A-Za-z0-9.]+)?", re.ASCII)
# Longer than any real version: one from PyPI past this is not shown.
_LONGEST = 64


def order(text):
    """A key that sorts versions as PEP 440 does, for the normalized forms
    PyPI and setuptools-scm write (a local part is ignored), in ASCII digits
    and at most 64 characters; ValueError for any other text."""
    text = str(text).strip() if text is not None else ""
    found = _PEP440.fullmatch(text) if len(text) <= _LONGEST else None
    if not found:
        raise ValueError(f"not a version: {text!r}")
    numbers, kind, pre, post, dev = found.groups()
    release = tuple(int(part) for part in numbers.split("."))
    while len(release) > 1 and release[-1] == 0:
        release = release[:-1]
    if kind:
        stage = ({"a": 0, "b": 1, "rc": 2}[kind], int(pre))
    elif dev is not None and post is None:
        stage = (-1, 0)  # X.devN comes before X's alphas
    else:
        stage = (3, 0)
    return (release, stage, -1 if post is None else int(post), float("inf") if dev is None else int(dev))


def adrpy_outside_range():
    """(version found, range) when the installed adrpy-ai is outside the
    declared range; None when it is within, or not installed (the header
    says so already)."""
    specifier = adrpy_range()
    found = installed_version("adrpy-ai") or "unknown"
    if not specifier or found == NOT_INSTALLED:
        return None
    try:
        if within(found, specifier):
            return None
    except ValueError:
        pass  # a version that cannot be compared is named, never a refusal (ADR0003V01)
    clauses = sorted((clause.strip() for clause in specifier.split(",")), key=lambda clause: not clause.startswith(">"))
    return found, ", ".join(clauses)
