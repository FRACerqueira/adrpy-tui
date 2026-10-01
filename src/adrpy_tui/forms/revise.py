"""`revise` form: a wording-fix revision of an Accepted or Rejected
decision (or a migrated placeholder), status Proposed."""

from adrpy_tui.core.decisions import ACCEPTED, MIGRATED, REJECTED
from adrpy_tui.core.fields import Field

PATH_FLAG = None
FIELDS = (
    Field("file", "decision", required=True, eligible=(ACCEPTED, REJECTED, MIGRATED)),
    Field("refdate", "date", not_before=("date_update", "date_create")),
    # The decision created opens in the editor once the command succeeds (ADR0007V01).
    Field("edit", "switch", local=True, needs_editor=True),
)
