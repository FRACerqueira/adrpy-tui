"""`installconfig`: its own screen, the editor of the per-user install-level
config (ui/config.py); `seed` and `language` create or replace it whole."""

from adrpy_tui.core.config_fields import CONFIG_FIELDS
from adrpy_tui.core.fields import Field

VIEW = "installconfig"
PATH_FLAG = None
FIELDS = CONFIG_FIELDS + (
    Field("seed", "file"),
    Field("language", "language"),
)
