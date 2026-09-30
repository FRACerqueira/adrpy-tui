"""Appearance presets: the color of each role the screens use, on top of a
Textual base theme (the variables `$tui-*` of resources/app.tcss)."""

ROLES = (
    "tui-banner",     # banner, command started/finished
    "tui-info",       # info lines, key hints
    "tui-warning",    # warnings
    "tui-summary",    # summary, the command line to confirm
    "tui-help",       # command help
    "tui-error",      # errors
    "tui-result",     # a command's result
    "tui-value",      # typed values
    "tui-highlight",  # the highlighted item (menus, tables): its row
    "tui-cursor",     # the highlighted item's text; its row out of focus
)

DEFAULT_PRESET = "default"

PRESETS = {
    "default": {
        "base": "textual-dark",
        "primary": "#00509E",  # buttons: white text at 6.4:1
        "colors": {
            "tui-banner": "#FF8C00",
            "tui-info": "#808080",
            "tui-warning": "#FFD700",
            "tui-summary": "#FFDEAD",
            "tui-help": "#87CEEB",
            "tui-error": "#FF0000",
            "tui-result": "#FFFFFF",
            "tui-value": "#00FFFF",
            "tui-highlight": "#00FF00",
            "tui-cursor": "#303030",
        },
    },
    "light": {
        "base": "textual-light",
        "colors": {
            "tui-banner": "#8A4700",
            "tui-info": "#5F5F5F",
            "tui-warning": "#6E5700",
            "tui-summary": "#6B4E16",
            "tui-help": "#005F87",
            "tui-error": "#C00000",
            "tui-result": "#000000",
            "tui-value": "#006060",
            "tui-highlight": "#006400",
            "tui-cursor": "#C8E6C9",
        },
    },
    "high-contrast": {
        "base": "textual-dark",
        "primary": "#00509E",
        "colors": {
            "tui-banner": "#FFAF00",
            "tui-info": "#E0E0E0",
            "tui-warning": "#FFFF00",
            "tui-summary": "#FFFFFF",
            "tui-help": "#5FD7FF",
            "tui-error": "#FF5F5F",
            "tui-result": "#FFFFFF",
            "tui-value": "#FFFFFF",
            "tui-highlight": "#00FFFF",
            "tui-cursor": "#3A3A3A",
        },
    },
}


def preset_or_default(name):
    """`name` when it is a known preset (a state file may hold one from
    another version), else the default."""
    return name if name in PRESETS else DEFAULT_PRESET


def theme_name(preset):
    return f"adrpy-{preset}"
