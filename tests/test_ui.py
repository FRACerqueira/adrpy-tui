"""The screens, driven headless through Textual's Pilot."""

import threading
from pathlib import Path

from textual.widgets import DataTable, Markdown, OptionList, Static

from adrpy_tui.core.state import UserState
from adrpy_tui.ui.app import AdrpyTui
from adrpy_tui.ui.confirm import ConfirmScreen
from adrpy_tui.ui.form import FormScreen
from adrpy_tui.ui.help import HelpScreen
from adrpy_tui.ui.language import LanguageScreen
from adrpy_tui.ui.menu import MenuScreen
from adrpy_tui.ui.result import ResultScreen

from conftest import FakeClient, run_app, settle

NOT_CONFIGURED = {"config": {"success": False, "code": "config-not-found", "detail": "no config"}}


def _options(screen):
    return screen.query_one("#options", OptionList)


def _highlighted_id(screen):
    options = _options(screen)
    return options.get_option_at_index(options.highlighted).id


def _text(screen, selector):
    return str(screen.query_one(selector, Static).render())


def test_first_run_starts_with_the_language_choice_and_remembers_it(tmp_path):
    state = UserState(tmp_path / "state" / "state.json")
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=state)

    async def scenario(pilot):
        assert isinstance(app.screen, LanguageScreen)
        languages = app.screen.query_one("#languages", OptionList)
        assert languages.option_count == 11
        languages.highlighted = languages.get_option_index("pt-br")
        await pilot.press("enter")
        await settle(pilot)
        assert isinstance(app.screen, MenuScreen)
        assert _text(app.screen, ".title") == "Menu principal"

    run_app(app, scenario)
    assert UserState(tmp_path / "state" / "state.json").language == "pt-br"


def test_the_language_menu_item_offers_back_on_top_of_the_languages(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        options = _options(app.screen)
        options.highlighted = options.get_option_index("language")
        await pilot.press("enter")
        assert isinstance(app.screen, LanguageScreen)
        languages = app.screen.query_one("#languages", OptionList)
        assert (languages.get_option_at_index(0).id, languages.option_count) == ("back", 12)
        assert languages.get_option_at_index(languages.highlighted).id == "en-us"  # the current one
        languages.highlighted = 0
        await pilot.press("enter")
        assert isinstance(app.screen, MenuScreen) and app.screen.menu.id == "main"

    run_app(app, scenario)
    assert user_state.language == "en-us"


def test_the_first_run_language_choice_has_no_back(tmp_path):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=UserState(tmp_path / "state.json"))

    async def scenario(pilot):
        languages = app.screen.query_one("#languages", OptionList)
        assert "back" not in {languages.get_option_at_index(i).id for i in range(languages.option_count)}

    run_app(app, scenario)


def test_a_stored_language_skips_the_choice(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        assert isinstance(app.screen, MenuScreen)
        assert _text(app.screen, ".title") == "Main menu"

    run_app(app, scenario)


def test_the_header_shows_the_banner_and_the_repository(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        rendered = " ".join(str(static.render()) for static in app.screen.query("AppHeader Static").results(Static))
        assert r"/_/   \_\____/|_| \_\    |_|    |_|" in rendered
        assert str(Path(tmp_path).resolve()) in rendered

    run_app(app, scenario)


def test_without_a_repository_the_groups_that_need_one_are_disabled(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(answers=NOT_CONFIGURED), user_state=user_state)

    async def scenario(pilot):
        options = _options(app.screen)
        disabled = {options.get_option_at_index(i).id for i in range(options.option_count) if options.get_option_at_index(i).disabled}
        assert {"decisions", "explore", "log"} <= disabled
        assert not {"repository", "help", "language", "exit"} & disabled
        assert app.repo_problem is None  # "no config" is not a problem to report

    run_app(app, scenario)


def test_a_config_that_cannot_be_read_is_reported_on_the_main_menu(tmp_path, user_state):
    answers = {"config": {"success": False, "code": "config-invalid-json", "detail": "Unexpected token"}}
    app = AdrpyTui(tmp_path, client=FakeClient(answers=answers), user_state=user_state)

    async def scenario(pilot):
        assert "Unexpected token" in _text(app.screen, ".error")

    run_app(app, scenario)


def test_the_last_selected_item_is_highlighted_again(tmp_path, user_state):
    user_state.remember("main", "explore")
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        assert _highlighted_id(app.screen) == "explore"

    run_app(app, scenario)


def test_a_remembered_item_that_no_longer_exists_is_ignored(tmp_path, user_state):
    user_state.remember("main", "an-item-from-an-older-version")
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        assert isinstance(app.screen, MenuScreen)
        assert _highlighted_id(app.screen) == "decisions"

    run_app(app, scenario)


def test_pending_commands_are_listed_but_disabled(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        await pilot.press("enter")  # Decisions
        options = _options(app.screen)
        assert not options.get_option(f"decisions.new").disabled
        assert options.get_option("decisions.approve").disabled

    run_app(app, scenario)


def test_a_submenu_starts_with_back_and_highlights_its_first_command(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        await pilot.press("enter")  # Decisions
        options = _options(app.screen)
        back = options.get_option_at_index(0)
        assert (back.id, str(back.prompt)) == ("back", "← Back")
        assert _highlighted_id(app.screen) == "decisions.new"

    run_app(app, scenario)


def test_back_returns_to_the_previous_menu_and_is_not_remembered(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        await pilot.press("enter")  # Decisions
        options = _options(app.screen)
        options.highlighted = options.get_option_index("back")
        await pilot.press("enter")
        assert isinstance(app.screen, MenuScreen) and app.screen.menu.id == "main"

    run_app(app, scenario)
    assert user_state.last("decisions") is None
    assert user_state.last("main") == "decisions"


def test_the_main_menu_has_no_back_item(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        options = _options(app.screen)
        assert "back" not in {options.get_option_at_index(i).id for i in range(options.option_count)}

    run_app(app, scenario)


def _open_new_form(pilot):
    async def go():
        await pilot.press("enter")  # Decisions
        await pilot.press("enter")  # New decision
        await settle(pilot)
        assert isinstance(pilot.app.screen, FormScreen)

    return go()


def test_new_creates_the_decision_through_adrpy(repo, user_state):
    app = AdrpyTui(repo, user_state=user_state)

    async def scenario(pilot):
        await _open_new_form(pilot)
        app.screen.query_one("#field-title").focus()
        await pilot.press(*"Use PostgreSQL")
        await pilot.press("ctrl+r")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmScreen)
        line = _text(app.screen, "#command-line")
        assert line.startswith("adrpy new --path ") and "Use PostgreSQL" in line
        await pilot.press("enter")  # Yes
        await settle(pilot)
        assert isinstance(app.screen, ResultScreen) and app.screen.result.success

    run_app(app, scenario)
    assert [path.name for path in (repo / "doc" / "adr").glob("*.md")] == ["ADR001V01-use-postgre-sql.md"]


def test_an_obvious_mistake_is_shown_without_running_adrpy(tmp_path, user_state):
    client = FakeClient()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _open_new_form(pilot)
        await pilot.press("ctrl+r")  # title left empty
        await pilot.pause()
        assert isinstance(app.screen, FormScreen)
        assert _text(app.screen, "#problem-title") == "Required."

    run_app(app, scenario)
    assert "new" not in client.verbs()


def test_forbidden_characters_cannot_be_typed_in_a_title(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        await _open_new_form(pilot)
        app.screen.query_one("#field-title").focus()
        await pilot.press(*"a/b|c")
        assert app.screen.query_one("#field-title").value == "abc"

    run_app(app, scenario)


def test_scope_offers_the_values_the_repository_already_uses(tmp_path, user_state):
    decisions = [{"header": {"scope": "security", "domain": None}}, {"header": {"scope": "backend"}}, {"header": None}]
    client = FakeClient(answers={"explore": {"success": True, "data": {"decisions": decisions, "warnings": []}}})
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _open_new_form(pilot)
        scope = app.screen.query_one("#field-scope")
        assert scope.suggester.candidates == ["backend", "security"]
        scope.focus()
        await pilot.press(*"secu")
        await pilot.pause()
        assert _text(app.screen, "#similar-scope") == "Existing: security"
        await pilot.press("right")  # accepts the inline suggestion
        assert scope.value == "security"

    run_app(app, scenario)


def test_a_failure_shows_adrpy_s_detail_and_its_errors(tmp_path, user_state):
    failure = {
        "success": False, "code": "repository-inconsistent", "detail": "The repository is inconsistent.",
        "data": {"errors": [{"file": "ADR001V01-x.md", "code": "no-header", "hint": "Run migrate."}]}, "warnings": [],
    }
    app = AdrpyTui(tmp_path, client=FakeClient(answers={"new": failure}), user_state=user_state)

    async def scenario(pilot):
        await _open_new_form(pilot)
        app.screen.query_one("#field-title").focus()
        await pilot.press(*"Anything", "ctrl+r")
        await pilot.pause()
        await pilot.press("enter")
        await settle(pilot)
        assert isinstance(app.screen, ResultScreen)
        assert "repository-inconsistent" in _text(app.screen, ".title")
        table = app.screen.query_one("#errors", DataTable)
        assert table.row_count == 1 and table.get_row_at(0) == ["ADR001V01-x.md", "no-header", "Run migrate."]
        await pilot.press("escape")
        assert isinstance(app.screen, MenuScreen)  # back to the Decisions menu

    run_app(app, scenario)


class BlockingClient(FakeClient):
    """Holds `new` until `release` is set, as a slow adrpy would."""

    def __init__(self):
        super().__init__()
        self.release = threading.Event()

    def _answer(self, argv):
        if argv[3] == "new":
            self.release.wait(timeout=10)
        return super()._answer(argv)


def test_keys_pressed_while_a_command_runs_neither_leave_nor_run_it_again(tmp_path, user_state):
    client = BlockingClient()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _open_new_form(pilot)
        app.screen.query_one("#field-title").focus()
        await pilot.press(*"Anything", "ctrl+r")
        await pilot.pause()
        await pilot.press("enter")  # Yes: `new` starts and blocks
        await pilot.pause()
        await pilot.press("escape", "ctrl+r", "enter", "escape")
        await pilot.pause()
        assert isinstance(app.screen, FormScreen)
        client.release.set()
        await settle(pilot)
        assert isinstance(app.screen, ResultScreen)
        await pilot.press("escape")
        assert isinstance(app.screen, MenuScreen) and app.screen.menu.id == "decisions"

    run_app(app, scenario)
    assert client.verbs().count("new") == 1


def test_help_shows_the_command_s_contract(tmp_path, user_state):
    app = AdrpyTui(tmp_path, user_state=user_state)

    async def scenario(pilot):
        options = _options(app.screen)
        options.highlighted = options.get_option_index("help")
        await pilot.press("enter")
        options = _options(app.screen)
        options.highlighted = options.get_option_index("help.new")
        await pilot.press("enter")
        await settle(pilot)
        assert isinstance(app.screen, HelpScreen)
        markdown = app.screen.query_one(Markdown).source
        assert markdown.startswith("# adrpy new") and "`--title`" in markdown and "`title-already-exists`" in markdown

    run_app(app, scenario)
