"""The fields of adr-config.adrplus, as the `config` and `installconfig`
editors show them: their group, their editor, and the limits `adrpy help
config` states (adrpy's own refusal stays the final word)."""

from adrpy_tui.core.fields import Field

# The groups, in the order the editor lists them.
GROUPS = ("folders", "names", "status", "header", "template", "migration", "plugins")

_STATUS = "|()<:"  # also '<!--' and '-->'; adrpy says so if they are typed
_HEADER = "|"


def _text(flag, group, max_length, forbidden=_HEADER, guarded=False):
    return Field(flag, "text", forbidden=forbidden, group=group, max_length=max_length, guarded=guarded)


def _select(flag, group, choices, guarded=False):
    return Field(flag, "select", choices=choices, group=group, guarded=guarded)


CONFIG_FIELDS = (
    _text("folderadr", "folders", 50, forbidden="", guarded=True),
    _text("folderlog", "folders", 50, forbidden="", guarded=True),
    _text("prefix", "names", 5, forbidden="", guarded=True),
    _select("separator", "names", ("-", "_", "."), guarded=True),
    _select("casetransform", "names", ("CamelCase", "PascalCase", "SnakeCase", "KebabCase")),
    _select("lenseq", "names", ("3", "4", "5", "6")),
    _select("lenversion", "names", ("2", "3", "4")),
    _select("lenrevision", "names", ("0", "1", "2", "3")),
    _text("statusnew", "status", 25, forbidden=_STATUS, guarded=True),
    _text("statusacc", "status", 25, forbidden=_STATUS, guarded=True),
    _text("statusrej", "status", 25, forbidden=_STATUS, guarded=True),
    _text("statussup", "status", 25, forbidden=_STATUS, guarded=True),
    _text("headerdisclaimer", "header", 100),
    _text("headertitlefile", "header", 40),
    _text("headerversion", "header", 40),
    _text("headerrevision", "header", 40),
    _text("headerscope", "header", 40),
    _text("headerdomain", "header", 40),
    _text("headertitlestatuscreated", "header", 40),
    _text("headertitlestatuschanged", "header", 40),
    _text("headertitlestatussuperseded", "header", 40),
    _text("headertablefields", "header", 40, guarded=True),
    _text("headertablevalues", "header", 40),
    _text("headermigrated", "header", 40),
    Field("template", "multiline", group="template", max_length=10000),
    _text("migrationpattern", "migration", 40, forbidden="", guarded=True),
    Field("disableplugins", "bool", group="plugins"),
)
