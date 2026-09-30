"""`adrpy-skills remove` form: removes the bundled AI-agent skills, for one or
more providers, in the repository or (claude only) the user's home."""

from adrpy_tui.core.fields import Field

PROVIDERS = ("claude", "cursor", "copilot", "agentsmd")
SKILLS = ("adrpy", "decision-log", "pre-release-audit")

PATH_FLAG = "path"
FIELDS = (
    # Nothing chosen: every one (adrpy-skills' own default).
    Field("provider", "multi", choices=PROVIDERS),
    Field("skill", "multi", choices=SKILLS),
    Field("target", "choice", choices=("project", "global")),
    Field("force", "switch"),
    Field("allow-external-links", "switch"),
)
