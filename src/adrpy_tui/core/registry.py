"""Maps each command to its form module (one module per command,
ADR0004V01), and lays out the menus that reach them.

An item's title and description are language-pack keys derived from its id
(`menu.<id>`, `menu.<id>.description`), except for the help items, which
are named after the command itself.
"""

from dataclasses import dataclass

from adrpy_tui.forms import approve as approve_form
from adrpy_tui.forms import check as check_form
from adrpy_tui.forms import config as config_form
from adrpy_tui.forms import explore as explore_form
from adrpy_tui.forms import init as init_form
from adrpy_tui.forms import installconfig as installconfig_form
from adrpy_tui.forms import log as log_form
from adrpy_tui.forms import migrate as migrate_form
from adrpy_tui.forms import new as new_form
from adrpy_tui.forms import reject as reject_form
from adrpy_tui.forms import revise as revise_form
from adrpy_tui.forms import skills_install, skills_list, skills_remove
from adrpy_tui.forms import supersede as supersede_form
from adrpy_tui.forms import undo as undo_form
from adrpy_tui.forms import version as version_form

FORMS = {
    "new": new_form,
    "approve": approve_form,
    "reject": reject_form,
    "undo": undo_form,
    "version": version_form,
    "revise": revise_form,
    "supersede": supersede_form,
    "explore": explore_form,
    "check": check_form,
    "init": init_form,
    "config": config_form,
    "installconfig": installconfig_form,
    "migrate": migrate_form,
    "log": log_form,
    "skills:list": skills_list,
    "skills:install": skills_install,
    "skills:remove": skills_remove,
}


def destroys(command, flags, configured):
    """Whether running `command` with `flags` destroys something or is hard
    to undo -- its confirmation's Yes is red: a decision rejected or
    superseded, skills removed, a repository's config replaced, a skill's
    file changed by hand overwritten."""
    if command in ("reject", "supersede", "skills:remove"):
        return True
    if command == "init":  # adrpy replaces an existing config only from a seed file
        return configured and "--seed" in flags
    return command == "skills:install" and "--force" in flags


def commands_taking(decision_state):
    """The commands whose decision field takes a decision in this state, in
    menu order: the actions a decision's detail offers."""
    return [
        command
        for command, form in FORMS.items()
        if any(field.kind == "decision" and decision_state in field.eligible for field in form.FIELDS)
    ]

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
    Item("log", needs_repo=True, submenu=(
        Item("log.log", command="log", needs_repo=True),
        Item("log.browse", needs_repo=True),
    )),
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
    Item("keys"),
    Item("exit"),
))


def walk(menu=MAIN_MENU):
    """Every item under `menu`, depth first."""
    for item in menu.submenu:
        yield item
        yield from walk(item)
