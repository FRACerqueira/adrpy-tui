"""What each screen says of its keys, and where they lead: a key the key line
names acts in the state the screen is in, a key that acts is named, and a
screen reached after an action says what it is about and what comes next."""

import pytest
from textual.containers import VerticalScroll
from textual.widgets import Button, Input, OptionList, RadioSet, Select, Static, Switch, TextArea

from adrpy_tui.core.client import ABANDONED, Result
from adrpy_tui.ui.app import AdrpyTui
from adrpy_tui.ui.check import CheckScreen
from adrpy_tui.ui.config import FieldEditScreen
from adrpy_tui.ui.confirm import ConfirmScreen
from adrpy_tui.ui.errors import ErrorList
from adrpy_tui.ui.explore import DetailScreen
from adrpy_tui.ui.form import FormScreen
from adrpy_tui.ui.result import ResultScreen
from adrpy_tui.ui.toggles import CheckList

from conftest import FakeClient, run_app, settle
from test_editing import _decision, _repository_client, _shown, _with_editor
from test_ui import FOCUS_SCREENS, _dialogs, _layout_client, _walk


def _line(app):
    """The key line of what is in front: the screen's, or the dialog's own."""
    lines = app.screen.query("#hints, #dialog-keys").results(Static)
    return " · ".join(str(line.render()) for line in lines)


def _announced(app):
    """The keys the line in front names. The line drawn must be the one the
    screen computes now: one left as it was drawn before the screen changed
    would name keys for what it no longer shows."""
    from adrpy_tui.ui.base import key_line

    screen = app.screen
    hints = screen.hints() if hasattr(screen, "hints") else ()
    if hints:
        assert _line(app) == key_line(app, hints), "the line drawn is not the screen's own now"
    return {key for key, _ in hints}


def _somewhere_to_act(app, key):
    """Whether `key`, named on the key line, can act in this state."""
    screen, focused = app.screen, app.focused
    lists = [options for options in screen.query(OptionList)
             if options.display and type(options).__name__ != "SelectOverlay"
             and any(not options.get_option_at_index(i).disabled for i in range(options.option_count))]
    if key == "arrows":
        scrolls = [box for box in screen.query("#command-scroll") if box.max_scroll_y > 0]
        return bool(lists) or bool(scrolls) or isinstance(focused, (VerticalScroll, TextArea, RadioSet))
    if key == "space":
        return isinstance(focused, (CheckList, RadioSet, Switch))
    if key == "enter":
        return bool(lists) or isinstance(focused, (Button, Input, RadioSet, Switch, Select))
    if key == "right":
        return any(field.suggest_from for field in getattr(getattr(screen, "form", None), "FIELDS", ()))
    if key == "@preview":
        if isinstance(screen, CheckScreen):
            return bool(screen.query(ErrorList))
        if isinstance(screen, ResultScreen):
            return bool(screen.query(ErrorList)) or isinstance(
                screen.result.data.get("created") or screen.result.data.get("file"), str)
        return bool(lists) or isinstance(screen, DetailScreen)
    return True  # Tab, Esc, Ctrl+R, F2: their screen's own bindings


EXTRA = {
    "result: created": lambda app: ResultScreen("new", Result((), 0, True, data={
        "created": str(app.repo / "doc" / "adr" / "ADR001V01-d.md"), "status": "Proposed"})),
    "result: approved": lambda app: ResultScreen("approve", Result((), 0, True, data={})),
    "result: errors": lambda app: ResultScreen("approve", Result((), 1, False, code="repository-inconsistent",
                                                                 detail="d", data={"errors": [
                                                                     {"code": "no-header", "file": "/r/x.md"}]})),
    "result: write left": lambda app: ResultScreen("approve", Result((), -1, False, code=ABANDONED, detail="d")),
    "check: consistent": lambda app: CheckScreen(),
}
STATES = [*FOCUS_SCREENS, *_dialogs(), *EXTRA, "explore: nothing", "log: nothing", "migrate: nothing to migrate",
          "approve: nothing to approve", "confirmation: Enter on No"]


def _empty_repository(tmp_path):
    from test_ui import REPO_CONFIG

    (tmp_path / "doc" / "adr").mkdir(parents=True)
    (tmp_path / "doc" / "decision-log").mkdir(parents=True)
    return FakeClient(answers={
        "config": {"success": True, "data": {"config": {**REPO_CONFIG, "migrationpattern": ""}, "warnings": []}},
        "explore": {"success": True, "data": {"decisions": [], "warnings": []}},
    })


EMPTY = {"explore: nothing": ["explore", "explore.explore"], "log: nothing": ["log", "log.browse"],
         "migrate: nothing to migrate": ["repository", "repository.migrate"],
         "approve: nothing to approve": ["decisions", "decisions.approve"]}


@pytest.mark.parametrize("state", STATES)
def test_every_key_the_line_names_acts_there(tmp_path, user_state, state):
    """Reported after editing: check with nothing wrong named the arrows,
    Enter and F3, which did nothing -- only Esc did."""
    client = _empty_repository(tmp_path) if state in EMPTY else _layout_client(tmp_path)
    if state == "check: consistent":
        client.answers["check"] = {"success": True, "data": {"decisions": 3, "warnings": []}}
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        if state in FOCUS_SCREENS:
            await _walk(app, pilot, FOCUS_SCREENS[state][0])
        elif state in EMPTY:
            await _walk(app, pilot, EMPTY[state])
        elif state in EXTRA:
            app.push_screen(EXTRA[state](app))
        elif state == "confirmation: Enter on No":
            app.push_screen(ConfirmScreen("adrpy new --path C:/r --title x"))
            await settle(pilot)
            app.screen.query_one("#no").focus()
        else:
            app.push_screen(_dialogs()[state]())
        await settle(pilot)
        # The key capture's own instruction names its keys (keys.press).
        assert _line(app) or type(app.screen).__name__ == "KeyCaptureScreen", "no key line"
        idle = [key for key in _announced(app) if not _somewhere_to_act(app, key)]
        assert idle == [], _line(app)

    run_app(app, scenario, size=(80, 24))


@pytest.mark.parametrize("state, says, never", [
    ("check: consistent", ["Esc back"], ["↑↓", "Enter", "F3"]),
    ("result: write left", ["Enter run check", "Esc back"], ["F3"]),
    ("result: errors", ["↑↓ move", "F3 preview"], []),
    ("result: approved", ["Esc back"], ["F3"]),
])
def test_the_line_says_what_acts_on_a_result(tmp_path, user_state, state, says, never):
    client = FakeClient(answers={"check": {"success": True, "data": {"decisions": 3, "warnings": []}}})
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        app.push_screen(EXTRA[state](app))
        await settle(pilot)
        line = _line(app)
        assert all(text in line for text in says) and not any(text in line for text in never), line

    run_app(app, scenario)


def test_check_with_errors_names_no_enter(tmp_path, user_state):
    """Enter does nothing on the list of errors: its highlight shows each."""
    app = AdrpyTui(tmp_path, client=_layout_client(tmp_path), user_state=user_state)

    async def scenario(pilot):
        await _walk(app, pilot, FOCUS_SCREENS["check with errors"][0])
        line = _line(app)
        assert "↑↓ move" in line and "F3 preview" in line and "Enter" not in line, line

    run_app(app, scenario)


@pytest.mark.parametrize("command, suggests", [("new", True), ("init", False), ("skills:install", False)])
def test_a_form_names_suggestions_only_where_it_has_them(tmp_path, user_state, command, suggests):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        app.push_screen(FormScreen(command))
        await settle(pilot)
        assert ("accept suggestion" in _line(app)) is suggests, _line(app)

    run_app(app, scenario)


def test_a_choice_names_space_while_it_has_the_focus(tmp_path, user_state):
    """The first question asked of the skills form: how is a provider marked."""
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        app.push_screen(FormScreen("skills:install"))
        await settle(pilot)
        app.screen.query_one("#field-provider").focus()
        await pilot.pause()
        assert "Space mark" in _line(app), _line(app)
        app.screen.query_one("#field-force").focus()
        await pilot.pause()
        assert "Space mark" in _line(app), _line(app)
        app.screen.query_one("#run").focus()
        await pilot.pause()
        assert "Space" not in _line(app), _line(app)

    run_app(app, scenario)


def test_creating_the_install_level_config_names_its_button_not_save(tmp_path, user_state):
    """Ctrl+R saves an existing config: with none yet it said nothing changed."""
    app = AdrpyTui(tmp_path, client=_layout_client(tmp_path), user_state=user_state)

    async def scenario(pilot):
        await _walk(app, pilot, FOCUS_SCREENS["installconfig to create"][0])
        line = _line(app)
        assert "save" not in line and "Ctrl+R" not in line and "Enter" in line, line

    run_app(app, scenario)


@pytest.mark.parametrize("dialog, says", [
    (lambda: ConfirmScreen("adrpy new --path C:/r --title x"), ["Enter", "Esc no"]),
    (lambda: ConfirmScreen("adrpy log --path C:/r --body " + chr(10).join(f"line {n}" for n in range(60))),
     ["↑↓ scroll", "Esc no"]),
    (lambda: FieldEditScreen(next(field for field in __import__("adrpy_tui.core.config_fields", fromlist=["x"])
                                  .CONFIG_FIELDS if field.flag == "headerscope"), "Scope", "d"),
     ["Enter OK", "Esc cancel"]),
])
def test_a_dialog_names_its_keys(tmp_path, user_state, dialog, says):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        app.push_screen(dialog())
        await settle(pilot)
        line = str(app.screen.query_one("#dialog-keys", Static).render())
        assert all(text in line for text in says), line

    run_app(app, scenario, size=(80, 24))


@pytest.mark.parametrize("name", ["help", "preview"])
def test_a_screen_to_read_names_the_arrows_that_scroll_it(tmp_path, user_state, name):
    app = AdrpyTui(tmp_path, client=_layout_client(tmp_path), user_state=user_state)

    async def scenario(pilot):
        await _walk(app, pilot, FOCUS_SCREENS[name][0])
        assert "↑↓ scroll" in _line(app), _line(app)

    run_app(app, scenario)


def test_a_created_decision_s_result_says_what_comes_next(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        app.push_screen(EXTRA["result: created"](app))
        await settle(pilot)
        assert app.screen.query("#next-step")
        assert "Explore" in str(app.screen.query_one("#next-step", Static).render())

    run_app(app, scenario)


@pytest.mark.parametrize("flow", ["new", "detail"])
def test_check_after_editing_names_the_file_and_esc_goes_to_its_detail(tmp_path, user_state, monkeypatch, flow):
    """Reported: a bare "No inconsistencies", the arrows and F3 named for
    nothing, and Esc back to new's result, then the menu."""
    _with_editor(monkeypatch, user_state, "code")
    created = _decision(tmp_path)
    client = _repository_client(tmp_path, None, created=created)
    decision = client.answers["explore"]["data"]["decisions"][0]
    if flow == "new":
        decision["path"] = str(created)
        decision["filename"] = created.name
    client.answers["check"] = {"success": True, "data": {"decisions": 1, "warnings": []}}
    client.editor_closed.set()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        if flow == "new":
            await _walk(app, pilot, ["decisions", "decisions.new"])
            app.screen.query_one("#field-title").value = "x"
            app.screen.query_one("#field-edit").value = True
            await pilot.press("ctrl+r")
            await settle(pilot)
            await pilot.press("enter")
        else:
            app.push_screen(DetailScreen(decision))
            await settle(pilot)
            options = app.screen.query_one("#actions", OptionList)
            options.focus()
            options.highlighted = 0
            await pilot.press("enter")
        await _shown(pilot)
        await settle(pilot)
        assert isinstance(app.screen, CheckScreen)
        body = " ".join(str(static.render()) for static in app.screen.query("#body Static").results(Static))
        assert decision["filename"] in body and "goes to its detail" in body, body
        assert _line(app) == "Esc back to the decision", _line(app)
        await pilot.press("escape")
        await settle(pilot)
        assert isinstance(app.screen, DetailScreen) and app.screen.decision["path"] == decision["path"]
        assert not any(isinstance(screen, (ResultScreen, CheckScreen)) for screen in app.screen_stack)

    run_app(app, scenario)



def test_a_decision_gone_by_the_time_its_detail_comes_back_names_only_esc(tmp_path, user_state):
    """Its detail is read again as it comes back to the top: the line
    named the actions it no longer offers."""
    client = _repository_client(tmp_path, None)
    decision = client.answers["explore"]["data"]["decisions"][0]
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        app.push_screen(DetailScreen(decision))
        await settle(pilot)
        assert "Enter" in _line(app)
        client.answers["explore"] = {"success": True, "data": {"decisions": [], "warnings": []}}
        app.push_screen(ResultScreen("approve", Result((), 0, True, data={})))
        await settle(pilot)
        await pilot.press("escape")
        await settle(pilot)
        assert isinstance(app.screen, DetailScreen) and _line(app) == "Esc back", _line(app)

    run_app(app, scenario)


def test_back_from_check_after_an_edit_leaves_one_detail_of_the_decision(tmp_path, user_state, monkeypatch):
    """The detail below is the decision's, however explore spells its path."""
    _with_editor(monkeypatch, user_state, "code")
    client = _repository_client(tmp_path, None)
    decision = client.answers["explore"]["data"]["decisions"][0]
    decision["path"] = decision["path"].upper() if __import__("os").name == "nt" else decision["path"]
    client.answers["check"] = {"success": True, "data": {"decisions": 1, "warnings": []}}
    client.editor_closed.set()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        app.push_screen(DetailScreen(decision))
        await settle(pilot)
        options = app.screen.query_one("#actions", OptionList)
        options.focus()
        options.highlighted = 0
        await pilot.press("enter")
        await _shown(pilot)
        await settle(pilot)
        await pilot.press("escape")
        await settle(pilot)
        details = [screen for screen in app.screen_stack if isinstance(screen, DetailScreen)]
        assert len(details) == 1 and details[0] is app.screen
        assert app.screen.query("#actions")  # the decision found again, not "gone"

    run_app(app, scenario)


def test_check_after_an_edit_with_errors_says_how_to_repair(tmp_path, user_state, monkeypatch):
    from adrpy_tui.ui.editing import edit_decision

    _with_editor(monkeypatch, user_state, "code")
    client = FakeClient(answers={"check": {"success": False, "code": "repository-inconsistent", "detail": "d",
                                           "data": {"errors": [{"code": "invalid-header", "file": "/r/x.md"}]}}})
    client.editor_closed.set()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        edit_decision(app, str(_decision(tmp_path)))
        await _shown(pilot)
        await settle(pilot)
        assert "Edit opens it again" in str(app.screen.query_one("#next-step", Static).render())
        assert _line(app) == "↑↓ move · F3 preview · Esc back to the decision", _line(app)

    run_app(app, scenario)


def test_only_a_created_decision_s_result_says_what_comes_next(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        # log names the entry it created: no decision to read or approve.
        app.push_screen(ResultScreen("log", Result((), 0, True, data={"created": "C:/r/doc/decision-log/x.md"})))
        await settle(pilot)
        assert not app.screen.query("#next-step")

    run_app(app, scenario)


def test_the_next_step_names_the_preview_key_given_and_edit_only_with_an_editor(tmp_path, user_state, monkeypatch):
    user_state.set_key("preview", "f7")
    shown = {}
    for chosen in (None, "code"):
        if chosen:
            _with_editor(monkeypatch, user_state, chosen)
        app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

        async def scenario(pilot):
            app.push_screen(EXTRA["result: created"](app))
            await settle(pilot)
            shown[chosen] = str(app.screen.query_one("#next-step", Static).render())

        run_app(app, scenario)
    assert all("F7" in text and "F3" not in text for text in shown.values()), shown
    assert "edit" not in shown[None] and "edit" in shown["code"], shown


def test_a_choice_names_the_arrows_that_move_in_it(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        app.push_screen(FormScreen("skills:install"))
        await settle(pilot)
        for widget in ("#field-provider", "#field-target"):
            app.screen.query_one(widget).focus()
            await pilot.pause()
            assert "↑↓ move" in _line(app), (widget, _line(app))

    run_app(app, scenario)
