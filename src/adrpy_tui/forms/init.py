"""`init` form: initializes the current repository (another folder goes
through "Change repository"), from a language pack, the default, or a seed
file."""

from adrpy_tui.core.fields import Field

PATH_FLAG = "path"
# The repository is read again once this command succeeds.
RELOADS_REPOSITORY = True
FIELDS = (
    # A language pack; adrpy's default (the install-level config, or English
    # when there is none); or a config file. adrpy refuses a language while
    # an install-level config exists: its failure says so.
    Field("source", "choice", choices=("language", "default", "seed"), local=True),
    Field("language", "language", shown_when=("source", "language")),
    Field("seed", "file", shown_when=("source", "seed"), required_if_shown=True),
)
