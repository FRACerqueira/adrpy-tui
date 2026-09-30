"""`version` form: a new major version of an Accepted or Rejected decision
(or a migrated placeholder), status Proposed."""

from adrpy_tui.core.decisions import ACCEPTED, MIGRATED, REJECTED
from adrpy_tui.core.fields import HEADER_FORBIDDEN, Field

PATH_FLAG = None
FIELDS = (
    Field("file", "decision", required=True, eligible=(ACCEPTED, REJECTED, MIGRATED)),
    Field("domain", "text", forbidden=HEADER_FORBIDDEN, suggest_from="domain", prefill_from="domain"),
    Field("scope", "text", forbidden=HEADER_FORBIDDEN, suggest_from="scope", prefill_from="scope"),
    Field("refdate", "date", not_before=("date_update", "date_create")),
    Field("empty", "switch"),
)
