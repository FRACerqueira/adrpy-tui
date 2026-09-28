"""The screens, driven headless through Textual's Pilot."""

import pathlib
import threading

import pytest
from pathlib import Path

from textual.widgets import DataTable, Markdown, OptionList, Static

from adrpy_tui.core.state import UserState
from adrpy_tui.ui.app import AdrpyTui
from adrpy_tui.ui.appearance import AppearanceScreen, ColorEditScreen, ColorsScreen
from adrpy_tui.ui.check import CheckScreen
from adrpy_tui.ui.config import ConfigScreen, FieldEditScreen
from adrpy_tui.ui.explore import DetailScreen, ExploreScreen
from adrpy_tui.ui.confirm import ConfirmScreen
from adrpy_tui.ui.form import FormScreen
from adrpy_tui.ui.help import HelpScreen
from adrpy_tui.ui.keys import KeyCaptureScreen, KeysScreen
from adrpy_tui.ui.language import LanguageScreen
from adrpy_tui.ui.logs import LogScreen
from adrpy_tui.ui.menu import MenuScreen
from adrpy_tui.ui.migrate import MigrateScreen
from adrpy_tui.ui.preview import PreviewScreen
from adrpy_tui.ui.repository import RepositoryScreen
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


def _open_appearance(pilot):
    async def go():
        options = _options(pilot.app.screen)
        options.highlighted = options.get_option_index("appearance")
        await pilot.press("enter")
        assert isinstance(pilot.app.screen, AppearanceScreen)
        return pilot.app.screen.query_one("#presets", OptionList)

    return go()


def _banner_color(app):
    return app.screen.query_one("AppHeader .banner").styles.color.hex


def test_appearance_previews_a_preset_and_saves_it_on_enter(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        assert _banner_color(app) == "#FF8C00"
        presets = await _open_appearance(pilot)
        assert [presets.get_option_at_index(i).id for i in range(presets.option_count)] == [
            "back", "default", "light", "high-contrast", "colors",
        ]
        assert presets.get_option_at_index(presets.highlighted).id == "default"  # the current one
        presets.highlighted = presets.get_option_index("light")
        await settle(pilot)
        assert _banner_color(app) == "#8A4700"  # previewed live
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, MenuScreen) and _banner_color(app) == "#8A4700"

    run_app(app, scenario)
    assert user_state.appearance == "light"


def test_leaving_appearance_without_choosing_restores_the_saved_preset(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        presets = await _open_appearance(pilot)
        presets.highlighted = presets.get_option_index("high-contrast")
        await pilot.pause()
        assert _banner_color(app) != "#FF8C00"
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, MenuScreen) and _banner_color(app) == "#FF8C00"

    run_app(app, scenario)
    assert user_state.appearance is None


def test_a_stored_appearance_is_applied_on_start_and_an_unknown_one_is_the_default(tmp_path, user_state):
    for stored, banner in (("light", "#8A4700"), ("from-a-newer-version", "#FF8C00")):
        user_state.set_appearance(stored)
        app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

        async def scenario(pilot):
            assert _banner_color(app) == banner

        run_app(app, scenario)


def _contrast(foreground, background):
    """WCAG contrast of `foreground` drawn on `background`, blending a
    translucent foreground first, as the terminal shows it."""
    from test_themes import _contrast as ratio

    foreground = background.blend(foreground.with_alpha(1.0), foreground.a)
    return ratio(foreground, background)


def _drawn(widget):
    return widget.styles.color, widget.background_colors[1]


@pytest.mark.parametrize("preset", ["default", "light", "high-contrast"])
def test_text_drawn_on_its_own_background_meets_wcag_aa(tmp_path, user_state, preset):
    """The role colors against the screen are checked in test_themes.py;
    this checks the text drawn on a widget's own background -- the menu
    cursor, a field, the confirmation and its buttons."""
    from textual.color import Color
    from textual.widgets import Button, Input

    user_state.set_appearance(preset)
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)
    found = {}

    async def scenario(pilot):
        cursor = _options(app.screen).get_component_rich_style("option-list--option-highlighted")
        found["menu cursor"] = (Color.from_rich_color(cursor.color), Color.from_rich_color(cursor.bgcolor))
        await _open_new_form(pilot)
        title = app.screen.query_one("#field-title", Input)
        title.focus()
        await pilot.press(*"abc")
        found["typed value"] = _drawn(title)
        found["run button"] = _drawn(app.screen.query_one("#run", Button))
        await pilot.press("ctrl+r")
        await pilot.pause()
        found["command to confirm"] = _drawn(app.screen.query_one("#command-line", Static))
        found["focused yes"] = _drawn(app.screen.query_one("#yes", Button))

    run_app(app, scenario)
    too_low = {name: round(_contrast(*pair), 2) for name, pair in found.items() if _contrast(*pair) < 4.5}
    assert too_low == {}


@pytest.mark.parametrize("preset", ["default", "light", "high-contrast"])
def test_the_active_row_stands_out_from_the_other_rows(tmp_path, user_state, preset):
    """Reported on explore: the active row differed from the others by its
    text color alone (1.13:1 on Default between the two backgrounds). Its
    background now stands apart from the rows' own at WCAG's 3:1 for a
    component, and its text still reads at 4.5:1 -- with the list focused
    and without."""
    from textual.color import Color

    user_state.set_appearance(preset)
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)
    found = {}

    def styles(options):
        active = options.get_component_rich_style("option-list--option-highlighted")
        return (Color.from_rich_color(active.color), Color.from_rich_color(active.bgcolor),
                options.background_colors[1])

    async def scenario(pilot):
        options = _options(app.screen)
        found["focused"] = styles(options)
        app.screen.set_focus(None)
        await pilot.pause()
        found["blurred"] = styles(options)

    run_app(app, scenario)
    text = {state: round(_contrast(fg, bg), 2) for state, (fg, bg, _) in found.items()}
    apart = round(_contrast(*found["focused"][1:]), 2)
    assert (min(text.values()) >= 4.5, apart >= 3) == (True, True), (text, apart)


@pytest.mark.parametrize("preset", ["default", "light", "high-contrast"])
def test_markdown_headings_and_table_headers_meet_wcag_aa(tmp_path, user_state, preset):
    """Reported on help in High contrast: Textual draws a Markdown heading
    and a table's header in the theme's primary color, which Default and
    High contrast set as a button's background (#00509E) -- 2.36:1 as text
    on their dark screen. Measured on help and on a preview, which is
    Markdown too."""
    from textual.widgets._markdown import MarkdownBullet, MarkdownHeader, MarkdownTableCellContents

    user_state.set_appearance(preset)
    contract = {"success": True, "data": {"commands": [{
        "name": "new", "summary": "Creates.", "description": "Text.",
        "arguments": [{"name": "title", "type": "string", "required": True, "description": "The title."}],
        "failure_codes": [{"code": "x-code", "condition": "When."}]}], "warnings": []}}
    page = tmp_path / "ADR001V01-d.md"
    page.write_text("\n".join(["# Title", "", "## Context", "", "### Detail", "", "- a point", "",
                               "| Field | Value |", "|---|---|", "| a | b |", ""]), encoding="utf-8")
    app = AdrpyTui(tmp_path, client=FakeClient(answers={"help": contract}), user_state=user_state)
    too_low = {}

    def measure(screen_name):
        for widget in app.screen.query(Markdown).first().query("*"):
            if isinstance(widget, (MarkdownHeader, MarkdownBullet)) or (
                    isinstance(widget, MarkdownTableCellContents) and widget.has_class("header")):
                ratio = _contrast(widget.styles.color, widget.background_colors[1])
                if ratio < 4.5:
                    too_low[f"{screen_name} {type(widget).__name__}"] = round(ratio, 2)

    async def scenario(pilot):
        app.push_screen(HelpScreen("new"))
        await settle(pilot)
        measure("help")
        app.pop_screen()
        app.push_screen(PreviewScreen(page))
        await settle(pilot)
        measure("preview")

    run_app(app, scenario)
    assert too_low == {}


def _component(widget, component):
    from textual.color import Color

    style = widget.get_component_rich_style(component)
    foreground = Color.from_rich_color(style.color) if style.color else widget.styles.color
    background = Color.from_rich_color(style.bgcolor) if style.bgcolor else widget.background_colors[1]
    return foreground, background


@pytest.mark.parametrize("preset", ["default", "light", "high-contrast"])
def test_every_kind_of_field_meets_wcag_contrast(tmp_path, user_state, preset):
    """Text at 4.5:1 (WCAG AA), a switch's slider -- a component, not
    text -- at 3:1 (WCAG 1.4.11), on or off: the selects and their open
    list, the text area with its cursor and selection, the multi-selects,
    the radio buttons, the switches and the folders tree."""
    from textual.widgets import DirectoryTree, RadioButton, Select, SelectionList, Switch, TextArea

    user_state.set_appearance(preset)
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)
    text, components = {}, {}

    async def scenario(pilot):
        await _open_group_item(pilot, "log", "log")
        select = app.screen.query_one("#field-classification", Select)
        select.focus()
        current = select.query_one("SelectCurrent")
        text["select"] = (current.styles.color, current.background_colors[1])
        await pilot.press("enter")
        await pilot.pause()
        overlay = select.query_one("SelectOverlay")
        text["open select's cursor"] = _component(overlay, "option-list--option-highlighted")
        text["open select's option"] = _component(overlay, "option-list--option")
        await pilot.press("escape")
        body = app.screen.query_one("#field-body", TextArea)
        body.focus()
        body.text = "Some text"
        await pilot.pause()
        text["text area"] = (body.styles.color, body.background_colors[1])
        text["text area's cursor"] = _component(body, "text-area--cursor")
        text["text area's selection"] = (body.styles.color, _component(body, "text-area--selection")[1])
        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        await _open_group_item(pilot, "skills", "install")
        choices = app.screen.query_one("#field-provider", SelectionList)
        choices.focus()
        choices.highlighted = 0
        await pilot.pause()
        text["multi-select's cursor"] = _component(choices, "option-list--option-highlighted")
        radio = app.screen.query_one("#target-project", RadioButton)
        text["radio button"] = (radio.styles.color, radio.background_colors[1])
        switch = app.screen.query_one("#field-force", Switch)
        components["switch off"] = _component(switch, "switch--slider")
        switch.value = True
        await pilot.pause()
        components["switch on"] = _component(switch, "switch--slider")
        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        options = _options(app.screen)
        options.highlighted = options.get_option_index("change-repository")
        await pilot.press("enter")
        await pilot.pause()
        tree = app.screen.query_one("#folders", DirectoryTree)
        tree.focus()
        await pilot.pause()
        text["folders tree's cursor"] = _component(tree, "tree--cursor")

    run_app(app, scenario)
    too_low = {name: round(_contrast(*pair), 2) for name, pair in text.items() if _contrast(*pair) < 4.5}
    too_low.update({name: round(_contrast(*pair), 2) for name, pair in components.items() if _contrast(*pair) < 3})
    assert too_low == {}


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
        options = _options(app.screen)
        # Every item of every menu has its screen now.
        assert not any("(not available yet)" in str(item.prompt)
                       for item in (options.get_option_at_index(i) for i in range(options.option_count)))

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
        errors = app.screen.query_one("#errors-options", OptionList)
        assert [str(errors.get_option_at_index(i).prompt) for i in range(errors.option_count)] == [
            "ADR001V01-x.md  ·  no-header"]
        assert _text(app.screen, "#errors-hint") == "Run migrate."
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


def _decision(filename, created="2026-01-10", update=None, migrated=False, valid=True, updated=None,
              scope=None, domain=None, title="x"):
    return {
        "filename": filename,
        "path": f"C:/repo/doc/adr/{filename}",
        "title": title,
        "header": {"is_valid": valid, "is_migrated": migrated, "status_create": None if migrated else "Proposed",
                   "date_create": None if migrated else created, "status_update": update,
                   "date_update": updated if update else None, "status_change": None, "scope": scope, "domain": domain},
    }


PORTUGUESE_CONFIG = {"success": True, "data": {"config": {
    "statusnew": "Proposto", "statusacc": "Aceito", "statusrej": "Rejeitado", "statussup": "Substituído",
    "headermigrated": "Migrado"}, "warnings": []}}

DECISIONS = [
    _decision("ADR001V01-proposed.md"),
    _decision("ADR002V01-accepted.md", update="Accepted"),
    _decision("ADR003V01-migrated.md", migrated=True),
    _decision("ADR004V01-broken.md", valid=False),
]


def _client_with(decisions, config=PORTUGUESE_CONFIG):
    return FakeClient(answers={
        "config": config,
        "explore": {"success": True, "data": {"decisions": decisions, "warnings": []}},
    })


async def _open(pilot, item):
    """Opens Decisions > `item` and waits for its form to read the repository."""
    options = _options(pilot.app.screen)
    options.highlighted = options.get_option_index("decisions")  # not the remembered item
    await pilot.press("enter")
    await settle(pilot)  # the submenu is mounted before it is queried
    options = _options(pilot.app.screen)
    options.highlighted = options.get_option_index(f"decisions.{item}")
    await pilot.press("enter")
    await settle(pilot)
    assert isinstance(pilot.app.screen, FormScreen)
    return pilot.app.screen.query_one("#field-file-options", OptionList)


async def _show_all(pilot):
    """Turns "only the available ones" off."""
    pilot.app.screen.query_one("#field-file-only-available").value = False
    await pilot.pause()


def _listed(options):
    return {str(options.get_option_at_index(i).prompt): options.get_option_at_index(i).disabled
            for i in range(options.option_count)}


def test_the_picker_lists_every_decision_with_its_label_and_disables_what_approve_cannot_take(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=_client_with(DECISIONS), user_state=user_state)

    async def scenario(pilot):
        options = await _open(pilot, "approve")
        await _show_all(pilot)
        assert _listed(options) == {
            "ADR001V01-proposed.md  ·  Proposto": False,
            "ADR002V01-accepted.md  ·  Aceito": True,
            "ADR003V01-migrated.md  ·  Migrado": False,
            "ADR004V01-broken.md  ·  ?": True,
        }

    run_app(app, scenario)


def test_undo_takes_the_accepted_and_rejected_ones(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=_client_with(DECISIONS), user_state=user_state)

    async def scenario(pilot):
        options = await _open(pilot, "undo")
        await _show_all(pilot)
        enabled = [prompt for prompt, disabled in _listed(options).items() if not disabled]
        assert enabled == ["ADR002V01-accepted.md  ·  Aceito"]

    run_app(app, scenario)


def test_the_picker_filter_narrows_the_list_by_name(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=_client_with(DECISIONS), user_state=user_state)

    async def scenario(pilot):
        options = await _open(pilot, "approve")
        app.screen.query_one("#field-file-filter").focus()
        await pilot.press(*"MIGR")
        await pilot.pause()
        assert list(_listed(options)) == ["ADR003V01-migrated.md  ·  Migrado"]
        assert _text(app.screen, "#problem-file") == ""  # typing a filter is not an answer

    run_app(app, scenario)


def test_the_picker_shows_only_the_available_decisions_by_default(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=_client_with(DECISIONS), user_state=user_state)

    async def scenario(pilot):
        options = await _open(pilot, "approve")
        assert _listed(options) == {"ADR001V01-proposed.md  ·  Proposto": False, "ADR003V01-migrated.md  ·  Migrado": False}

    run_app(app, scenario)


def test_the_picker_shows_eight_decisions_a_page_with_where_the_cursor_is(tmp_path, user_state):
    many = [_decision(f"ADR{n:03}V01-d.md") for n in range(1, 21)]
    app = AdrpyTui(tmp_path, client=_client_with(many), user_state=user_state)

    async def scenario(pilot):
        options = await _open(pilot, "approve")
        assert options.scrollable_content_region.height == 8
        assert _text(app.screen, "#field-file-page") == "Items 1–8 of 20 · page 1 of 3 · PgUp/PgDn"
        options.focus()
        await pilot.press("pagedown")
        await pilot.pause()
        assert _text(app.screen, "#field-file-page") == "Items 9–16 of 20 · page 2 of 3 · PgUp/PgDn"
        await pilot.press("end")
        await pilot.pause()
        assert _text(app.screen, "#field-file-page") == "Items 17–20 of 20 · page 3 of 3 · PgUp/PgDn"

    run_app(app, scenario)


def test_the_picker_says_so_when_nothing_matches(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=_client_with(DECISIONS), user_state=user_state)

    async def scenario(pilot):
        options = await _open(pilot, "approve")
        app.screen.query_one("#field-file-filter").focus()
        await pilot.press(*"accepted")  # exists, but approve can't take it
        await pilot.pause()
        assert options.option_count == 0
        assert _text(app.screen, "#field-file-page") == "No decision matches."

    run_app(app, scenario)


def test_choosing_no_decision_is_shown_without_running_adrpy(tmp_path, user_state):
    client = _client_with(DECISIONS)
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _open(pilot, "approve")
        await pilot.press("ctrl+r")
        await pilot.pause()
        assert isinstance(app.screen, FormScreen)
        assert _text(app.screen, "#problem-file") == "Required."

    run_app(app, scenario)
    assert "approve" not in client.verbs()


def test_a_date_before_the_decision_s_creation_is_shown_without_running_adrpy(tmp_path, user_state):
    client = _client_with(DECISIONS)
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        options = await _open(pilot, "approve")
        options.focus()
        options.highlighted = 0
        await pilot.press("enter")  # ADR001V01-proposed.md, created 2026-01-10
        assert _text(app.screen, "#field-file-selected") == "Selected: ADR001V01-proposed.md"
        refdate = app.screen.query_one("#field-refdate")
        refdate.value = "2026-01-09"
        await pilot.press("ctrl+r")
        await pilot.pause()
        assert _text(app.screen, "#problem-refdate") == "Cannot be before 2026-01-10."

    run_app(app, scenario)
    assert "approve" not in client.verbs()


def test_approve_then_undo_through_adrpy(repo, user_state, client):
    created = client.run("new", ("--path", str(repo), "--title", "Use PostgreSQL")).data["created"]
    app = AdrpyTui(repo, user_state=user_state)

    async def run(pilot, item):
        options = await _open(pilot, item)
        options.focus()
        options.highlighted = next(i for i in range(options.option_count) if not options.get_option_at_index(i).disabled)
        await pilot.press("enter", "ctrl+r")
        await pilot.pause()
        line = _text(app.screen, "#command-line")
        await pilot.press("enter")  # Yes
        await settle(pilot)
        assert isinstance(app.screen, ResultScreen) and app.screen.result.success, app.screen.result
        await pilot.press("escape", "escape")  # result -> Decisions -> main
        return line

    async def scenario(pilot):
        assert (await run(pilot, "approve")).startswith("adrpy approve --file ")
        assert (await run(pilot, "undo")).startswith("adrpy undo --file ")

    run_app(app, scenario)
    [decision] = client.run("explore", ("--path", str(repo))).data["decisions"]
    assert decision["path"] == created and decision["header"]["status_update"] is None


def _page_text(screen, list_id):
    return _text(screen, f"#{list_id}-page")


def test_the_help_menu_shows_a_page_of_eight_commands(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        options = _options(app.screen)
        options.highlighted = options.get_option_index("help")
        await pilot.press("enter")
        options = _options(app.screen)
        assert options.option_count == 20  # Back and the 19 commands
        assert options.scrollable_content_region.height == 8
        assert _page_text(app.screen, "options") == "Items 1–8 of 20 · page 1 of 3 · PgUp/PgDn"
        await pilot.press("pagedown")
        await pilot.pause()
        assert _page_text(app.screen, "options") == "Items 9–16 of 20 · page 2 of 3 · PgUp/PgDn"

    run_app(app, scenario)


def test_a_remembered_item_past_the_first_page_opens_on_its_page(tmp_path, user_state):
    user_state.remember("main", "exit")
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        assert _page_text(app.screen, "options") == "Items 9–12 of 12 · page 2 of 2 · PgUp/PgDn"

    run_app(app, scenario)


def test_a_list_that_fits_one_page_shows_no_page_line(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        await _open_appearance(pilot)
        assert _page_text(app.screen, "presets") == ""

    run_app(app, scenario)


def _check_paged(app, seen):
    """Every OptionList the current screen shows sits in a PagedList, eight
    rows at most. Two kinds are not lists of content and are left out: a
    Select's open list (a dropdown, closed again at once) and a field's
    SelectionList of a few fixed choices (capped at eight rows itself)."""
    from textual.widgets import SelectionList

    from adrpy_tui.ui.paged import PAGE_SIZE, PagedList

    for options in app.screen.query(OptionList):
        if isinstance(options, SelectionList) or type(options).__name__ == "SelectOverlay":
            assert options.styles.max_height is None or options.styles.max_height.value <= PAGE_SIZE + 2
            continue
        assert isinstance(options.parent, PagedList), f"{type(app.screen).__name__}: #{options.id}"
        assert options.scrollable_content_region.height <= PAGE_SIZE
    seen.append(type(app.screen).__name__)


def test_every_list_of_the_other_screens_is_paged(tmp_path, user_state):
    """The same rule on the screens of their own: explore and a decision's
    detail, check's errors, migrate's files and preview, the skills list,
    the colors, and the log and skills forms (with a select and a
    multi-select, left out as above)."""
    (tmp_path / "doc" / "adr").mkdir(parents=True)
    for n in range(1, 12):
        (tmp_path / "doc" / "adr" / f"{n:04}-legacy.md").write_text("# x\n", encoding="utf-8")
    decisions = [_decision(f"ADR{n:03}V01-d.md", update="Accepted", updated="2026-02-01") for n in range(1, 12)]
    errors = [{"code": "no-header", "file": f"/r/{n}.md", "hint": "Run migrate."} for n in range(11)]
    preview = [{"file": f"/r/{n:04}-legacy.md", "number": n, "version": 0, "title": "legacy"} for n in range(1, 12)]
    skills = [{"skill": "adrpy", "provider": f"p{n}", "scope": "project", "installed": False, "drifted": None,
               "file": f"f{n}"} for n in range(11)]
    client = FakeClient(answers={
        "config": {"success": True, "data": {"config": {**REPO_CONFIG, "migrationpattern": ""}, "warnings": []}},
        "explore": {"success": True, "data": {"decisions": decisions, "migrationpattern_preview": preview,
                                              "warnings": []}},
        "check": {"success": False, "code": "repository-inconsistent", "detail": "x", "warnings": [],
                  "data": {"errors": errors}},
        "skills:list": {"success": True, "data": {"skills": skills, "warnings": []}},
    })
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)
    seen = []

    async def back(pilot, times=2):
        for _ in range(times):
            await pilot.press("escape")
            await pilot.pause()

    async def scenario(pilot):
        await _open_group_item(pilot, "explore", "explore")
        _check_paged(app, seen)
        app.screen.query_one("#decisions", OptionList).focus()
        await pilot.press("enter")
        await settle(pilot)
        _check_paged(app, seen)  # the detail and its actions
        await back(pilot, 3)
        await _open_group_item(pilot, "explore", "check")
        _check_paged(app, seen)
        await back(pilot)
        await _open_group_item(pilot, "repository", "migrate")
        app.screen.query_one("#preview").press()
        await settle(pilot)
        _check_paged(app, seen)  # its files and its preview
        await back(pilot)
        await _open_group_item(pilot, "skills", "list")
        _check_paged(app, seen)
        await back(pilot)
        await _open_group_item(pilot, "skills", "install")
        _check_paged(app, seen)
        await back(pilot)
        await _open_group_item(pilot, "log", "log")
        _check_paged(app, seen)
        await back(pilot)
        await _open_colors(pilot)
        _check_paged(app, seen)
        await back(pilot)  # colors -> appearance -> main menu
        await _open_group_item(pilot, "log", "browse")
        _check_paged(app, seen)
        await back(pilot)
        await _open_keys(pilot)
        _check_paged(app, seen)

    run_app(app, scenario)
    assert set(seen) == {"ExploreScreen", "DetailScreen", "CheckScreen", "MigrateScreen", "SkillsListScreen",
                         "FormScreen", "ColorsScreen", "LogScreen", "KeysScreen"}
    assert len(seen) == 10


def test_every_list_of_every_screen_is_paged(tmp_path, user_state):
    """The interface's rule for lists (doc/forms.md): any OptionList a
    screen shows sits in a PagedList, eight rows at most."""
    app = AdrpyTui(tmp_path, client=_client_with(DECISIONS), user_state=user_state)
    seen = []

    def check():
        _check_paged(app, seen)

    async def scenario(pilot):
        check()  # main menu
        options = _options(app.screen)
        options.highlighted = options.get_option_index("help")
        await pilot.press("enter")
        check()  # a submenu
        await pilot.press("escape")
        options = _options(app.screen)
        options.highlighted = options.get_option_index("language")
        await pilot.press("enter")
        check()  # language
        await pilot.press("escape")
        await _open_appearance(pilot)
        check()
        await pilot.press("escape")
        await pilot.pause()  # the main menu is back
        await _open(pilot, "approve")
        check()  # the decision picker
        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        await _open_group_item(pilot, "repository", "config")
        check()  # the config editor

    run_app(app, scenario)
    assert set(seen) == {"MenuScreen", "LanguageScreen", "AppearanceScreen", "FormScreen", "ConfigScreen"}


CHANGE_DECISIONS = [
    _decision("ADR001V01-proposed.md"),
    _decision("ADR002V01-accepted.md", update="Accepted", updated="2026-02-01", scope="backend", domain="dados",
              title="adotar-textual"),
    _decision("ADR003V01-rejected.md", update="Rejected", updated="2026-02-02"),
    _decision("ADR004V01-migrated.md", migrated=True),
]


def _enabled(options):
    return [prompt.split("  ·  ")[0] for prompt, disabled in _listed(options).items() if not disabled]


async def _choose(pilot, options, filename):
    options.focus()
    options.highlighted = next(i for i in range(options.option_count)
                               if str(options.get_option_at_index(i).prompt).startswith(filename))
    await pilot.press("enter")
    await pilot.pause()


def test_version_revise_and_supersede_take_the_states_adrpy_says(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=_client_with(CHANGE_DECISIONS), user_state=user_state)
    expected = {
        "version": ["ADR002V01-accepted.md", "ADR003V01-rejected.md", "ADR004V01-migrated.md"],
        "revise": ["ADR002V01-accepted.md", "ADR003V01-rejected.md", "ADR004V01-migrated.md"],
        "supersede": ["ADR002V01-accepted.md", "ADR004V01-migrated.md"],
    }
    found = {}

    async def scenario(pilot):
        for item in expected:
            found[item] = _enabled(await _open(pilot, item))
            await pilot.press("escape")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

    run_app(app, scenario)
    assert found == expected


def test_choosing_a_decision_fills_its_scope_and_domain_and_shows_the_default_title(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=_client_with(CHANGE_DECISIONS), user_state=user_state)

    async def scenario(pilot):
        options = await _open(pilot, "supersede")
        await _choose(pilot, options, "ADR002V01-accepted.md")
        assert app.screen.query_one("#field-scope").value == "backend"
        assert app.screen.query_one("#field-domain").value == "dados"
        title = app.screen.query_one("#field-title")
        assert (title.value, title.placeholder) == ("", "Default: adotar-textual")

    run_app(app, scenario)


def test_a_value_typed_before_choosing_is_not_overwritten(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=_client_with(CHANGE_DECISIONS), user_state=user_state)

    async def scenario(pilot):
        options = await _open(pilot, "version")
        app.screen.query_one("#field-scope").value = "mine"
        await _choose(pilot, options, "ADR002V01-accepted.md")
        assert app.screen.query_one("#field-scope").value == "mine"
        assert app.screen.query_one("#field-domain").value == "dados"

    run_app(app, scenario)


def test_version_s_date_cannot_be_before_the_decision_s_last_update(tmp_path, user_state):
    client = _client_with(CHANGE_DECISIONS)
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        options = await _open(pilot, "version")
        await _choose(pilot, options, "ADR002V01-accepted.md")  # accepted on 2026-02-01
        app.screen.query_one("#field-refdate").value = "2026-01-31"
        await pilot.press("ctrl+r")
        await pilot.pause()
        assert _text(app.screen, "#problem-refdate") == "Cannot be before 2026-02-01."

    run_app(app, scenario)
    assert "version" not in client.verbs()


def test_version_s_empty_switch_becomes_the_presence_only_flag(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=_client_with(CHANGE_DECISIONS), user_state=user_state)

    async def scenario(pilot):
        options = await _open(pilot, "version")
        await _choose(pilot, options, "ADR002V01-accepted.md")
        app.screen.query_one("#field-empty").value = True
        await pilot.press("ctrl+r")
        await pilot.pause()
        line = _text(app.screen, "#command-line")
        assert line.endswith("--empty") and "--empty true" not in line

    run_app(app, scenario)


def test_a_failed_explore_is_shown_in_the_picker(tmp_path, user_state):
    failure = {"success": False, "code": "io-error", "detail": "Permission denied: doc/adr"}
    client = FakeClient(answers={"config": PORTUGUESE_CONFIG, "explore": failure})
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _open(pilot, "approve")
        assert _text(app.screen, "#field-file-page") == "Could not read the decisions: Permission denied: doc/adr"

    run_app(app, scenario)


def test_version_and_revise_through_adrpy(repo, user_state, client):
    created = client.run("new", ("--path", str(repo), "--title", "Use PostgreSQL", "--scope", "backend")).data["created"]
    assert client.run("approve", ("--file", created)).success
    app = AdrpyTui(repo, user_state=user_state)
    results = {}

    async def run(pilot, item, filename_start):
        options = await _open(pilot, item)
        await _choose(pilot, options, filename_start)
        await pilot.press("ctrl+r")
        await pilot.pause()
        await pilot.press("enter")  # Yes
        await settle(pilot)
        results[item] = app.screen.result
        await pilot.press("escape", "escape")

    async def scenario(pilot):
        await run(pilot, "version", "ADR001V01")
        await run(pilot, "revise", "ADR001V01")  # the fixture repository has revisions off

    run_app(app, scenario)
    assert results["version"].success, results["version"]
    assert (results["revise"].success, results["revise"].code) == (False, "revision-not-configured")
    names = sorted(d["filename"] for d in client.run("explore", ("--path", str(repo))).data["decisions"])
    assert names == ["ADR001V01-use-postgre-sql.md", "ADR001V02-use-postgre-sql.md"]


def test_supersede_through_adrpy(repo, user_state, client):
    created = client.run("new", ("--path", str(repo), "--title", "Use PostgreSQL")).data["created"]
    assert client.run("approve", ("--file", created)).success
    app = AdrpyTui(repo, user_state=user_state)

    async def scenario(pilot):
        options = await _open(pilot, "supersede")
        await _choose(pilot, options, "ADR001V01")
        app.screen.query_one("#field-title").focus()
        await pilot.press(*"Use CockroachDB", "ctrl+r")
        await pilot.pause()
        await pilot.press("enter")
        await settle(pilot)
        assert app.screen.result.success, app.screen.result

    run_app(app, scenario)
    names = sorted(d["filename"] for d in client.run("explore", ("--path", str(repo))).data["decisions"])
    assert names == ["ADR001V01-use-postgre-sql.md", "ADR002V01-use-cockroach-db--001.md"]


async def _open_group_item(pilot, group, item):
    options = _options(pilot.app.screen)
    options.highlighted = options.get_option_index(group)
    await pilot.press("enter")
    await settle(pilot)  # the submenu is mounted before it is queried
    options = _options(pilot.app.screen)
    options.highlighted = options.get_option_index(f"{group}.{item}")
    await pilot.press("enter")
    await settle(pilot)


def _rows(options):
    return [" ".join(str(options.get_option_at_index(i).prompt).split()) for i in range(options.option_count)]


def test_explore_lists_every_decision_with_its_label_scope_and_domain(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=_client_with(CHANGE_DECISIONS), user_state=user_state)

    async def scenario(pilot):
        await _open_group_item(pilot, "explore", "explore")
        assert isinstance(app.screen, ExploreScreen)
        # The fake decisions' paths are outside this repository: their folder
        # shows as its own name.
        assert _rows(app.screen.query_one("#decisions", OptionList)) == [
            "ADR001V01-proposed.md adr Proposto",
            "ADR002V01-accepted.md adr Aceito backend dados",
            "ADR003V01-rejected.md adr Rejeitado",
            "ADR004V01-migrated.md adr Migrado",
        ]

    run_app(app, scenario)


def test_explore_warns_of_the_repository_s_inconsistencies(tmp_path, user_state):
    explore = {"success": True, "data": {"decisions": DECISIONS, "warnings": [],
                                         "consistency": {"errors": [{"code": "duplicate-number"}] * 2}}}
    client = FakeClient(answers={"config": PORTUGUESE_CONFIG, "explore": explore})
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _open_group_item(pilot, "explore", "explore")
        assert _text(app.screen, "#explore-notes") == "The repository has 2 inconsistencies: see Check."

    run_app(app, scenario)


def test_a_decision_s_detail_offers_the_commands_its_state_allows_and_opens_them_with_it(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=_client_with(CHANGE_DECISIONS), user_state=user_state)

    async def scenario(pilot):
        await _open_group_item(pilot, "explore", "explore")
        decisions = app.screen.query_one("#decisions", OptionList)
        decisions.focus()
        decisions.highlighted = 1  # ADR002V01-accepted.md
        await pilot.press("enter")
        await settle(pilot)
        assert isinstance(app.screen, DetailScreen)
        actions = app.screen.query_one("#actions", OptionList)
        assert [actions.get_option_at_index(i).id for i in range(actions.option_count)] == [
            "undo", "version", "revise", "supersede"]
        actions.highlighted = actions.get_option_index("version")
        await pilot.press("enter")
        await settle(pilot)
        assert isinstance(app.screen, FormScreen) and app.screen.command == "version"
        assert _text(app.screen, "#field-file-selected") == "Selected: ADR002V01-accepted.md"
        assert app.screen.query_one("#field-scope").value == "backend"  # as if picked by hand

    run_app(app, scenario)


def test_a_decision_s_detail_shows_its_content_without_control_characters(repo, user_state, client):
    created = client.run("new", ("--path", str(repo), "--title", "Use PostgreSQL")).data["created"]
    with open(created, "a", encoding="utf-8") as file:
        file.write("\nPlain line.\x1b]0;owned\x07\n")
    app = AdrpyTui(repo, user_state=user_state)

    async def scenario(pilot):
        await _open_group_item(pilot, "explore", "explore")
        app.screen.query_one("#decisions", OptionList).focus()
        await pilot.press("enter")
        await settle(pilot)
        source = app.screen.query_one(Markdown).source
        assert "Plain line.]0;owned" in source and "\x1b" not in source and "\x07" not in source

    run_app(app, scenario)


def test_explore_and_its_detail_show_what_a_command_run_from_there_changed(repo, user_state, client):
    client.run("new", ("--path", str(repo), "--title", "Use PostgreSQL"))
    app = AdrpyTui(repo, user_state=user_state)

    async def scenario(pilot):
        await _open_group_item(pilot, "explore", "explore")
        app.screen.query_one("#decisions", OptionList).focus()
        await pilot.press("enter")  # the detail of ADR001, Proposed
        await settle(pilot)
        await pilot.press("enter")  # its first action: Approve
        await settle(pilot)
        await pilot.press("ctrl+r")
        await pilot.pause()
        await pilot.press("enter")  # Yes
        await settle(pilot)
        assert app.screen.result.success, app.screen.result
        await pilot.press("escape")  # back to the detail
        await settle(pilot)
        assert isinstance(app.screen, DetailScreen)
        assert "Status: Accepted" in [str(s.render()) for s in app.screen.query(".info").results(Static)]
        await pilot.press("escape")  # back to the list
        await settle(pilot)
        assert "Accepted" in _rows(app.screen.query_one("#decisions", OptionList))[0]

    run_app(app, scenario)


def test_check_says_a_consistent_repository_is_consistent(repo, user_state, client):
    client.run("new", ("--path", str(repo), "--title", "Use PostgreSQL"))
    app = AdrpyTui(repo, user_state=user_state)

    async def scenario(pilot):
        await _open_group_item(pilot, "explore", "check")
        assert isinstance(app.screen, CheckScreen)
        assert _text(app.screen, ".title") == "No inconsistencies in 1 decisions."

    run_app(app, scenario)


def test_check_lists_every_inconsistency_with_adrpy_s_hint(tmp_path, user_state):
    failure = {"success": False, "code": "repository-inconsistent", "detail": "2 rules broken.", "warnings": [],
               "data": {"errors": [
                   {"code": "duplicate-number", "file": "C:\\r\\doc\\adr\\ADR001V01-b.md",
                    "related_files": ["C:\\r\\doc\\adr\\ADR001V01-a.md"], "detail": None, "hint": "Renumber one."},
                   {"code": "no-header", "file": "/r/doc/adr/ADR002V01-c.md", "hint": "Run migrate."},
               ]}}
    client = FakeClient(answers={"check": failure})
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _open_group_item(pilot, "explore", "check")
        errors = app.screen.query_one("#errors-options", OptionList)
        assert _rows(errors) == ["ADR001V01-b.md · duplicate-number", "ADR002V01-c.md · no-header"]
        assert _text(app.screen, "#errors-hint") == "Renumber one.\nRelated: ADR001V01-a.md"
        errors.focus()
        await pilot.press("down")
        assert _text(app.screen, "#errors-hint") == "Run migrate."

    run_app(app, scenario)
    assert client.verbs().count("check") == 1  # once as it opens


async def _open_init(pilot):
    await _open_group_item(pilot, "repository", "init")
    assert isinstance(pilot.app.screen, FormScreen) and pilot.app.screen.command == "init"


def test_init_shows_the_field_of_the_chosen_source_only(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(answers=NOT_CONFIGURED), user_state=user_state)

    async def scenario(pilot):
        await _open_init(pilot)
        screen = app.screen
        assert screen.query_one("#field-language").value == "en-us"  # the interface's language
        assert (screen.query_one("#row-language").display, screen.query_one("#row-seed").display) == (True, False)
        screen.query_one("#source-seed").value = True
        await pilot.pause()
        assert (screen.query_one("#row-language").display, screen.query_one("#row-seed").display) == (False, True)
        assert not screen.query("#form-warning")  # not initialized yet

    run_app(app, scenario)


def test_init_from_a_seed_needs_an_existing_file(tmp_path, user_state):
    client = FakeClient(answers=NOT_CONFIGURED)
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _open_init(pilot)
        app.screen.query_one("#source-seed").value = True
        app.screen.query_one("#field-seed").value = str(tmp_path / "missing.json")
        await pilot.press("ctrl+r")
        await pilot.pause()
        assert _text(app.screen, "#problem-seed").startswith("File not found: ")

    run_app(app, scenario)
    assert "init" not in client.verbs()


def test_init_warns_when_the_repository_is_already_initialized(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        await _open_init(pilot)
        assert "already has adr-config.adrplus" in _text(app.screen, "#form-warning")

    run_app(app, scenario)


def test_init_through_adrpy_enables_the_menus_that_need_a_repository(tmp_path, user_state, client):
    app = AdrpyTui(tmp_path, user_state=user_state)

    async def scenario(pilot):
        assert _options(app.screen).get_option("decisions").disabled
        await _open_init(pilot)
        app.screen.query_one("#field-language").value = "pt-br"
        await pilot.press("ctrl+r")
        await pilot.pause()
        assert _text(app.screen, "#command-line").endswith("--language pt-br")
        await pilot.press("enter")  # Yes
        await settle(pilot)
        assert app.screen.result.success, app.screen.result
        await pilot.press("escape")  # the repository is read again
        await settle(pilot)
        assert isinstance(app.screen, MenuScreen) and app.screen.menu.id == "main"
        assert not _options(app.screen).get_option("decisions").disabled

    run_app(app, scenario)
    assert client.run("config", ("--path", str(tmp_path))).data["config"]["statusnew"] == "Proposto"


REPO_CONFIG = {"folderadr": "doc/adr", "folderlog": "doc/decision-log", "prefix": "ADR", "separator": "-",
               "casetransform": "KebabCase", "lenseq": 3, "lenversion": 2, "lenrevision": 0,
               "statusnew": "Proposed", "statusacc": "Accepted", "statusrej": "Rejected", "statussup": "Superseded",
               "headerscope": "Scope", "template": "---\n# [Title]\n\nBody", "migrationpattern": "",
               "disableplugins": False}


def _config_client(**answers):
    return FakeClient(answers={"config": {"success": True, "data": {"config": REPO_CONFIG, "warnings": []}}, **answers})


async def _open_config(pilot):
    await _open_group_item(pilot, "repository", "config")
    assert isinstance(pilot.app.screen, ConfigScreen)
    return pilot.app.screen.query_one("#fields", OptionList)


async def _edit(pilot, fields, flag):
    fields.focus()
    fields.highlighted = fields.get_option_index(flag)
    await pilot.press("enter")
    await pilot.pause()
    assert isinstance(pilot.app.screen, FieldEditScreen)
    return pilot.app.screen.query_one("#editor")


def test_config_lists_the_fields_in_groups_with_their_values(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=_config_client(), user_state=user_state)

    async def scenario(pilot):
        fields = await _open_config(pilot)
        rows = _rows(fields)
        assert rows[0] == "— Folders —" and fields.get_option_at_index(0).disabled
        assert "Decisions folder: doc/adr" in rows
        assert "Template for new decisions: --- …" in rows
        assert "Plugins disabled: false" in rows
        assert "Legacy name pattern: —" in rows
        fields.highlighted = fields.get_option_index("statusnew")
        await pilot.pause()
        assert "Guarded" in _text(app.screen, "#field-description")

    run_app(app, scenario)


def test_config_saves_only_the_changed_fields_in_one_command(tmp_path, user_state):
    client = _config_client()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        fields = await _open_config(pilot)
        editor = await _edit(pilot, fields, "headerscope")
        editor.value = "Escopo"
        await pilot.press("enter")
        await pilot.pause()
        assert "\"Scope\" row: Escopo •" in _rows(fields)
        editor = await _edit(pilot, fields, "separator")
        editor.value = "_"
        await pilot.press("tab", "enter")  # OK
        await pilot.pause()
        editor = await _edit(pilot, fields, "disableplugins")
        editor.value = True
        await pilot.press("tab", "enter")
        await pilot.pause()
        await pilot.press("ctrl+r")
        await pilot.pause()
        line = _text(app.screen, "#command-line")
        assert line.startswith("adrpy config --path ")
        assert line.endswith("--separator _ --headerscope Escopo --disableplugins true")

    run_app(app, scenario)


def test_setting_a_field_back_to_its_value_is_no_change(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=_config_client(), user_state=user_state)

    async def scenario(pilot):
        fields = await _open_config(pilot)
        editor = await _edit(pilot, fields, "headerscope")
        editor.value = "Other"
        await pilot.press("enter")
        editor = await _edit(pilot, fields, "headerscope")
        editor.value = "Scope"
        await pilot.press("enter")
        await pilot.pause()
        assert "\"Scope\" row: Scope" in _rows(fields)
        await pilot.press("ctrl+r")
        await pilot.pause()
        assert isinstance(app.screen, ConfigScreen)  # nothing to save, nothing to confirm

    run_app(app, scenario)


def test_the_template_is_edited_in_a_text_area(tmp_path, user_state):
    from textual.widgets import TextArea

    app = AdrpyTui(tmp_path, client=_config_client(), user_state=user_state)

    async def scenario(pilot):
        fields = await _open_config(pilot)
        editor = await _edit(pilot, fields, "template")
        assert isinstance(editor, TextArea) and editor.text == "---\n# [Title]\n\nBody"

    run_app(app, scenario)


def test_a_crlf_template_opened_and_left_as_it_is_is_no_change(tmp_path, user_state):
    """A repository seeded from adrpy-ai's own config keeps a CRLF template.
    Suspected: the text area would hand it back with LF, marking it changed
    and rewriting it on save. It does not -- TextArea keeps the line endings
    of the text it was given -- and this test pins that."""
    crlf = {**REPO_CONFIG, "template": "---" + chr(13) + chr(10) + "# [Title]" + chr(13) + chr(10) + "Body"}
    client = FakeClient(answers={"config": {"success": True, "data": {"config": crlf, "warnings": []}}})
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        fields = await _open_config(pilot)
        await _edit(pilot, fields, "template")
        app.screen.query_one("#ok").press()
        await pilot.pause()
        assert not any(row.endswith("•") for row in _rows(fields) if row.startswith("Template"))
        await pilot.press("ctrl+r")
        await pilot.pause()
        assert isinstance(app.screen, ConfigScreen)  # nothing changed, nothing to confirm

    run_app(app, scenario)


def test_an_edited_crlf_template_keeps_its_line_endings(tmp_path, user_state):
    crlf = {**REPO_CONFIG, "template": "---" + chr(13) + chr(10) + "Body"}
    client = FakeClient(answers={"config": {"success": True, "data": {"config": crlf, "warnings": []}}})
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        fields = await _open_config(pilot)
        editor = await _edit(pilot, fields, "template")
        editor.text = "---" + chr(10) + "Body changed"
        app.screen.query_one("#ok").press()
        await pilot.pause()
        assert app.screen._save_flags()[-2:] == ["--template", "---" + chr(13) + chr(10) + "Body changed"]

    run_app(app, scenario)


def test_leaving_with_changes_asks_first(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=_config_client(), user_state=user_state)

    async def scenario(pilot):
        fields = await _open_config(pilot)
        editor = await _edit(pilot, fields, "headerscope")
        editor.value = "Escopo"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmScreen)
        await pilot.press("tab", "enter")  # No
        await pilot.pause()
        assert isinstance(app.screen, ConfigScreen)
        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("enter")  # Yes, leave
        await pilot.pause()
        assert isinstance(app.screen, MenuScreen)

    run_app(app, scenario)


def test_config_through_adrpy_changes_the_repository_and_reads_it_again(repo, user_state, client):
    app = AdrpyTui(repo, user_state=user_state)

    async def scenario(pilot):
        fields = await _open_config(pilot)
        editor = await _edit(pilot, fields, "statusnew")
        editor.value = "Proposto"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("ctrl+r")
        await pilot.pause()
        await pilot.press("enter")  # Yes
        await settle(pilot)
        assert app.screen.result.success, app.screen.result
        await pilot.press("escape")
        await settle(pilot)
        assert isinstance(app.screen, MenuScreen) and app.labels["Proposed"] == "Proposto"

    run_app(app, scenario)
    assert client.run("config", ("--path", str(repo))).data["config"]["statusnew"] == "Proposto"


def test_installconfig_without_one_offers_to_create_it_and_takes_no_path(tmp_path, user_state):
    """Only a fake client here: the real adrpy would write this machine's
    own install-level config."""
    client = FakeClient(answers={"installconfig": {"success": True, "data": {"configured": False, "warnings": []}}})
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _open_group_item(pilot, "install", "installconfig")
        assert "no install-level config" in _text(app.screen, "#install-missing")
        app.screen.query_one("#create-language-value").value = "de-de"
        app.screen.query_one("#create").press()
        await pilot.pause()
        assert _text(app.screen, "#command-line") == "adrpy installconfig --language de-de"

    run_app(app, scenario)


def test_installconfig_edits_the_install_level_config_without_a_path(tmp_path, user_state):
    client = FakeClient(answers={"installconfig": {"success": True, "data": {
        "configured": True, "config": REPO_CONFIG, "warnings": []}}})
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _open_group_item(pilot, "install", "installconfig")
        fields = app.screen.query_one("#fields", OptionList)
        editor = await _edit(pilot, fields, "prefix")
        editor.value = "DEC"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("ctrl+r")
        await pilot.pause()
        assert _text(app.screen, "#command-line") == "adrpy installconfig --prefix DEC"

    run_app(app, scenario)
    assert all("--path" not in argv for argv in client.calls if "installconfig" in argv)


def _legacy_repo(client, root, names=("0001-use-postgres.md", "0002-adopt-kafka.md")):
    from conftest import FIXTURE_CONFIG

    assert client.run("init", ("--path", str(root), "--seed", str(FIXTURE_CONFIG))).success
    folder = root / "doc" / "adr"
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        (folder / name).write_text(f"# {name}\n", encoding="utf-8")
    return root


async def _open_migrate(pilot):
    await _open_group_item(pilot, "repository", "migrate")
    assert isinstance(pilot.app.screen, MigrateScreen)
    return pilot.app.screen


def test_migrate_proposes_a_pattern_and_shows_what_each_part_reads(tmp_path, user_state, client):
    _legacy_repo(client, tmp_path)
    app = AdrpyTui(tmp_path, user_state=user_state)

    async def scenario(pilot):
        screen = await _open_migrate(pilot)
        assert _rows(screen.query_one("#files", OptionList)) == ["0001-use-postgres.md", "0002-adopt-kafka.md"]
        assert _text(screen, "#pattern") == "Pattern: N00:04T05"
        assert _text(screen, "#reads-N") == "reads: 0001"
        assert _text(screen, "#reads-T") == "reads: use-postgres"
        assert _text(screen, "#reads-V") == ""  # optional, off
        screen.query_one("#start-T").value = 4
        await pilot.pause()
        assert (_text(screen, "#pattern"), _text(screen, "#reads-T")) == ("Pattern: N00:04T04", "reads: -use-postgres")

    run_app(app, scenario)


def test_migrate_previews_what_adrpy_reads_from_every_file(tmp_path, user_state, client):
    _legacy_repo(client, tmp_path)
    app = AdrpyTui(tmp_path, user_state=user_state)

    async def scenario(pilot):
        screen = await _open_migrate(pilot)
        screen.query_one("#preview").press()
        await settle(pilot)
        assert _rows(screen.query_one("#preview-options", OptionList)) == [
            "0001-use-postgres.md · N 1 · V 0 · use-postgres",
            "0002-adopt-kafka.md · N 2 · V 0 · adopt-kafka",
        ]

    run_app(app, scenario)


def test_migrate_through_adrpy_saves_the_pattern_then_migrates(tmp_path, user_state, client):
    _legacy_repo(client, tmp_path)
    app = AdrpyTui(tmp_path, user_state=user_state)

    async def scenario(pilot):
        await _open_migrate(pilot)
        await pilot.press("ctrl+r")
        await pilot.pause()
        lines = _text(app.screen, "#command-line").splitlines()
        assert lines[0].startswith("adrpy config --path ") and lines[0].endswith("--migrationpattern N00:04T05")
        assert lines[1].startswith("adrpy migrate --path ")
        await pilot.press("enter")  # Yes
        await settle(pilot)
        assert app.screen.result.success, app.screen.result

    run_app(app, scenario)
    decisions = client.run("explore", ("--path", str(tmp_path))).data["decisions"]
    assert len(decisions) == 2 and all(d["header"]["is_migrated"] for d in decisions)


def test_migrate_does_not_run_when_saving_the_pattern_fails(tmp_path, user_state):
    config = {"success": True, "data": {"config": {"folderadr": "doc/adr", "migrationpattern": ""}, "warnings": []}}
    refused = {"success": False, "code": "config-migrationpattern-invalid", "detail": "T starts inside N."}
    client = FakeClient(answers={"config": config, "explore": {"success": True, "data": {"decisions": [], "warnings": []}}})
    (tmp_path / "doc" / "adr").mkdir(parents=True)
    (tmp_path / "doc" / "adr" / "0001-x.md").write_text("# x\n", encoding="utf-8")
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _open_migrate(pilot)
        client.answers["config"] = refused  # the startup read succeeded; saving is refused
        await pilot.press("ctrl+r")
        await pilot.pause()
        await pilot.press("enter")
        await settle(pilot)
        assert (app.screen.result.code, app.screen.command) == ("config-migrationpattern-invalid", "config")

    run_app(app, scenario)
    assert "migrate" not in client.verbs()


def test_migrate_says_so_when_there_is_nothing_to_migrate(repo, user_state):
    app = AdrpyTui(repo, user_state=user_state)

    async def scenario(pilot):
        screen = await _open_migrate(pilot)
        assert "No hand-written files to migrate" in _text(screen, ".info:last-of-type")

    run_app(app, scenario)


async def _open_log(pilot):
    await _open_group_item(pilot, "log", "log")
    assert isinstance(pilot.app.screen, FormScreen) and pilot.app.screen.command == "log"
    return pilot.app.screen


def _displayed(screen, *flags):
    return tuple(screen.query_one(f"#row-{flag}").display for flag in flags)


def test_log_shows_the_fields_each_classification_takes(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)
    finding = ("front", "severity", "resolution", "round")

    async def scenario(pilot):
        screen = await _open_log(pilot)
        assert _displayed(screen, *finding, "reopenwhen") == (False,) * 5  # scope-note
        screen.query_one("#field-classification").value = "audit-finding"
        await pilot.pause()
        assert _displayed(screen, *finding, "reopenwhen") == (True,) * 4 + (False,)
        screen.query_one("#field-classification").value = "deferred"
        await pilot.pause()
        assert _displayed(screen, *finding, "reopenwhen") == (False,) * 4 + (True,)

    run_app(app, scenario)


def test_log_scope_and_slug_take_kebab_case_only(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        screen = await _open_log(pilot)
        screen.query_one("#field-slug").focus()
        await pilot.press(*"Use Postgres-2")
        assert screen.query_one("#field-slug").value == "seostgres-2"  # the capitals and the space refused

    run_app(app, scenario)


def test_a_deferred_entry_needs_its_reopening_condition(tmp_path, user_state):
    client = FakeClient()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        screen = await _open_log(pilot)
        screen.query_one("#field-classification").value = "deferred"
        for flag, value in (("scope", "packaging"), ("slug", "later"), ("summary", "Later")):
            screen.query_one(f"#field-{flag}").value = value
        screen.query_one("#field-body").text = "Why."
        await pilot.press("ctrl+r")
        await pilot.pause()
        assert _text(screen, "#problem-reopenwhen") == "Required."

    run_app(app, scenario)
    assert "log" not in client.verbs()


def test_an_audit_finding_through_adrpy(repo, user_state, client):
    assert client.run("config", ("--path", str(repo), "--folderlog", "doc/decision-log")).success
    app = AdrpyTui(repo, user_state=user_state)

    async def scenario(pilot):
        screen = await _open_log(pilot)
        screen.query_one("#field-classification").value = "audit-finding"
        await pilot.pause()
        for flag, value in (("scope", "security"), ("slug", "no-expiry"), ("summary", "Sessions never expire"),
                            ("front", "stability")):
            screen.query_one(f"#field-{flag}").value = value
        screen.query_one("#field-body").text = "Found in review."
        screen.query_one("#field-severity").value = "High"
        await pilot.press("ctrl+r")
        await pilot.pause()
        line = _text(app.screen, "#command-line")
        assert "--severity High --resolution Direct" in line and "--round" not in line and "--reopenwhen" not in line
        await pilot.press("enter")
        await settle(pilot)
        assert app.screen.result.success, app.screen.result

    run_app(app, scenario)
    entries = [p.name for p in (repo / "doc" / "decision-log").glob("*.md") if p.name != "INDEX.md"]
    assert len(entries) == 1 and entries[0].endswith("--audit-finding--security--no-expiry.md")


async def _open_skills(pilot, item):
    await _open_group_item(pilot, "skills", item)
    return pilot.app.screen


def test_skills_install_sends_the_chosen_providers_comma_separated(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        screen = await _open_skills(pilot, "install")
        providers = screen.query_one("#field-provider")
        providers.select("cursor")
        providers.select("claude")
        await pilot.press("ctrl+r")
        await pilot.pause()
        line = _text(app.screen, "#command-line")
        assert line.startswith("adrpy-skills install --path ")
        assert line.endswith("--provider claude,cursor --target project")  # the order of the list, no --skill

    run_app(app, scenario)


def test_skills_install_globally_is_only_sent_to_a_fake_here(tmp_path, user_state):
    """The real adrpy-skills would write to this user's own ~/.claude."""
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        screen = await _open_skills(pilot, "install")
        screen.query_one("#target-global").value = True
        await pilot.press("ctrl+r")
        await pilot.pause()
        assert _text(app.screen, "#command-line").endswith("--target global")

    run_app(app, scenario)


def test_skills_install_list_and_remove_through_adrpy_skills(repo, user_state, client):
    app = AdrpyTui(repo, user_state=user_state)

    async def run(pilot, item):
        screen = await _open_skills(pilot, item)
        screen.query_one("#field-provider").select("claude")
        screen.query_one("#field-skill").select("adrpy")
        await pilot.press("ctrl+r")
        await pilot.pause()
        await pilot.press("enter")
        await settle(pilot)
        assert app.screen.result.success, app.screen.result
        await pilot.press("escape", "escape")
        await pilot.pause()

    async def listed(pilot):
        screen = await _open_skills(pilot, "list")
        rows = _rows(screen.query_one("#skills", OptionList))
        await pilot.press("escape", "escape")
        await pilot.pause()
        return [row for row in rows if row.startswith("adrpy claude project")][0]

    async def scenario(pilot):
        assert "not installed" in await listed(pilot)
        await run(pilot, "install")
        assert (repo / ".claude" / "skills" / "adrpy" / "SKILL.md").is_file()
        assert "not installed" not in await listed(pilot)
        await run(pilot, "remove")
        assert not (repo / ".claude" / "skills" / "adrpy" / "SKILL.md").exists()

    run_app(app, scenario)


async def _open_change_repository(pilot):
    options = _options(pilot.app.screen)
    options.highlighted = options.get_option_index("change-repository")
    await pilot.press("enter")
    await pilot.pause()
    assert isinstance(pilot.app.screen, RepositoryScreen)
    return pilot.app.screen


def test_change_repository_works_on_the_chosen_folder_from_then_on(tmp_path, repo, user_state):
    other = tmp_path / "other"
    other.mkdir()
    app = AdrpyTui(other, user_state=user_state)

    async def scenario(pilot):
        assert _options(app.screen).get_option("decisions").disabled  # "other" is not initialized
        screen = await _open_change_repository(pilot)
        assert screen.query_one("#repository-path").value == str(other.resolve())
        screen.query_one("#repository-path").value = str(repo)
        await pilot.press("ctrl+r")
        await settle(pilot)
        assert isinstance(app.screen, MenuScreen) and app.repo == repo.resolve()
        assert not _options(app.screen).get_option("decisions").disabled
        header = " ".join(str(s.render()) for s in app.screen.query("AppHeader Static").results(Static))
        assert str(repo.resolve()) in header

    run_app(app, scenario)


def test_change_repository_refuses_what_is_not_a_folder(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        screen = await _open_change_repository(pilot)
        screen.query_one("#repository-path").value = str(tmp_path / "missing")
        await pilot.press("ctrl+r")
        await pilot.pause()
        assert _text(screen, "#problem-path").startswith("Not a folder: ")
        assert app.repo == tmp_path.resolve()

    run_app(app, scenario)


def test_choosing_a_folder_in_the_tree_fills_the_path(tmp_path, user_state):
    from textual.widgets import DirectoryTree

    (tmp_path / "sibling").mkdir()
    here = tmp_path / "here"
    here.mkdir()
    app = AdrpyTui(here, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        screen = await _open_change_repository(pilot)
        tree = screen.query_one("#folders", DirectoryTree)
        await pilot.pause()
        names = [str(node.label) for node in tree.root.children]
        assert names == ["here", "sibling"]  # folders only
        tree.select_node(tree.root.children[1])
        await pilot.pause()
        assert screen.query_one("#repository-path").value == str(tmp_path / "sibling")

    run_app(app, scenario)


async def _open_colors(pilot):
    presets = await _open_appearance(pilot)
    presets.highlighted = presets.get_option_index("colors")
    await pilot.press("enter")
    await pilot.pause()
    assert isinstance(pilot.app.screen, ColorsScreen)
    return pilot.app.screen.query_one("#roles", OptionList)


async def _edit_color(pilot, roles, role, value, button="ok"):
    roles.highlighted = roles.get_option_index(role)
    await pilot.press("enter")
    await pilot.pause()
    assert isinstance(pilot.app.screen, ColorEditScreen)
    pilot.app.screen.query_one("#color").value = value
    await pilot.pause()
    note = _text(pilot.app.screen, "#color-note")
    pilot.app.screen.query_one(f"#{button}").press()
    # A new theme is applied asynchronously: wait for it to be painted, or a
    # loaded machine checks the color before it (seen under pytest-xdist).
    await settle(pilot)
    return note


def test_a_customized_color_is_shown_at_once_and_kept(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        roles = await _open_colors(pilot)
        assert await _edit_color(pilot, roles, "tui-banner", "#FFA500") == ""
        assert _banner_color(app) == "#FFA500"
        assert "Banner and command line: #FFA500 •" in _rows(roles)

    run_app(app, scenario)
    assert user_state.colors == {"tui-banner": "#FFA500"}


def test_a_customized_color_stays_on_top_of_another_preset(tmp_path, user_state):
    user_state.set_color("tui-banner", "#FFA500")
    user_state.set_appearance("light")
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        assert _banner_color(app) == "#FFA500"

    run_app(app, scenario)


def test_back_to_the_preset_and_restore_every_color(tmp_path, user_state):
    user_state.set_color("tui-banner", "#FFA500")
    user_state.set_color("tui-info", "#999999")
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        roles = await _open_colors(pilot)
        await _edit_color(pilot, roles, "tui-banner", "ignored", button="reset")
        assert _banner_color(app) == "#FF8C00" and user_state.colors == {"tui-info": "#999999"}
        roles.highlighted = roles.get_option_index("reset-all")
        await pilot.press("enter")
        await pilot.pause()
        assert user_state.colors == {}

    run_app(app, scenario)


def test_a_color_that_is_not_one_is_refused(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        roles = await _open_colors(pilot)
        note = await _edit_color(pilot, roles, "tui-banner", "orangey")
        assert note.startswith("Not a color: orangey")
        assert isinstance(app.screen, ColorEditScreen)  # still open: OK refused it

    run_app(app, scenario)
    assert user_state.colors == {}


def test_a_hard_to_read_color_is_warned_about_but_allowed(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        roles = await _open_colors(pilot)
        note = await _edit_color(pilot, roles, "tui-info", "#222222")  # on the dark background
        assert "below the 4.5:1 WCAG AA minimum" in note
        assert isinstance(app.screen, ColorsScreen)

    run_app(app, scenario)
    assert user_state.colors == {"tui-info": "#222222"}


def test_a_saved_color_that_cannot_be_read_is_ignored_and_said(tmp_path, user_state):
    user_state.set_color("tui-banner", "not-a-color")
    user_state.set_color("tui-info", "#999999")
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        assert _banner_color(app) == "#FF8C00"
        assert "tui-banner" in _text(app.screen, "#ignored-colors")

    run_app(app, scenario)


class BlockingOn(FakeClient):
    """Holds one command until `release` is set, as a slow adrpy would."""

    def __init__(self, command, answers=None):
        super().__init__(answers=answers or {})
        self.command = command
        self.release = threading.Event()

    def _answer(self, argv):
        verb = argv[4] if argv[2] == "adrpy.skills" else argv[3]
        if verb == self.command and self.calls_to(verb) >= self.reads_before:
            self.release.wait(timeout=10)
        return super()._answer(argv)

    reads_before = 0

    def calls_to(self, verb):
        return sum(1 for argv in self.calls if argv[3] == verb)


async def _keys_while_running(pilot, client):
    """Presses what could leave or run again while the command is held."""
    await pilot.press("escape", "ctrl+r", "enter", "escape")
    await pilot.pause()
    client.release.set()
    await settle(pilot)


def test_keys_pressed_while_config_saves_neither_leave_nor_save_again(tmp_path, user_state):
    client = BlockingOn("config", answers={"config": {"success": True, "data": {"config": REPO_CONFIG, "warnings": []}}})
    client.reads_before = 2  # the startup read and the editor's read are not held
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        fields = await _open_config(pilot)
        editor = await _edit(pilot, fields, "headerscope")
        editor.value = "Escopo"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("ctrl+r")
        await pilot.pause()
        await pilot.press("enter")  # Yes: config starts and is held
        await pilot.pause()
        await _keys_while_running(pilot, client)
        assert isinstance(app.screen, ResultScreen)
        assert [type(s).__name__ for s in app.screen_stack][-2:] == ["MenuScreen", "ResultScreen"]

    run_app(app, scenario)
    assert client.calls_to("config") == 3  # startup, editor, one save


def test_keys_pressed_while_installconfig_creates_neither_leave_nor_create_again(tmp_path, user_state):
    client = BlockingOn("installconfig",
                        answers={"installconfig": {"success": True, "data": {"configured": False, "warnings": []}}})
    client.reads_before = 1  # the editor's read is not held
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _open_group_item(pilot, "install", "installconfig")
        app.screen.query_one("#create").press()
        await pilot.pause()
        await pilot.press("enter")  # Yes: installconfig starts and is held
        await pilot.pause()
        await _keys_while_running(pilot, client)
        assert isinstance(app.screen, ResultScreen)
        assert [type(s).__name__ for s in app.screen_stack][-2:] == ["MenuScreen", "ResultScreen"]

    run_app(app, scenario)
    assert client.calls_to("installconfig") == 2  # the read, one create


def test_a_name_with_brackets_is_shown_as_it_is_everywhere(tmp_path, user_state):
    """Textual reads a string label as markup: "[red]x" would lose its
    brackets and turn red. Names come from files, so every list shows them
    as plain text."""
    name = "ADR001V01-use-[red]beta-api.md"  # brackets, no "/": a name cannot hold one
    decisions = [_decision(name, update="Accepted", updated="2026-02-01", scope="[b]x")]
    errors = [{"code": "no-header", "file": f"/r/{name}", "hint": "[i]hint[/i]"}]
    client = FakeClient(answers={
        "explore": {"success": True, "data": {"decisions": decisions, "warnings": []}},
        "check": {"success": False, "code": "repository-inconsistent", "detail": "x", "warnings": [],
                  "data": {"errors": errors}},
    })
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)
    shown = {}

    async def scenario(pilot):
        await _open_group_item(pilot, "explore", "explore")
        shown["explore"] = _rendered_rows(app.screen.query_one("#decisions", OptionList))
        await pilot.press("escape", "escape")
        await pilot.pause()
        await _open(pilot, "undo")
        shown["picker"] = _rendered_rows(app.screen.query_one("#field-file-options", OptionList))
        await pilot.press("escape", "escape")
        await pilot.pause()
        await _open_group_item(pilot, "explore", "check")
        shown["errors"] = _rendered_rows(app.screen.query_one("#errors-options", OptionList))

    run_app(app, scenario)
    assert all(name in rows for rows in shown.values()), shown
    assert "[b]x" in shown["explore"]


def _rendered_rows(options):
    """What the screen draws, as text, from a screenshot of it."""
    import html
    import re

    rows = {}
    svg = options.app.export_screenshot()
    for match in re.finditer(r'<text[^>]*?y="([\d.]+)"[^>]*>(.*?)</text>', svg):
        rows.setdefault(float(match.group(1)), []).append(html.unescape(re.sub(r"<[^>]+>", "", match.group(2))))
    return "\n".join("".join(parts) for _, parts in sorted(rows.items())).replace("\xa0", " ")


async def _open_keys(pilot):
    options = _options(pilot.app.screen)
    options.highlighted = options.get_option_index("keys")
    await pilot.press("enter")
    await settle(pilot)
    assert isinstance(pilot.app.screen, KeysScreen)
    return pilot.app.screen.query_one("#actions", OptionList)


async def _capture(pilot, actions, action, *pressed):
    actions.focus()
    actions.highlighted = actions.get_option_index(action)
    await pilot.press("enter")
    await pilot.pause()
    assert isinstance(pilot.app.screen, KeyCaptureScreen)
    await pilot.press(*pressed)
    await settle(pilot)


def test_a_new_key_runs_the_action_everywhere_and_the_key_line_says_it(tmp_path, user_state):
    client = FakeClient()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        actions = await _open_keys(pilot)
        await _capture(pilot, actions, "run", "f5")
        assert "Run the screen's action (run, save, migrate, use): F5 •" in _rows(actions)
        await pilot.press("escape")
        await pilot.pause()
        await _open_group_item(pilot, "decisions", "new")
        assert "F5 run" in _text(app.screen, "#hints") and "Ctrl+R" not in _text(app.screen, "#hints")
        app.screen.query_one("#field-title").value = "Anything"
        await pilot.press("ctrl+r")  # no longer the key
        await pilot.pause()
        assert isinstance(app.screen, FormScreen)
        await pilot.press("f5")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmScreen)

    run_app(app, scenario)
    assert user_state.keys == {"run": "f5"}


def test_a_chosen_key_is_used_again_in_the_next_session(tmp_path, user_state):
    user_state.set_key("preview", "f6")
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        actions = await _open_keys(pilot)
        assert "Preview a decision or log entry: F6 •" in _rows(actions)

    run_app(app, scenario)


def test_a_key_every_screen_relies_on_or_another_action_s_is_refused(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        actions = await _open_keys(pilot)
        await _capture(pilot, actions, "run", "tab")
        assert _text(app.screen, "#key-problem") == "Tab is one every screen relies on."
        await pilot.press("f3")  # the preview's
        await settle(pilot)
        assert _text(app.screen, "#key-problem") == "F3 is already the key of Preview a decision or log entry."
        await pilot.press("x")
        await settle(pilot)
        assert _text(app.screen, "#key-problem") == "X would be typed into a field."
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, KeysScreen)

    run_app(app, scenario)
    assert user_state.keys == {}


def test_backspace_and_restore_every_key_go_back_to_the_defaults(tmp_path, user_state):
    user_state.set_key("run", "f5")
    user_state.set_key("toggle", "f7")
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        actions = await _open_keys(pilot)
        await _capture(pilot, actions, "run", "backspace")
        assert user_state.keys == {"toggle": "f7"} and app.key_of("run") == "ctrl+r"
        actions.highlighted = actions.get_option_index("reset-all")
        await pilot.press("enter")
        await pilot.pause()
        assert user_state.keys == {} and app.key_of("toggle") == "f2"

    run_app(app, scenario)


def test_an_adrpy_outside_the_validated_range_is_said_on_the_main_menu(tmp_path, user_state, monkeypatch):
    """An adrpy-ai upgraded apart from the TUI (ADR003V01): a warning, and
    the TUI keeps working."""
    from adrpy_tui.core import versions

    monkeypatch.setattr(versions, "adrpy_outside_range", lambda: ("0.2.0", ">=0.1.dev0, <0.2"))
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        assert _text(app.screen, "#adrpy-outside-range") == (
            "adrpy-ai 0.2.0 is installed; this adrpy-tui was validated with adrpy-ai >=0.1.dev0, <0.2. "
            "Commands may fail; install a version in that range or update adrpy-tui.")
        assert _options(app.screen).option_count > 0

    run_app(app, scenario)


def test_an_adrpy_within_the_range_says_nothing(tmp_path, user_state, monkeypatch):
    from adrpy_tui.core import versions

    monkeypatch.setattr(versions, "adrpy_outside_range", lambda: None)
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        assert not app.screen.query("#adrpy-outside-range")

    run_app(app, scenario)


def test_a_saved_key_that_cannot_be_used_is_ignored_and_said(tmp_path, user_state):
    user_state.set_key("run", "escape")
    user_state.set_key("nonsense", "f9")
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        assert app.key_of("run") == "ctrl+r"
        assert _text(app.screen, "#ignored-keys") == "A saved key could not be used and is ignored: run, nonsense."

    run_app(app, scenario)


def test_the_key_lines_read_as_before_in_the_interface_s_language(tmp_path, user_state):
    """The key line is built from keys and hints now; in Portuguese it reads
    as the fixed texts did."""
    user_state.set_language("pt-br")
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        assert _text(app.screen, "#hints") == "↑↓ mover · Enter selecionar · Esc sair"
        await _open_group_item(pilot, "decisions", "new")
        assert _text(app.screen, "#hints") == "Tab próximo campo · → aceitar sugestão · Ctrl+R executar · Esc voltar"

    run_app(app, scenario)


def test_f2_shows_every_decision_and_says_what_it_hides(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=_client_with(DECISIONS), user_state=user_state)

    async def scenario(pilot):
        options = await _open(pilot, "approve")
        assert options.option_count == 2
        assert _text(app.screen, "#field-file-filter-note") == \
            "2 of 4 decisions (only the available ones · F2 shows all)"
        app.screen.query_one("#field-refdate").focus()
        await pilot.press("f2")  # from any field of the form, not only the list
        await settle(pilot)
        assert options.option_count == 4
        assert _text(app.screen, "#field-file-filter-note") == "4 decisions, all shown (F2: only the available ones)"
        assert "F2 all / only available" in _text(app.screen, "#hints")

    run_app(app, scenario)


def _repo_with_linked_decisions(client, root):
    """Two decisions, the second linking to the first as ADR Links do."""
    from conftest import FIXTURE_CONFIG

    assert client.run("init", ("--path", str(root), "--seed", str(FIXTURE_CONFIG))).success
    first = pathlib.Path(client.run("new", ("--path", str(root), "--title", "Use PostgreSQL")).data["created"])
    second = pathlib.Path(client.run("new", ("--path", str(root), "--title", "Add replicas")).data["created"])
    with open(second, "a", encoding="utf-8") as file:
        file.write(f"\n## Links\n\n* Refines [{first.stem}]({first.name})\n")
    return first, second


async def _preview_from_explore(pilot, name_start):
    await _open_group_item(pilot, "explore", "explore")
    decisions = pilot.app.screen.query_one("#decisions", OptionList)
    decisions.focus()
    decisions.highlighted = next(i for i in range(decisions.option_count)
                                 if str(decisions.get_option_at_index(i).prompt).startswith(name_start))
    await pilot.press("f3")
    await settle(pilot)
    assert isinstance(pilot.app.screen, PreviewScreen)


def test_f3_previews_the_highlighted_decision_and_esc_comes_back(repo, user_state, client):
    first, _ = _repo_with_linked_decisions(client, repo)
    app = AdrpyTui(repo, user_state=user_state)

    async def scenario(pilot):
        await _preview_from_explore(pilot, "ADR001")
        assert app.screen.path == first
        assert "Use PostgreSQL" in app.screen.query_one(Markdown).source
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, ExploreScreen)

    run_app(app, scenario)


def test_a_link_to_another_decision_opens_its_preview_like_a_browser(repo, user_state, client):
    first, second = _repo_with_linked_decisions(client, repo)
    app = AdrpyTui(repo, user_state=user_state)

    async def scenario(pilot):
        await _preview_from_explore(pilot, "ADR002")
        assert app.screen.path == second
        app.screen.query_one(Markdown).post_message(Markdown.LinkClicked(app.screen.query_one(Markdown), first.name))
        await settle(pilot)
        assert isinstance(app.screen, PreviewScreen) and app.screen.path == first
        await pilot.press("escape")
        await pilot.pause()
        assert app.screen.path == second  # back, as a browser does

    run_app(app, scenario)


def test_a_web_link_is_never_opened(repo, user_state, client, monkeypatch):
    _repo_with_linked_decisions(client, repo)
    app = AdrpyTui(repo, user_state=user_state)
    opened = []
    monkeypatch.setattr(app, "open_url", lambda url, **kwargs: opened.append(url))

    async def scenario(pilot):
        await _preview_from_explore(pilot, "ADR001")
        markdown = app.screen.query_one(Markdown)
        markdown.post_message(Markdown.LinkClicked(markdown, "https://example.com/x"))
        await settle(pilot)
        assert isinstance(app.screen, PreviewScreen)

    run_app(app, scenario)
    assert opened == []


def test_f3_in_the_picker_previews_the_decision_before_choosing_it(repo, user_state, client):
    first, _ = _repo_with_linked_decisions(client, repo)
    app = AdrpyTui(repo, user_state=user_state)

    async def scenario(pilot):
        options = await _open(pilot, "approve")
        options.focus()
        options.highlighted = 0
        await pilot.press("f3")
        await settle(pilot)
        assert isinstance(app.screen, PreviewScreen) and app.screen.path == first
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, FormScreen)
        assert app.screen.query_one("#field-file").selected is None  # previewing is not choosing

    run_app(app, scenario)


def test_f3_on_a_result_previews_the_file_the_command_wrote(repo, user_state):
    app = AdrpyTui(repo, user_state=user_state)

    async def scenario(pilot):
        await _open_group_item(pilot, "decisions", "new")
        app.screen.query_one("#field-title").value = "Use PostgreSQL"
        await pilot.press("ctrl+r")
        await pilot.pause()
        await pilot.press("enter")
        await settle(pilot)
        assert isinstance(app.screen, ResultScreen)
        await pilot.press("f3")
        await settle(pilot)
        assert isinstance(app.screen, PreviewScreen) and app.screen.path.name == "ADR001V01-use-postgre-sql.md"

    run_app(app, scenario)


def _repo_with_subfolders(client, root):
    """Decisions in the decisions folder and in two levels of subfolders,
    which adrpy finds too."""
    from conftest import FIXTURE_CONFIG

    assert client.run("init", ("--path", str(root), "--seed", str(FIXTURE_CONFIG))).success
    top = client.run("new", ("--path", str(root), "--title", "Top level")).data["created"]
    for title, folder in (("In backend", "backend"), ("In data", "backend/data")):
        created = pathlib.Path(client.run("new", ("--path", str(root), "--title", title)).data["created"])
        (root / "doc" / "adr" / folder).mkdir(parents=True, exist_ok=True)
        created.rename(root / "doc" / "adr" / folder / created.name)
    return top


def test_explore_shows_each_decision_s_folder_and_filters_by_it(repo, user_state, client):
    _repo_with_subfolders(client, repo)
    app = AdrpyTui(repo, user_state=user_state)

    async def scenario(pilot):
        await _open_group_item(pilot, "explore", "explore")
        decisions = app.screen.query_one("#decisions", OptionList)
        assert _rows(decisions) == [
            "ADR001V01-top-level.md . Proposed",
            "ADR002V01-in-backend.md backend Proposed",
            "ADR003V01-in-data.md backend/data Proposed",
        ]
        folder = app.screen.query_one("#explore-folder")
        folder.value = "backend"
        await settle(pilot)
        assert _rows(decisions) == ["ADR002V01-in-backend.md backend Proposed"]
        assert _text(app.screen, "#explore-count") == "1 of 3 decisions"
        folder.value = "*"
        app.screen.query_one("#explore-filter").value = "data"
        await settle(pilot)
        assert _rows(decisions) == ["ADR003V01-in-data.md backend/data Proposed"]  # the folder matches too

    run_app(app, scenario)


def _repo_with_log_entries(client, root):
    from conftest import FIXTURE_CONFIG

    assert client.run("init", ("--path", str(root), "--seed", str(FIXTURE_CONFIG))).success
    assert client.run("config", ("--path", str(root), "--folderlog", "doc/decision-log")).success
    path = ("--path", str(root))
    for flags in (
        ("--classification", "scope-note", "--scope", "backend", "--slug", "first-note", "--summary", "First note",
         "--body", "Body.", "--refdate", "2026-02-04"),
        ("--classification", "deferred", "--scope", "packaging", "--slug", "later", "--summary", "Later",
         "--body", "Why.", "--reopenwhen", "adrpy-ai is on PyPI", "--refdate", "2026-02-05"),
    ):
        assert client.run("log", (*path, *flags)).success


async def _open_log_browser(pilot):
    await _open_group_item(pilot, "log", "browse")
    assert isinstance(pilot.app.screen, LogScreen)
    return pilot.app.screen.query_one("#entries", OptionList)


def test_the_log_browser_lists_every_entry_and_filters_by_classification(repo, user_state, client):
    _repo_with_log_entries(client, repo)
    app = AdrpyTui(repo, user_state=user_state)

    async def scenario(pilot):
        entries = await _open_log_browser(pilot)
        assert _rows(entries) == ["2026-02-04 scope-note backend first-note",
                                  "2026-02-05 deferred packaging later"]  # no INDEX.md
        app.screen.query_one("#logs-classification").value = "deferred"
        await settle(pilot)
        assert _rows(entries) == ["2026-02-05 deferred packaging later"]
        assert _text(app.screen, "#logs-count") == "1 of 2 entries"

    run_app(app, scenario)


def test_enter_opens_an_entry_rendered(repo, user_state, client):
    _repo_with_log_entries(client, repo)
    app = AdrpyTui(repo, user_state=user_state)

    async def scenario(pilot):
        await _open_log_browser(pilot)
        await pilot.press("down", "enter")
        await settle(pilot)
        assert isinstance(app.screen, PreviewScreen)
        assert app.screen.path.name == "2026-02-05--deferred--packaging--later.md"
        assert "Later" in app.screen.query_one(Markdown).source

    run_app(app, scenario)


def test_the_log_browser_says_so_when_there_is_no_entry(repo, user_state):
    app = AdrpyTui(repo, user_state=user_state)

    async def scenario(pilot):
        await _open_log_browser(pilot)
        assert _text(app.screen, "#entries-page").startswith("No entries in ")

    run_app(app, scenario)


def test_explore_opens_with_the_list_taking_the_arrow_keys(tmp_path, user_state):
    """Reported: the arrows did not move explore's list, only the mouse did --
    the focus was on the scrolling body, not on the list."""
    app = AdrpyTui(tmp_path, client=_client_with(CHANGE_DECISIONS), user_state=user_state)

    async def scenario(pilot):
        await _open_group_item(pilot, "explore", "explore")
        decisions = app.screen.query_one("#decisions", OptionList)
        assert decisions.highlighted == 0
        await pilot.press("down", "down")
        assert decisions.highlighted == 2

    run_app(app, scenario)


@pytest.mark.parametrize("where", ["explore", "picker", "logs"])
def test_the_arrow_keys_typed_in_a_filter_move_its_list(tmp_path, user_state, where):
    """As in a search box: typing filters, the arrows move the list below."""
    app = AdrpyTui(tmp_path, client=_client_with(CHANGE_DECISIONS), user_state=user_state)

    async def scenario(pilot):
        if where == "explore":
            await _open_group_item(pilot, "explore", "explore")
            filter_id, list_id = "#explore-filter", "#decisions"
        elif where == "picker":
            await _open(pilot, "undo")
            await _show_all(pilot)
            filter_id, list_id = "#field-file-filter", "#field-file-options"
        else:
            folder = tmp_path / "doc" / "decision-log"
            folder.mkdir(parents=True)
            for n in range(3):
                (folder / f"2026-02-0{n + 1}--scope-note--backend--n{n}.md").write_text("# x\n", encoding="utf-8")
            await _open_group_item(pilot, "log", "browse")
            filter_id, list_id = "#logs-filter", "#entries"
        app.screen.query_one(filter_id).focus()
        await pilot.press("down")
        assert app.screen.query_one(list_id, OptionList).highlighted == 1
        assert app.focused is app.screen.query_one(filter_id)  # still typing in the filter

    run_app(app, scenario)


# The screens a person reaches, each as the path of menu items to it (":x"
# for a step of the screen itself), and what it offers the keys when it
# opens: a list the arrows move, a field to type in, or text to scroll.
FOCUS_SCREENS = {
    "main menu": ([], "list"),
    "submenu": (["decisions"], "list"),
    "new": (["decisions", "decisions.new"], "field"),
    "approve": (["decisions", "decisions.approve"], "list"),
    "supersede": (["decisions", "decisions.supersede"], "list"),
    "explore": (["explore", "explore.explore"], "list"),
    "explore detail": (["explore", "explore.explore", ":detail"], "list"),
    "check with errors": (["explore", "explore.check"], "list"),
    "log new": (["log", "log.log"], "field"),
    "log browse": (["log", "log.browse"], "list"),
    "init": (["repository", "repository.init"], "field"),
    "config": (["repository", "repository.config"], "list"),
    "migrate": (["repository", "repository.migrate"], "list"),
    "installconfig to create": (["install", "install.installconfig"], "field"),
    "skills list": (["skills", "skills.list"], "list"),
    "skills install": (["skills", "skills.install"], "list"),
    "change repository": (["change-repository"], "field"),
    "language": (["language"], "list"),
    "appearance": (["appearance"], "list"),
    "keys": (["keys"], "list"),
    "help": (["help", "help.new"], "text"),
    "preview": (["explore", "explore.explore", ":preview"], "text"),
}


def _focus_client(tmp_path):
    (tmp_path / "doc" / "adr").mkdir(parents=True)
    for n in (1, 2):
        (tmp_path / "doc" / "adr" / f"000{n}-legacy.md").write_text("# x\n", encoding="utf-8")
    log = tmp_path / "doc" / "decision-log"
    log.mkdir(parents=True)
    for n in (1, 2):
        (log / f"2026-02-0{n}--scope-note--backend--n{n}.md").write_text("# x\n", encoding="utf-8")
    decisions = [_decision(f"ADR00{n}V01-d.md", update="Accepted", updated="2026-02-01") for n in (1, 2, 3)]
    for decision in decisions:
        decision["path"] = str(tmp_path / "doc" / "adr" / decision["filename"])
        pathlib.Path(decision["path"]).write_text("# d\n", encoding="utf-8")
    for name in ("ADR004V01-p.md", "ADR005V01-p.md"):  # Proposed ones, for approve's arrows to move
        decisions.append(_decision(name))
        decisions[-1]["path"] = str(tmp_path / "doc" / "adr" / name)
    errors = [{"code": "no-header", "file": f"/r/{n}.md", "hint": "Run migrate."} for n in range(3)]
    skills = [{"skill": "adrpy", "provider": f"p{n}", "scope": "project", "installed": False, "drifted": None,
               "file": f"f{n}"} for n in range(3)]
    return FakeClient(answers={
        "config": {"success": True, "data": {"config": {**REPO_CONFIG, "migrationpattern": ""}, "warnings": []}},
        "explore": {"success": True, "data": {"decisions": decisions, "warnings": []}},
        "check": {"success": False, "code": "repository-inconsistent", "detail": "x", "warnings": [],
                  "data": {"errors": errors}},
        "installconfig": {"success": True, "data": {"configured": False, "warnings": []}},
        "skills:list": {"success": True, "data": {"skills": skills, "warnings": []}},
    })


async def _walk(app, pilot, path):
    """Goes down `path` (FOCUS_SCREENS) to its screen."""
    for step in path:
        if step == ":detail":
            app.screen.query_one("#decisions").focus()
            await pilot.press("enter")
        elif step == ":preview":
            app.screen.query_one("#decisions").focus()
            await pilot.press("f3")
        else:
            options = _options(app.screen)
            options.highlighted = options.get_option_index(step)
            await pilot.press("enter")
        await settle(pilot)


@pytest.mark.parametrize("screen_name", list(FOCUS_SCREENS))
def test_every_screen_opens_with_the_keys_where_they_act(tmp_path, user_state, screen_name):
    """Reported on explore, then found on most screens: the scrolling body
    took the focus as a screen opened (it is the first focusable widget), so
    the arrows scrolled the page instead of moving the list, and typing went
    nowhere until Tab. A list screen opens with its list taking the arrows
    (or a filter that passes them on), a form with its first field focused;
    only a screen of text to read scrolls."""
    path, offers = FOCUS_SCREENS[screen_name]
    app = AdrpyTui(tmp_path, client=_focus_client(tmp_path), user_state=user_state)

    async def scenario(pilot):
        await _walk(app, pilot, path)
        body = app.screen.query_one("#body")
        if offers == "text":
            assert app.focused is body, f"{screen_name}: {app.focused}"
            return
        assert app.focused is not None and app.focused is not body, f"{screen_name}: {app.focused}"
        if offers == "list":
            lists = [o for o in app.screen.query(OptionList) if type(o).__name__ != "SelectOverlay"]
            target = lists[0]
            before = target.highlighted
            focused_before = app.focused
            await pilot.press("down")
            await settle(pilot)
            assert target.highlighted == (before or 0) + 1, f"{screen_name}: #{target.id} {before} -> {target.highlighted} of {target.option_count}, focus {focused_before} -> {app.focused}"

    run_app(app, scenario)


async def _show_every_decision(app, pilot):
    app.screen.query_one("#field-file-options").focus()
    await pilot.press("f2")


async def _open_a_select(app, pilot):
    from textual.widgets import Select

    app.screen.query(Select).first().focus()
    await pilot.press("enter")


async def _notify(app, pilot):
    for severity in ("information", "warning", "error"):
        app.notify(f"A notice to read ({severity}).", severity=severity)


# Beyond each screen as it opens: the picker showing every decision (F2,
# the unavailable ones disabled), a Select's open list, the notifications.
CONTRAST_STATES = {
    **{name: (path, None) for name, (path, _) in FOCUS_SCREENS.items()},
    "approve showing every decision": (["decisions", "decisions.approve"], _show_every_decision),
    "a select open": (["repository", "repository.init"], _open_a_select),
    "notifications": ([], _notify),
}
# What tells a control's state apart, WCAG's 3:1 for a component: a radio
# button or checkbox (checked or not) and a select's arrow.
_INDICATORS = {"●", "X", "▼", "▲"}


def _drawn_segments(app):
    """Every run of text on the screen as the terminal gets it: (text,
    foreground, background), colors resolved."""
    import io

    from rich.console import Console
    from textual.color import Color

    console = Console(width=app.size.width, height=app.size.height, file=io.StringIO(), force_terminal=True,
                      color_system="truecolor", record=True, legacy_windows=False, safe_box=False)
    console.print(app.screen._compositor.render_update(full=True, screen_stack=app._background_screens))
    for segment in console._record_buffer:
        style = segment.style
        if segment.control or not segment.text.strip() or style is None:
            continue
        foreground, background = style.color.get_truecolor(), style.bgcolor.get_truecolor()
        if style.reverse:
            foreground, background = background, foreground
        yield segment.text.strip(), Color(*foreground), Color(*background)


def _too_low(app):
    """What falls below WCAG on the screen: text under 4.5:1, a state
    indicator or the focused widget's border under 3:1. Box and block
    characters otherwise are decoration -- a field's or a button's edges,
    a scrollbar -- that no state depends on, so they are not measured."""
    found = {}
    for text, foreground, background in _drawn_segments(app):
        graphic = all(0x2500 <= ord(c) <= 0x25FF or c == " " for c in text)
        indicator = text in _INDICATORS
        if graphic and not indicator:
            continue
        ratio = _contrast(foreground, background)
        if ratio < (3 if indicator else 4.5):
            found[f"{text[:24]} {foreground.hex} on {background.hex}"] = round(ratio, 2)
    focused = app.focused
    if focused is not None and focused.styles.border_left[0] not in ("", "none", "hidden", "blank"):
        ratio = _contrast(focused.styles.border_left[1], focused.background_colors[0])
        if ratio < 3:
            found[f"focus border of {type(focused).__name__}"] = round(ratio, 2)
    return found


@pytest.mark.parametrize("state", list(CONTRAST_STATES))
def test_every_screen_meets_wcag_contrast_in_every_preset(tmp_path, user_state, state):
    """Reported on help (a heading in the buttons' blue, 2.36:1), then
    swept on every screen: whatever Textual draws in a theme color no
    preset sets for it -- a placeholder, a disabled option, the focus
    border, an unchecked toggle, a select's arrow -- is measured as the
    terminal gets it. The presets are switched on the open screen, which
    measures the same as opening it in each (checked when this was written)."""
    path, act = CONTRAST_STATES[state]
    app = AdrpyTui(tmp_path, client=_focus_client(tmp_path), user_state=user_state)
    too_low = {}

    async def scenario(pilot):
        await _walk(app, pilot, path)
        if act:
            await act(app, pilot)
            await settle(pilot)
        for preset in ("default", "light", "high-contrast"):
            app.apply_preset(preset)
            await settle(pilot)
            too_low.update({f"{preset}: {key}": ratio for key, ratio in _too_low(app).items()})

    run_app(app, scenario)
    assert too_low == {}


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
