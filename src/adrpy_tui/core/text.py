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
    cannot be encoded, and would kill the thread that draws the screen."""
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


# The controls that reorder what is drawn: embeddings, overrides, isolates
# and marks. The other format characters (Cf) are part of a language's
# text -- a Persian ZWNJ, an emoji's ZWJ, a BOM -- and a field keeps them;
# the confirmation writes them out (`visible`).
_BIDI_CONTROLS = frozenset("‪‫‬‭‮⁦⁧⁨⁩‎‏؜")


def field_text(text, multiline=False):
    """What a text field keeps (ui/inputs.py): no control character, no
    lone surrogate, no line or paragraph separator (Zl, Zp), no
    bidirectional control, no tag character (U+E0000-E007F: text nobody
    sees, smuggled into a decision an AI agent reads later). A multi-line field also keeps its tabs and line
    breaks, a CR only as part of a CRLF (a template keeps its line endings)."""
    kept = []
    for index, char in enumerate(text):
        if multiline and (char in "\t\n" or char == "\r" and text[index + 1:index + 2] == "\n"):
            kept.append(char)
        elif (char not in _BIDI_CONTROLS and not "\U000e0000" <= char <= "\U000e007f"
              and unicodedata.category(char) not in ("Cc", "Cs", "Zl", "Zp")):
            kept.append(char)
    return "".join(kept)


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
