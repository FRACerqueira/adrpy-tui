"""The legacy naming pattern `migrate` reads (N##:##T##[V##:##][R##:##][P##:##]):
the position and length of each part of a name without `.md`, positions
from 00. Built part by part by the migrate form; adrpy validates it (a
pattern reading part of a name twice is refused) and previews it."""

import re
from dataclasses import dataclass

# N: the number; T: where the title starts (it runs to the end); V, R, P:
# the optional version, revision and prefix.
PARTS = ("N", "T", "V", "R", "P")
REQUIRED = ("N", "T")

_PATTERN = re.compile(
    r"N(?P<N>\d{2}):(?P<Nl>\d{2})T(?P<T>\d{2})"
    r"(?:V(?P<V>\d{2}):(?P<Vl>\d{2}))?(?:R(?P<R>\d{2}):(?P<Rl>\d{2}))?(?:P(?P<P>\d{2}):(?P<Pl>\d{2}))?$"
)


@dataclass(frozen=True)
class Part:
    start: int
    length: int | None = None  # None for T, which runs to the end


def build(parts):
    """The pattern for {part: Part}; the optional parts only when given."""
    pattern = f"N{parts['N'].start:02}:{parts['N'].length:02}T{parts['T'].start:02}"
    for name in ("V", "R", "P"):
        if name in parts:
            pattern += f"{name}{parts[name].start:02}:{parts[name].length:02}"
    return pattern


def parse(pattern):
    """{part: Part} of a well-formed pattern, else None."""
    match = _PATTERN.match(pattern or "")
    if not match:
        return None
    parts = {"N": Part(int(match["N"]), int(match["Nl"])), "T": Part(int(match["T"]))}
    for name in ("V", "R", "P"):
        if match[name] is not None:
            parts[name] = Part(int(match[name]), int(match[f"{name}l"]))
    return parts


def read(stem, part):
    """What a part reads from a name without `.md`."""
    return stem[part.start:] if part.length is None else stem[part.start:part.start + part.length]


def propose(stem):
    """A first pattern for a name: its leading digits as the number, the
    title after the next character (`0001-use-postgres` -> N00:04T05)."""
    digits = len(stem) - len(stem.lstrip("0123456789"))
    length = max(digits, 1)
    title = length + 1 if len(stem) > length and not stem[length].isalnum() else length
    return {"N": Part(0, length), "T": Part(min(title, max(len(stem) - 1, 0)))}
