"""Reading `explore`'s decisions: which state each one is in, and how the
repository labels it.

States are canonical (adrpy-ai ADR0004V02's hidden marker makes `explore`
report `Proposed`, `Accepted`, ... whatever labels a repository
configures); the labels are for display only (ADR0001V01).
"""

from pathlib import Path

PROPOSED = "Proposed"
ACCEPTED = "Accepted"
REJECTED = "Rejected"
SUPERSEDED = "Superseded"
# A migrated decision whose Created cell is blank: approve and reject take it.
MIGRATED = "migrated"
# A header adrpy can't read; no command takes it.
INVALID = "invalid"

_LABEL_FIELDS = {
    PROPOSED: "statusnew",
    ACCEPTED: "statusacc",
    REJECTED: "statusrej",
    SUPERSEDED: "statussup",
    MIGRATED: "headermigrated",
}


def state(decision):
    """The decision's current state: its latest status, or MIGRATED, or
    INVALID."""
    header = decision.get("header")
    if not header or not header.get("is_valid"):
        return INVALID
    current = header.get("status_change") or header.get("status_update") or header.get("status_create")
    if current:
        return current
    return MIGRATED if header.get("is_migrated") else INVALID


# The header cells the screens read as text: another type (a number, a
# list) is read as no value.
_HEADER_TEXTS = ("status_create", "status_update", "status_change", "scope", "domain",
                 "date_create", "date_update", "superseded_by_file")


def listed(data):
    """`explore`'s decisions in the shape every screen reads them: adrpy's
    JSON is read, not trusted (the screens filter and sort them in their own
    handlers, where no failure is contained). One whose name or path is not
    text is left out: nothing could be shown or run for it."""
    decisions = data.get("decisions")
    kept = []
    for decision in decisions if isinstance(decisions, list) else []:
        if not isinstance(decision, dict):
            continue
        if not all(isinstance(decision.get(key), str) and decision[key] for key in ("filename", "path")):
            continue
        header = decision.get("header")
        header = dict(header) if isinstance(header, dict) else {}
        for key in _HEADER_TEXTS:
            if not isinstance(header.get(key), str):
                header[key] = None
        for key in ("is_valid", "is_migrated"):
            header[key] = header.get(key) is True
        kept.append({**decision, "header": header})
    return kept


def repository_config(data):
    """`adrpy config`'s `config`, or {} when it is not an object."""
    config = data.get("config")
    return config if isinstance(config, dict) else {}


TOP = "."  # a decision straight in the decisions folder


def folder_of(path, decisions_folder):
    """The folder of a decision relative to the decisions folder, "." for one
    straight in it: adrpy finds decisions in its subfolders too."""
    parent = Path(path).parent
    try:
        relative = parent.relative_to(decisions_folder)
    except ValueError:
        return parent.name
    return relative.as_posix() if relative.parts else TOP


def setting(config, field, default):
    """A text setting of `adrpy config`'s data; `default` when it is empty or
    of another type (a number, a list): adrpy's JSON is read, not trusted."""
    value = config.get(field)
    return value if isinstance(value, str) and value else default


def labels(config):
    """Each state's label in this repository, from `adrpy config`'s data."""
    return {state: setting(config, field, state) for state, field in _LABEL_FIELDS.items()}
