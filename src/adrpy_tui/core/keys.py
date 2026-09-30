"""The interface's keys: the actions whose key can be changed, their
defaults, the keys that never change, and how a key is named on screen.

A configurable action is one Textual binding id everywhere it applies:
`run` confirms each screen's own action (run a form, save a config, migrate,
use a folder), so changing its key changes it on every screen."""

PREFIX = "adrpy."

# action -> default key (Textual's key names)
ACTIONS = {
    "run": "ctrl+r",
    "preview": "f3",
    "toggle": "f2",
}

# Keys no action can take: the ones every screen relies on, and the ones
# Textual itself keeps (ctrl+c, ctrl+q quit; ctrl+p opens its palette).
RESERVED = frozenset({
    "escape", "enter", "tab", "shift+tab", "up", "down", "left", "right", "pageup", "pagedown", "home", "end",
    "space", "backspace", "delete", "ctrl+c", "ctrl+q", "ctrl+p",
})

_MODIFIERS = ("ctrl", "alt", "shift")


def binding_id(action):
    return f"{PREFIX}{action}"


def problem(key):
    """Why `key` can't be given to an action, as a language-pack key, or None."""
    if key in RESERVED:
        return "keys.reserved"
    parts = key.split("+")
    modifiers, base = parts[:-1], parts[-1]
    if not base or any(modifier not in _MODIFIERS for modifier in modifiers):
        return "keys.unknown"
    if not modifiers and (len(base) == 1 or base in ("minus", "plus", "comma", "full_stop")):
        # A plain character would be typed into a field instead.
        return "keys.types"
    return None


def keymap(chosen):
    """Textual's keymap for the keys chosen, {action: key}."""
    return {binding_id(action): key for action, key in chosen.items()}


def display(key, texts):
    """A key as the key line names it: "Ctrl+R", "F3", "Strg+R" in German."""
    names = []
    for part in key.split("+"):
        if part in _MODIFIERS:
            names.append(texts(f"keyname.{part}"))
        elif len(part) == 1:
            names.append(part.upper())
        elif part.startswith("f") and part[1:].isdigit():
            names.append(part.upper())
        else:
            names.append(part.replace("_", " ").title())
    return "+".join(names)
