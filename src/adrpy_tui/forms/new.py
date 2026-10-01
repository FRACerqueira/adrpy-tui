"""`new` form: creates a decision, status Proposed."""

from adrpy_tui.core.fields import HEADER_FORBIDDEN, TITLE_FORBIDDEN, Field

PATH_FLAG = "path"
FIELDS = (
    Field("title", "text", required=True, forbidden=TITLE_FORBIDDEN),
    Field("domain", "text", forbidden=HEADER_FORBIDDEN, suggest_from="domain"),
    Field("scope", "text", forbidden=HEADER_FORBIDDEN, suggest_from="scope"),
    Field("refdate", "date"),
    # The decision created opens in the editor once the command succeeds (ADR0007V01).
    Field("edit", "switch", local=True, needs_editor=True),
)
