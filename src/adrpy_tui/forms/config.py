"""`config`: its own screen, the editor of the repository's
.adrpy.json (ui/config.py)."""

from adrpy_tui.core.config_fields import CONFIG_FIELDS

VIEW = "config"
PATH_FLAG = "path"
FIELDS = CONFIG_FIELDS
# Labels, names or folders may have changed: the repository is read again.
RELOADS_REPOSITORY = True
