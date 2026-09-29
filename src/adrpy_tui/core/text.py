"""Text from files the TUI did not write, made safe to show.

Textual draws ESC as it is, so an escape sequence in a file name, a header
cell or a decision's content would reach the terminal (SECURITY.md)."""

import re
import unicodedata

# C0 and C1 control characters but tab and line feed.
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")
# The same, but a CR that starts a CRLF stays: for values adrpy returns,
# which may be written back (a template keeps its line endings).
_CONTROL_BUT_CRLF = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]|\r(?!\n)")


def _without_controls(text):
    return _CONTROL.sub("", text.replace("\r\n", "\n"))


def printable(text):
    """Text to show, with its line breaks as LF. A lone surrogate (a name
    that is not valid UTF-8) becomes U+FFFD: written to the terminal it
    cannot be encoded, and killed the thread that draws the screen."""
    return "".join("\ufffd" if unicodedata.category(c) == "Cs" else c for c in _without_controls(text))


def visible(text):
    """A name, a path or a command line to show: `printable`, and every
    character that changes how the rest of the line reads without showing
    itself -- a bidirectional override, a zero-width one, a line
    separator (Unicode Cf, Zl, Zp), a lone surrogate (Cs) -- written out
    as <U+XXXX>, so "abc<U+202E>dm.txt" is not read as "abctxt.md". Not for
    a decision's own text, where such a character may be meant."""
    return "".join(f"<U+{ord(c):04X}>" if unicodedata.category(c) in ("Cf", "Zl", "Zp", "Cs") else c
                   for c in _without_controls(text))


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
