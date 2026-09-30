import pytest

from adrpy_tui.core import keys


def _texts(key, **params):
    return {"keyname.ctrl": "Strg", "keyname.alt": "Alt", "keyname.shift": "Umschalt"}[key]


@pytest.mark.parametrize("key, shown", [
    ("ctrl+r", "Strg+R"),
    ("f3", "F3"),
    ("ctrl+shift+f5", "Strg+Umschalt+F5"),
    ("alt+page_down", "Alt+Page Down"),
])
def test_display_names_a_key_in_the_interface_s_language(key, shown):
    assert keys.display(key, _texts) == shown


@pytest.mark.parametrize("key, expected", [
    ("f5", None),
    ("ctrl+e", None),
    ("alt+x", None),
    ("escape", "keys.reserved"),
    ("ctrl+c", "keys.reserved"),
    ("tab", "keys.reserved"),
    ("x", "keys.types"),  # would be typed into a field
    ("super+x", "keys.unknown"),
    ("ctrl+", "keys.unknown"),
])
def test_problem(key, expected):
    assert keys.problem(key) == expected


def test_every_default_key_can_be_given_to_its_action():
    assert all(keys.problem(key) is None for key in keys.ACTIONS.values())


def test_keymap_uses_the_binding_ids():
    assert keys.keymap({"run": "f5"}) == {"adrpy.run": "f5"}
