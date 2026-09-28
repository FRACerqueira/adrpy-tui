"""Maps each command to its form module (one module per command,
ADR004V01), and lays out the menus that reach them.

An item's title and description are language-pack keys derived from its id
(`menu.<id>`, `menu.<id>.description`), except for the help items, which
are named after the command itself.
"""

from dataclasses import dataclass

from adrpy_tui.forms import new as new_form

FORMS = {
    "new": new_form,
}

# Every command of both programs, as `adrpy help` and `adrpy-skills help`
# list them; tests/test_registry.py checks these against the installed ones.
ADRPY_COMMANDS = (
    "help", "init", "explore", "check", "new", "approve", "reject", "undo", "supersede",
    "version", "revise", "migrate", "config", "installconfig", "log",
)
SKILLS_COMMANDS = ("skills:help", "skills:install", "skills:list", "skills:remove")


@dataclass(frozen=True)
class Item:
    id: str
    command: str | None = None
    needs_repo: bool = False
    shows_help: bool = False
    submenu: tuple = ()


def command_name(command):
    """How a person types the command: `adrpy new`, `adrpy-skills list`."""
    if command.startswith("skills:"):
        return f"adrpy-skills {command[len('skills:'):]}"
    return f"adrpy {command}"


def _group(id, commands, needs_repo=False):
    return Item(id, needs_repo=needs_repo, submenu=tuple(
        Item(f"{id}.{command.replace('skills:', '')}", command=command, needs_repo=needs_repo) for command in commands
    ))


MAIN_MENU = Item("main", submenu=(
    _group("decisions", ("new", "approve", "reject", "undo", "version", "revise", "supersede"), needs_repo=True),
    _group("explore", ("explore", "check"), needs_repo=True),
    _group("log", ("log",), needs_repo=True),
    Item("repository", submenu=(
        Item("repository.init", command="init"),
        Item("repository.config", command="config", needs_repo=True),
        Item("repository.migrate", command="migrate", needs_repo=True),
    )),
    _group("install", ("installconfig",)),
    _group("skills", ("skills:list", "skills:install", "skills:remove")),
    Item("help", submenu=tuple(
        Item(f"help.{command}", command=command, shows_help=True) for command in (*ADRPY_COMMANDS, *SKILLS_COMMANDS)
    )),
    Item("change-repository"),
    Item("language"),
    Item("appearance"),
    Item("exit"),
))


def walk(menu=MAIN_MENU):
    """Every item under `menu`, depth first."""
    for item in menu.submenu:
        yield item
        yield from walk(item)
