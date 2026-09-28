"""Our screens and widgets must not reuse an attribute name Textual already
gives them: FormScreen once stored its own `_running` flag over Textual's
(MessagePump._running, True while the widget runs), which silently turned
Ctrl+R into a no-op."""

import ast
import inspect
import textwrap

import pytest
from textual.app import App
from textual.dom import DOMNode

import importlib
import pkgutil

import adrpy_tui.ui

# Every module of the UI, found rather than listed, so a new one is never
# left out.
MODULES = tuple(importlib.import_module(f"adrpy_tui.ui.{info.name}")
                for info in pkgutil.iter_modules(adrpy_tui.ui.__path__))


def _ours():
    for module in MODULES:
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, (DOMNode, App)) and cls.__module__ == module.__name__:
                yield cls


def _textual_names(cls):
    """Textual's class attributes and the ones its classes set on self (as
    MessagePump's `_running`, set in its __init__)."""
    names = set()
    for base_cls in cls.__mro__[1:]:
        if base_cls.__module__.startswith(("textual", "rich")):
            names |= set(vars(base_cls))
            try:
                names |= _assigned_in_init(base_cls)
            except (OSError, TypeError):  # no source to read
                pass
    return names


def _assigned_in_init(cls):
    """Every `self.<name> = ...` in the class's own code."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(cls)))
    names = set()
    for node in ast.walk(tree):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(
            node, (ast.AugAssign, ast.AnnAssign)) else []
        for target in targets:
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                names.add(target.attr)
    return names


@pytest.mark.parametrize("cls", list(_ours()), ids=lambda cls: cls.__name__)
def test_no_attribute_of_ours_shadows_one_of_textual(cls):
    textual = _textual_names(cls)
    instance_names = _assigned_in_init(cls)
    # Deliberate: Textual's own attributes, set for what Textual does with
    # them (the app's theme, a screen's key hints).
    allowed = {"theme", "HINTS"}
    clashes = {name for name in instance_names if name in textual and name not in allowed}
    assert not clashes, f"{cls.__name__} reuses Textual's {sorted(clashes)}"


class _LikeTheOldFormScreen(DOMNode):
    def __init__(self):
        super().__init__()
        self._running = False  # the bug this file exists for


def test_the_check_catches_the_bug_it_was_written_for():
    assert "_running" in _assigned_in_init(_LikeTheOldFormScreen)
    assert "_running" in _textual_names(_LikeTheOldFormScreen)
