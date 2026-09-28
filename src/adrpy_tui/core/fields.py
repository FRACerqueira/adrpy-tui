"""Form fields: what a form asks for, how a value is checked before running,
and how the values become adrpy flags.

The checks only spare a round trip for an obvious mistake; adrpy's own
failure code stays the final word (ADR001V01). A field's label is the
language-pack key `field.<flag>`.
"""

from dataclasses import dataclass
from datetime import date

# Characters adrpy refuses in a header-table cell, and additionally in a
# title, which also lands in a file name (`adrpy help new`).
HEADER_FORBIDDEN = "|"
TITLE_FORBIDDEN = '|<>:"/\\?*'


@dataclass(frozen=True)
class Field:
    flag: str
    kind: str  # "text", "date" or "switch"
    required: bool = False
    forbidden: str = ""
    # Header key of `explore`'s decisions whose existing values are offered
    # as suggestions ("scope", "domain").
    suggest_from: str | None = None


def problem(field, value):
    """Why a value can't be sent as is, as a (language-pack key, params)
    pair, or None."""
    if field.kind == "switch":
        return None
    if not value.strip():
        if field.required:
            return "problem.required", {}
        if value:
            return "problem.blank", {}
        return None
    for char in field.forbidden:
        if char in value:
            return "problem.forbidden", {"char": char}
    if field.kind == "date":
        try:
            day = date.fromisoformat(value)
        except ValueError:
            return "problem.date_format", {}
        if day > date.today():
            return "problem.date_future", {}
    return None


def build_flags(form, repo, values):
    """The flags for a form's values: the repository first, then every
    field in order; an empty value or an off switch is left out, so adrpy
    applies its own default."""
    flags = [f"--{form.PATH_FLAG}", str(repo)] if form.PATH_FLAG else []
    for field in form.FIELDS:
        value = values.get(field.flag)
        if field.kind == "switch":
            if value:
                flags.append(f"--{field.flag}")
        elif value:
            flags += [f"--{field.flag}", value]
    return flags
