"""Text from files the TUI did not write, made safe to show.

Textual draws ESC as it is, so an escape sequence in a file name, a header
cell or a decision's content would reach the terminal (SECURITY.md)."""

import re

# C0 and C1 control characters but tab and line feed.
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")
# The same, but a CR that starts a CRLF stays: for values adrpy returns,
# which may be written back (a template keeps its line endings).
_CONTROL_BUT_CRLF = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]|\r(?!\n)")


def printable(text):
    """Text to show, with its line breaks as LF."""
    return _CONTROL.sub("", text.replace("\r\n", "\n"))


def safe(text):
    """Text as adrpy returned it, without what could act on the terminal;
    tabs and line breaks, CRLF included, are kept."""
    return _CONTROL_BUT_CRLF.sub("", text)


def safe_json(value):
    """`safe` on every string of a decoded JSON value."""
    if isinstance(value, str):
        return safe(value)
    if isinstance(value, list):
        return [safe_json(item) for item in value]
    if isinstance(value, dict):
        return {safe(key): safe_json(item) for key, item in value.items()}
    return value
