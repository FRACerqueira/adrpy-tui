"""Form fields: what a form asks for, how a value is checked before running,
and how the values become adrpy flags.

The checks only spare a round trip for an obvious mistake; adrpy's own
failure code stays the final word (ADR001V01). A field's label is the
language-pack key `field.<flag>`.
"""

from dataclasses import dataclass
from datetime import date

from adrpy_tui.core.files import is_file

# Characters adrpy refuses in a header-table cell, and additionally in a
# title, which also lands in a file name (`adrpy help new`).
HEADER_FORBIDDEN = "|"
TITLE_FORBIDDEN = '|<>:"/\\?*'


@dataclass(frozen=True)
class Field:
    flag: str
    # "text", "date", "switch", "decision", "choice" (one of `choices`),
    # "language" (one of adrpy's languages), "file" (an existing file's
    # path), "multi" (any of `choices`, sent comma-separated; none: adrpy's
    # default, every one), "select" (one of `choices`), "multiline"; in the
    # config editors also "bool" ('true'/'false')
    kind: str
    required: bool = False
    forbidden: str = ""
    # Header key of `explore`'s decisions whose existing values are offered
    # as suggestions ("scope", "domain").
    suggest_from: str | None = None
    # "decision": the states (core/decisions.py) the command takes.
    eligible: tuple = ()
    # "date": header dates of the chosen decision; the first it has is the
    # earliest allowed, e.g. ("date_update", "date_create") for "its last
    # update, or its creation if never updated".
    not_before: tuple = ()
    # Header key of the chosen decision copied into the field once chosen,
    # as adrpy's own default for it ("scope", "domain").
    prefill_from: str | None = None
    # Key of the chosen decision shown as the field's placeholder: adrpy's
    # default when the field is left empty ("title").
    default_from: str | None = None
    # "choice": the values, the first one chosen at first.
    choices: tuple = ()
    # (flag, value) or (flag, (value, ...)): shown, checked and sent only
    # while that field holds that value (or one of them).
    shown_when: tuple | None = None
    # A regular expression the whole value must match as it is typed
    # (kebab-case, digits); characters that don't fit can't be typed.
    restrict: str | None = None
    # Required while shown, though adrpy itself takes the flag as optional.
    required_if_shown: bool = False
    # A field of the screen only, never sent as a flag (it chooses which
    # other fields are shown).
    local: bool = False
    # The config editors (core/config_fields.py): the field's group, its
    # longest value, and whether adrpy refuses changing it once decisions
    # exist.
    group: str | None = None
    max_length: int | None = None
    guarded: bool = False


def shown(field, values):
    if field.shown_when is None:
        return True
    flag, wanted = field.shown_when
    return values.get(flag) in (wanted if isinstance(wanted, tuple) else (wanted,))


def problem(field, value, decision=None):
    """Why a value can't be sent as is, as a (language-pack key, params)
    pair, or None. `decision` is the one the form's decision field holds,
    for a date that can't be before one of its own dates."""
    if field.kind in ("switch", "choice", "language", "select", "multi"):
        return None
    if not value.strip():
        if field.required or field.required_if_shown:
            return "problem.required", {}
        if value:
            return "problem.blank", {}
        return None
    for char in field.forbidden:
        if char in value:
            return "problem.forbidden", {"char": char}
    if field.kind == "file" and not is_file(value):
        return "problem.file_missing", {"path": value}
    if field.kind == "date":
        try:
            day = date.fromisoformat(value)
        except ValueError:
            return "problem.date_format", {}
        if day > date.today():
            return "problem.date_future", {}
        header = (decision or {}).get("header") or {}
        earliest = next((header[key] for key in field.not_before if header.get(key)), None)
        if earliest and day < date.fromisoformat(earliest):
            return "problem.date_before", {"date": earliest}
    return None


def build_flags(form, repo, values):
    """The flags for a form's values: the repository first, then every
    field in order; an empty value or an off switch is left out, so adrpy
    applies its own default."""
    flags = [f"--{form.PATH_FLAG}", str(repo)] if form.PATH_FLAG else []
    for field in form.FIELDS:
        if field.local or not shown(field, values):
            continue
        value = values.get(field.flag)
        if field.kind == "switch":
            if value:
                flags.append(f"--{field.flag}")
        elif value:
            flags += [f"--{field.flag}", value]
    return flags
