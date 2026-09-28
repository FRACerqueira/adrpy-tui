"""`reject` form: marks a Proposed decision (or a migrated placeholder) Rejected."""

from adrpy_tui.core.decisions import MIGRATED, PROPOSED
from adrpy_tui.core.fields import Field

PATH_FLAG = None
FIELDS = (
    Field("file", "decision", required=True, eligible=(PROPOSED, MIGRATED)),
    Field("refdate", "date", not_before=("date_create",)),
)
