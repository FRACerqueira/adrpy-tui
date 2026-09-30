"""`undo` form: reverts an Accepted or Rejected decision to Proposed."""

from adrpy_tui.core.decisions import ACCEPTED, REJECTED
from adrpy_tui.core.fields import Field

PATH_FLAG = None
FIELDS = (
    Field("file", "decision", required=True, eligible=(ACCEPTED, REJECTED)),
)
