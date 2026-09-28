"""`log` form: a decision-log entry, the lighter-weight sibling of an ADR.
The fields a classification takes appear with it: front, severity,
resolution and round for audit-finding and doc-drift, reopenwhen for
deferred."""

from adrpy_tui.core.fields import HEADER_FORBIDDEN, Field

FINDINGS = ("audit-finding", "doc-drift")
KEBAB = r"[a-z0-9-]*"

PATH_FLAG = "path"
FIELDS = (
    Field("classification", "select", required=True, choices=(
        "scope-note", "audit-finding", "doc-drift", "deferred", "accepted-divergence", "retraction",
        "risk-accepted", "investigation", "process-exception",
    )),
    Field("scope", "text", required=True, restrict=KEBAB),
    Field("slug", "text", required=True, restrict=KEBAB),
    Field("summary", "text", required=True, forbidden=HEADER_FORBIDDEN),
    Field("body", "multiline", required=True),
    Field("refdate", "date"),
    Field("front", "text", forbidden=HEADER_FORBIDDEN, shown_when=("classification", FINDINGS), required_if_shown=True),
    Field("severity", "select", choices=("Low", "Medium", "High"), shown_when=("classification", FINDINGS)),
    Field("resolution", "select", choices=("Direct", "Escalated", "Retraction"), shown_when=("classification", FINDINGS)),
    Field("round", "text", restrict=r"[0-9]*", shown_when=("classification", FINDINGS)),
    Field("reopenwhen", "text", forbidden=HEADER_FORBIDDEN, shown_when=("classification", "deferred"),
          required_if_shown=True),
)
