"""`supersede` form: marks an Accepted decision (or a migrated placeholder)
Superseded and creates its successor, status Proposed."""

from adrpy_tui.core.decisions import ACCEPTED, MIGRATED
from adrpy_tui.core.fields import HEADER_FORBIDDEN, TITLE_FORBIDDEN, Field

PATH_FLAG = None
FIELDS = (
    Field("file", "decision", required=True, eligible=(ACCEPTED, MIGRATED)),
    Field("title", "text", forbidden=TITLE_FORBIDDEN, default_from="title"),
    Field("domain", "text", forbidden=HEADER_FORBIDDEN, suggest_from="domain", prefill_from="domain"),
    Field("scope", "text", forbidden=HEADER_FORBIDDEN, suggest_from="scope", prefill_from="scope"),
    Field("refdate", "date", not_before=("date_update", "date_create")),
)
