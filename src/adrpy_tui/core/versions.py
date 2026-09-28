"""Installed versions, for the header and `adrpy-tui --version`."""

from importlib.metadata import PackageNotFoundError, version


def installed_version(distribution):
    try:
        return version(distribution)
    except PackageNotFoundError:
        return "unknown (not installed)"
