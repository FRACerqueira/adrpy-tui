"""The forms and menus against the installed adrpy (ADR004V01)."""

import pytest

from adrpy_tui.core.registry import ADRPY_COMMANDS, FORMS, SKILLS_COMMANDS, walk

# Commands whose form is not written yet: listed in the menu, disabled.
# Shrinks to nothing as the forms are written.
PENDING = set()
HELP_COMMANDS = {"help", "skills:help"}


def _listed(client, program):
    result = client.run(program, ("--full",))
    assert result.success, result
    return {command["name"]: command for command in result.data["commands"]}


@pytest.fixture(scope="module")
def contracts():
    from adrpy_tui.core.client import Client

    client = Client()
    adrpy = _listed(client, "help")
    skills = {f"skills:{name}": contract for name, contract in _listed(client, "skills:help").items()}
    return {**adrpy, **skills}


def test_the_registry_knows_every_command_of_both_programs(contracts):
    assert set(ADRPY_COMMANDS) | set(SKILLS_COMMANDS) == set(contracts)


def test_every_command_is_reachable_from_the_menu_and_has_its_help(contracts):
    actions = {item.command for item in walk() if item.command and not item.shows_help}
    helps = {item.command for item in walk() if item.shows_help}
    assert actions == set(contracts) - HELP_COMMANDS
    assert helps == set(contracts)


def test_the_commands_without_a_form_are_exactly_the_pending_ones(contracts):
    assert set(contracts) - HELP_COMMANDS - set(FORMS) == PENDING


def test_a_decision_s_actions_are_the_commands_that_take_its_state():
    from adrpy_tui.core.decisions import ACCEPTED, INVALID, MIGRATED, PROPOSED, REJECTED, SUPERSEDED
    from adrpy_tui.core.registry import commands_taking

    assert commands_taking(PROPOSED) == ["approve", "reject"]
    assert commands_taking(ACCEPTED) == ["undo", "version", "revise", "supersede"]
    assert commands_taking(REJECTED) == ["undo", "version", "revise"]
    assert commands_taking(MIGRATED) == ["approve", "reject", "version", "revise", "supersede"]
    assert commands_taking(SUPERSEDED) == commands_taking(INVALID) == []


@pytest.mark.parametrize("command", sorted(FORMS))
def test_every_form_has_the_same_flags_as_its_command(command, contracts):
    form = FORMS[command]
    arguments = {argument["name"]: argument for argument in contracts[command]["arguments"]}
    flags = {field.flag: field for field in form.FIELDS if not field.local}
    not_offered = set(getattr(form, "NOT_OFFERED", {}))
    assert set(arguments) == set(flags) | ({form.PATH_FLAG} if form.PATH_FLAG else set()) | not_offered
    for name, field in flags.items():
        assert field.required == arguments[name]["required"], name
    # PATH_FLAG is always sent: adrpy requires it; adrpy-skills does not (its
    # default is the current folder).
    if form.PATH_FLAG and not command.startswith("skills:"):
        assert arguments[form.PATH_FLAG]["required"]
