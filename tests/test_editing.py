"""A Proposed decision opened in the person's editor, then check
(ADR0007V01): what is started, the waiting, and what is said."""

import contextlib
import threading

import pytest
from textual.widgets import Button

from adrpy_tui.core import editors
from adrpy_tui.ui.app import AdrpyTui
from adrpy_tui.ui.check import CheckScreen
from adrpy_tui.ui.editing import EditorWaitScreen, edit_decision

from conftest import FakeClient, run_app, settle


def _with_editor(monkeypatch, user_state, name):
    monkeypatch.setattr(editors, "located", lambda editor, which=None: f"/bin/{editor.program}")
    user_state.set_editor(name)


def _decision(tmp_path):
    folder = tmp_path / "doc" / "adr"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "ADR0001V01R01-x.md"
    path.write_text("# x\n", encoding="utf-8")
    return path


async def _shown(pilot):
    """Lets the screens settle while an editor is open: its worker waits for
    it, so settle(), which waits for every worker, would wait for the editor."""
    for _ in range(10):
        await pilot.pause()


def _notes(app):
    return [str(notification.message) for notification in app._notifications]


def test_a_window_editor_is_waited_for_then_check_shows(tmp_path, user_state, monkeypatch):
    _with_editor(monkeypatch, user_state, "code")
    client = FakeClient()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)
    path = _decision(tmp_path)

    async def scenario(pilot):
        edit_decision(app, str(path))
        await _shown(pilot)
        assert isinstance(app.screen, EditorWaitScreen)
        stop = app.screen.query_one("#stop-waiting", Button)
        assert stop.variant == "warning" and app.focused is stop
        (command, _), = client.edits
        assert command == ["/bin/code", "--wait", str(path.resolve())]  # the absolute path
        client.editor_closed.set()
        await settle(pilot)
        assert isinstance(app.screen, CheckScreen)
        assert "check" in client.verbs()

    run_app(app, scenario)


def test_stopping_the_wait_says_the_editor_is_still_open(tmp_path, user_state, monkeypatch):
    _with_editor(monkeypatch, user_state, "code")
    client = FakeClient()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        edit_decision(app, str(_decision(tmp_path)))
        await _shown(pilot)
        await pilot.press("enter")  # Stop waiting
        await _shown(pilot)
        await settle(pilot)
        assert isinstance(app.screen, CheckScreen)
        assert any("still open" in note for note in _notes(app))
        assert client.still_writing()  # a write is refused until it closes
        client.editor_closed.set()

    run_app(app, scenario)


def test_esc_does_not_stop_waiting(tmp_path, user_state, monkeypatch):
    """Esc pressed by habit -- to leave the result the dialog opened over --
    left the editor open and refused every write until it closed: only Stop
    waiting, chosen, ends the wait."""
    _with_editor(monkeypatch, user_state, "code")
    client = FakeClient()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        edit_decision(app, str(_decision(tmp_path)))
        await _shown(pilot)
        await pilot.press("escape")
        await _shown(pilot)
        assert isinstance(app.screen, EditorWaitScreen) and not client.still_writing()
        client.editor_closed.set()
        await settle(pilot)
        assert isinstance(app.screen, CheckScreen)

    run_app(app, scenario)


def test_a_terminal_editor_gets_the_terminal_then_check_shows(tmp_path, user_state, monkeypatch):
    _with_editor(monkeypatch, user_state, "vim")
    client = FakeClient()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)
    suspended = []

    @contextlib.contextmanager
    def suspend():
        suspended.append(True)
        yield

    monkeypatch.setattr(app, "suspend", suspend)
    path = _decision(tmp_path)

    async def scenario(pilot):
        edit_decision(app, str(path))
        await settle(pilot)
        assert suspended and client.edits == [(["/bin/vim", str(path.resolve())], None)]
        assert isinstance(app.screen, CheckScreen)

    run_app(app, scenario)


def test_a_terminal_that_cannot_be_handed_over_is_said(tmp_path, user_state, monkeypatch):
    """The headless driver cannot suspend, as a web terminal cannot."""
    _with_editor(monkeypatch, user_state, "vim")
    client = FakeClient()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        edit_decision(app, str(_decision(tmp_path)))
        await settle(pilot)
        assert client.edits == [] and not isinstance(app.screen, CheckScreen)
        assert any("cannot be handed over" in note for note in _notes(app))

    run_app(app, scenario)


@pytest.mark.parametrize("error", [OSError("[WinError 2] not found"), ValueError("embedded null byte")])
@pytest.mark.parametrize("name", ["code", "vim"])
def test_an_editor_that_cannot_start_is_said_and_nothing_is_checked(tmp_path, user_state, monkeypatch, name, error):
    """A ValueError too (a NUL, a bad argument), as Client.run treats it:
    the TUI was left suspended, or the wait never closed."""
    _with_editor(monkeypatch, user_state, name)
    client = FakeClient(editor_error=error)
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)
    monkeypatch.setattr(app, "suspend", contextlib.nullcontext)

    async def scenario(pilot):
        edit_decision(app, str(_decision(tmp_path)))
        await settle(pilot)
        assert not isinstance(app.screen, (CheckScreen, EditorWaitScreen))
        assert any("could not be started" in note and str(error) in note for note in _notes(app))
        assert "check" not in client.verbs()

    run_app(app, scenario)


def test_an_editor_that_ends_with_an_error_is_said_and_checked(tmp_path, user_state, monkeypatch):
    """The file may have changed all the same: check says what it holds."""
    _with_editor(monkeypatch, user_state, "code")
    client = FakeClient(editor_code=1)
    client.editor_closed.set()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        edit_decision(app, str(_decision(tmp_path)))
        await settle(pilot)
        assert isinstance(app.screen, CheckScreen)
        assert any("ended with code 1" in note for note in _notes(app))

    run_app(app, scenario)


@pytest.mark.parametrize("where", ["repository root", "outside", "missing"])
def test_only_a_file_in_the_decisions_folder_is_opened(tmp_path, user_state, monkeypatch, where):
    _with_editor(monkeypatch, user_state, "code")
    client = FakeClient()
    app = AdrpyTui(tmp_path / "repo", client=client, user_state=user_state)
    (tmp_path / "repo").mkdir()
    path = {"repository root": tmp_path / "repo" / "README.md", "outside": tmp_path / "x.md",
            "missing": tmp_path / "repo" / "doc" / "adr" / "ADR0009V01R01-gone.md"}[where]
    if where != "missing":
        path.write_text("# x\n", encoding="utf-8")

    async def scenario(pilot):
        edit_decision(app, str(path))
        await settle(pilot)
        assert client.edits == [] and not isinstance(app.screen, EditorWaitScreen)
        assert _notes(app)

    run_app(app, scenario)


def test_quitting_while_an_editor_is_open_does_not_wait_for_it(tmp_path, user_state, monkeypatch):
    import time

    _with_editor(monkeypatch, user_state, "code")
    client = FakeClient()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)
    started = []

    async def scenario(pilot):
        edit_decision(app, str(_decision(tmp_path)))
        await _shown(pilot)
        started.append(time.monotonic())
        app.exit()

    run_app(app, scenario)
    assert time.monotonic() - started[0] < 3
    client.editor_closed.set()


@pytest.mark.parametrize("preset", ["default", "light", "high-contrast"])
def test_the_wait_fits_80_by_24_and_meets_wcag_contrast(tmp_path, user_state, monkeypatch, preset):
    """As every screen (tests/test_ui.py), here with the editor's worker
    still waiting, which those sweeps' settle() would wait for. What the
    dialog draws is measured; the screen behind it is dimmed on purpose."""
    from textual.widgets import Static

    from test_ui import _contrast, _cut_off

    _with_editor(monkeypatch, user_state, "code")
    user_state.set_appearance(preset)
    client = FakeClient()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)
    found = {}

    async def scenario(pilot):
        edit_decision(app, str(_decision(tmp_path)))
        await _shown(pilot)
        assert isinstance(app.screen, EditorWaitScreen)
        found["cut"] = _cut_off(app)
        note = app.screen.query_one("#editor-waiting", Static)
        stop = app.screen.query_one("#stop-waiting", Button)
        behind, face = stop.background_colors
        ratios = {"note": _contrast(note.visual_style.foreground, note.background_colors[1]),
                  "stop's text": _contrast(stop.visual_style.foreground, face)}
        found["low"] = {name: round(ratio, 2) for name, ratio in ratios.items() if ratio < 4.5}
        if _contrast(face, behind) < 3:
            found["low"]["stop's face"] = round(_contrast(face, behind), 2)
        found["stop on screen"] = 0 <= stop.region.y and stop.region.bottom <= app.size.height
        client.editor_closed.set()

    run_app(app, scenario, size=(80, 24))
    assert found == {"cut": [], "low": {}, "stop on screen": True}


def _repository_client(tmp_path, *states, created=None):
    """A configured repository whose decisions are in `states` (None:
    Proposed), on disk; `new` answers that it created `created`."""
    from test_ui import REPO_CONFIG, _decision as listed

    folder = tmp_path / "doc" / "adr"
    folder.mkdir(parents=True, exist_ok=True)
    decisions = []
    for n, update in enumerate(states, 1):
        decision = listed(f"ADR000{n}V01R01-d.md", update=update, updated="2026-02-01" if update else None)
        decision["path"] = str(folder / decision["filename"])
        (folder / decision["filename"]).write_text("# d\n", encoding="utf-8")
        decisions.append(decision)
    answers = {"config": {"success": True, "data": {"config": REPO_CONFIG, "warnings": []}},
               "explore": {"success": True, "data": {"decisions": decisions, "warnings": []}}}
    if created:
        answers["new"] = {"success": True, "data": {"created": str(created), "status": "Proposed", "warnings": []}}
    return FakeClient(answers=answers)


@pytest.mark.parametrize("command", ["new", "version", "revise", "supersede"])
def test_a_form_that_creates_a_decision_offers_the_editor_once_one_is_chosen(tmp_path, user_state, monkeypatch,
                                                                             command):
    from adrpy_tui.core.registry import FORMS
    from adrpy_tui.ui.form import FormScreen

    assert any(field.flag == "edit" and field.local for field in FORMS[command].FIELDS)
    shown = {}
    for chosen in (None, "code"):
        if chosen:
            _with_editor(monkeypatch, user_state, chosen)
        app = AdrpyTui(tmp_path, client=_repository_client(tmp_path, "Accepted"), user_state=user_state)

        async def scenario(pilot):
            app.push_screen(FormScreen(command))
            await settle(pilot)
            shown[chosen] = app.screen.query_one("#row-edit").display

        run_app(app, scenario)
    assert shown == {None: False, "code": True}


def test_new_with_the_editor_on_opens_the_decision_it_created(tmp_path, user_state, monkeypatch):
    from adrpy_tui.ui.confirm import ConfirmScreen
    from adrpy_tui.ui.form import FormScreen

    _with_editor(monkeypatch, user_state, "code")
    created = _decision(tmp_path)
    client = _repository_client(tmp_path, created=created)
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        app.push_screen(FormScreen("new"))
        await settle(pilot)
        app.screen.query_one("#field-title").value = "x"
        app.screen.query_one("#field-edit").value = True
        await pilot.press("ctrl+r")
        await settle(pilot)
        assert isinstance(app.screen, ConfirmScreen)
        assert "opens in code" in str(app.screen.query_one("#crlf-note").render())
        assert "--edit" not in str(app.screen.query_one("#command-line").render())  # the TUI's own field
        await pilot.press("enter")  # Yes
        await _shown(pilot)
        assert isinstance(app.screen, EditorWaitScreen)
        assert client.edits[0][0][-1] == str(created.resolve())
        client.editor_closed.set()
        await settle(pilot)
        assert isinstance(app.screen, CheckScreen)

    run_app(app, scenario)


def test_a_command_that_fails_opens_no_editor(tmp_path, user_state, monkeypatch):
    from adrpy_tui.ui.form import FormScreen
    from adrpy_tui.ui.result import ResultScreen

    _with_editor(monkeypatch, user_state, "code")
    client = _repository_client(tmp_path)
    client.answers["new"] = {"success": False, "code": "title-already-exists", "detail": "d"}
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        app.push_screen(FormScreen("new"))
        await settle(pilot)
        app.screen.query_one("#field-title").value = "x"
        app.screen.query_one("#field-edit").value = True
        await pilot.press("ctrl+r")
        await settle(pilot)
        await pilot.press("enter")
        await settle(pilot)
        assert isinstance(app.screen, ResultScreen) and client.edits == []

    run_app(app, scenario)


@pytest.mark.parametrize("state, chosen, offered", [
    (None, "code", True), ("Accepted", "code", False), (None, None, False),
])
def test_a_proposed_decision_s_detail_offers_edit(tmp_path, user_state, monkeypatch, state, chosen, offered):
    """An Accepted decision's text changes through revise or version."""
    from textual.widgets import OptionList

    from adrpy_tui.ui.explore import DetailScreen

    if chosen:
        _with_editor(monkeypatch, user_state, chosen)
    client = _repository_client(tmp_path, state)
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        app.push_screen(DetailScreen(client.answers["explore"]["data"]["decisions"][0]))
        await settle(pilot)
        actions = app.screen.query("#actions").results(OptionList)
        ids = [option.id for actions in actions for option in actions._options]
        assert ("edit" in ids) is offered
        if offered:
            assert ids[0] == "edit"
            options = app.screen.query_one("#actions", OptionList)
            options.focus()
            options.highlighted = 0
            await pilot.press("enter")
            await _shown(pilot)
            assert isinstance(app.screen, EditorWaitScreen)
            client.editor_closed.set()

    run_app(app, scenario)


@pytest.mark.parametrize("where", ["new form", "proposed detail"])
def test_the_editor_s_field_and_action_fit_80_by_24(tmp_path, user_state, monkeypatch, where):
    """The layout sweep (tests/test_ui.py) runs with no editor chosen: the
    field and the action it adds are drawn here."""
    from adrpy_tui.ui.explore import DetailScreen
    from adrpy_tui.ui.form import FormScreen

    from test_ui import _cut_off, _squeezed_lists

    _with_editor(monkeypatch, user_state, "code")
    client = _repository_client(tmp_path, None)
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        if where == "new form":
            app.push_screen(FormScreen("new"))
        else:
            app.push_screen(DetailScreen(client.answers["explore"]["data"]["decisions"][0]))
        await settle(pilot)
        assert app.screen.query("#row-edit" if where == "new form" else "#actions")
        assert _cut_off(app) == [] and _squeezed_lists(app) == []

    run_app(app, scenario, size=(80, 24))


@pytest.mark.parametrize("saved, warned", [("utf-8", False), ("cp1252", True)])
def test_a_file_the_editor_saved_in_another_encoding_is_said(tmp_path, user_state, monkeypatch, saved, warned):
    """adrpy check passes a cp1252 file, and approve then replaces each
    non-UTF-8 byte with U+FFFD, the text lost (measured with adrpy-ai
    0.1): said once the editor is closed, before anything is approved."""
    _with_editor(monkeypatch, user_state, "code")
    client = FakeClient()
    client.editor_closed.set()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)
    path = _decision(tmp_path)
    path.write_bytes("# Decisão: ação\n".encode(saved))

    async def scenario(pilot):
        edit_decision(app, str(path))
        await settle(pilot)
        assert isinstance(app.screen, CheckScreen)
        assert any("not saved as UTF-8" in note for note in _notes(app)) is warned

    run_app(app, scenario)


def test_a_terminal_editor_that_cannot_start_gives_the_terminal_back(tmp_path, user_state, monkeypatch):
    """Textual's suspend() resumes only after a body that returned: an
    exception left the TUI suspended, drawing nothing, taking no key."""
    _with_editor(monkeypatch, user_state, "vim")
    client = FakeClient(editor_error=OSError("[WinError 2] not found"))
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)
    calls = []

    async def scenario(pilot):
        monkeypatch.setattr(type(app._driver), "can_suspend", property(lambda driver: True))
        monkeypatch.setattr(app._driver, "suspend_application_mode", lambda: calls.append("suspend"))
        monkeypatch.setattr(app._driver, "resume_application_mode", lambda: calls.append("resume"))
        edit_decision(app, str(_decision(tmp_path)))
        await settle(pilot)
        assert calls == ["suspend", "resume"]
        assert any("could not be started" in note for note in _notes(app))

    run_app(app, scenario)


@pytest.mark.parametrize("left", ["write", "editor"])
def test_no_editor_opens_while_a_left_write_or_editor_still_runs(tmp_path, user_state, monkeypatch, left):
    """The file a left approve rewrites, or the one a left editor still has
    open: an editor saving it would undo the other."""
    from conftest import _OpenEditor

    _with_editor(monkeypatch, user_state, "code")
    client = FakeClient()
    still = threading.Event()
    client._left.append(_OpenEditor(still))
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        edit_decision(app, str(_decision(tmp_path)))
        await _shown(pilot)
        assert client.edits == [] and not isinstance(app.screen, EditorWaitScreen)
        assert any("still running" in note for note in _notes(app))
        still.set()
        edit_decision(app, str(_decision(tmp_path)))  # once it ended
        await _shown(pilot)
        assert isinstance(app.screen, EditorWaitScreen)
        client.editor_closed.set()

    run_app(app, scenario)


def test_the_editor_closing_under_another_dialog_closes_the_wait_not_the_dialog(tmp_path, user_state, monkeypatch):
    from adrpy_tui.ui.confirm import ConfirmScreen

    _with_editor(monkeypatch, user_state, "code")
    client = FakeClient()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        edit_decision(app, str(_decision(tmp_path)))
        await _shown(pilot)
        app.push_screen(ConfirmScreen("adrpy x"))
        await _shown(pilot)
        client.editor_closed.set()
        await settle(pilot)
        names = [type(screen).__name__ for screen in app.screen_stack]
        assert "EditorWaitScreen" not in names and names[-1] == "CheckScreen"

    run_app(app, scenario)


def test_a_window_editor_is_started_with_nothing_of_the_terminal(tmp_path, monkeypatch):
    """The real-process test passes whenever the runner's own stdin is
    empty (CI, xdist): the three streams are asserted here."""
    import subprocess

    from adrpy_tui.core.client import Client

    seen = {}

    class Started:
        def __init__(self, command, **options):
            seen.update(options)

        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr(subprocess, "Popen", Started)
    assert Client().edit(["editor", "x.md"], None) == 0
    assert (seen["stdin"], seen["stdout"], seen["stderr"]) == (subprocess.DEVNULL,) * 3


def test_a_decisions_folder_reached_through_a_link_is_not_opened(tmp_path, user_state, monkeypatch):
    """Like the preview (ADR0006V02): a folder link may lead anywhere."""
    import os
    import subprocess

    _with_editor(monkeypatch, user_state, "code")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "ADR0001V01R01-x.md").write_text("# x\n", encoding="utf-8")
    repo = tmp_path / "repo"
    (repo / "doc").mkdir(parents=True)
    link = repo / "doc" / "adr"
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(elsewhere)], check=True, capture_output=True)
    else:
        os.symlink(elsewhere, link, target_is_directory=True)
    client = FakeClient()
    app = AdrpyTui(repo, client=client, user_state=user_state)

    async def scenario(pilot):
        edit_decision(app, str(link / "ADR0001V01R01-x.md"))
        await _shown(pilot)
        assert client.edits == [] and _notes(app)

    run_app(app, scenario)


def test_a_failure_that_names_a_file_opens_no_editor(tmp_path, user_state, monkeypatch):
    """Only a success opens the editor, whatever a failure's data names."""
    from adrpy_tui.ui.form import FormScreen
    from adrpy_tui.ui.result import ResultScreen

    _with_editor(monkeypatch, user_state, "code")
    client = _repository_client(tmp_path)
    client.answers["new"] = {"success": False, "code": "x", "detail": "d",
                             "data": {"created": str(_decision(tmp_path))}}
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        app.push_screen(FormScreen("new"))
        await settle(pilot)
        app.screen.query_one("#field-title").value = "x"
        app.screen.query_one("#field-edit").value = True
        await pilot.press("ctrl+r")
        await settle(pilot)
        await pilot.press("enter")
        await _shown(pilot)
        assert isinstance(app.screen, ResultScreen) and client.edits == []

    run_app(app, scenario)


def test_a_run_asked_again_with_the_editor_off_opens_none(tmp_path, user_state, monkeypatch):
    """Asked with the editor on, refused, asked again with it off."""
    from adrpy_tui.ui.form import FormScreen
    from adrpy_tui.ui.result import ResultScreen

    _with_editor(monkeypatch, user_state, "code")
    client = _repository_client(tmp_path, created=_decision(tmp_path))
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        app.push_screen(FormScreen("new"))
        await settle(pilot)
        app.screen.query_one("#field-title").value = "x"
        app.screen.query_one("#field-edit").value = True
        await pilot.press("ctrl+r")
        await settle(pilot)
        await pilot.press("escape")  # No
        await settle(pilot)
        app.screen.query_one("#field-edit").value = False
        await pilot.press("ctrl+r")
        await settle(pilot)
        await pilot.press("enter")
        await _shown(pilot)
        assert isinstance(app.screen, ResultScreen) and client.edits == []

    run_app(app, scenario)


@pytest.mark.parametrize("code, warned", [(1, True), (None, False)])
def test_the_encoding_is_said_once_closed_whatever_its_code_not_while_left_open(tmp_path, user_state, monkeypatch,
                                                                                code, warned):
    _with_editor(monkeypatch, user_state, "code")
    client = FakeClient(editor_code=code or 0)
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)
    path = _decision(tmp_path)
    path.write_bytes("# Decisão\n".encode("cp1252"))

    async def scenario(pilot):
        edit_decision(app, str(path))
        await _shown(pilot)
        if code is None:
            app.screen.query_one("#stop-waiting").press()  # left open: what it holds now is not the end of it
        else:
            client.editor_closed.set()
        await _shown(pilot)
        await settle(pilot)
        assert isinstance(app.screen, CheckScreen)
        assert any("not saved as UTF-8" in note for note in _notes(app)) is warned
        client.editor_closed.set()

    run_app(app, scenario)



@pytest.mark.parametrize("where, says", [("outside", "outside"), ("missing", "missing")])
def test_a_refused_edit_says_why(tmp_path, user_state, monkeypatch, where, says):
    """The notice was only checked to exist: any text passed."""
    _with_editor(monkeypatch, user_state, "code")
    app = AdrpyTui(tmp_path / "repo", client=FakeClient(), user_state=user_state)
    (tmp_path / "repo" / "doc" / "adr").mkdir(parents=True)
    path = tmp_path / "x.md" if where == "outside" else tmp_path / "repo" / "doc" / "adr" / "ADR0009V01R01-gone.md"
    if where == "outside":
        path.write_text("# x\n", encoding="utf-8")
    expected = (app.texts("preview.outside", path=str(path)) if where == "outside"
                else app.texts("preview.missing", path=str(path)))

    async def scenario(pilot):
        edit_decision(app, str(path))
        await _shown(pilot)
        assert _notes(app) == [expected]

    run_app(app, scenario)


def test_an_editor_closed_cleanly_says_no_code(tmp_path, user_state, monkeypatch):
    _with_editor(monkeypatch, user_state, "code")
    client = FakeClient()
    client.editor_closed.set()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        edit_decision(app, str(_decision(tmp_path)))
        await _shown(pilot)
        await settle(pilot)
        assert isinstance(app.screen, CheckScreen) and not any("ended with code" in note for note in _notes(app))

    run_app(app, scenario)


def test_an_editor_gone_from_path_since_it_was_chosen_is_said(tmp_path, user_state, monkeypatch):
    """Chosen while on PATH, gone by the time the decision is opened."""
    looks = []  # once Edit is chosen: still there as it is chosen, gone as it starts
    monkeypatch.setattr(editors, "located", lambda editor, which=None: looks.pop(0) if looks else "/bin/code")
    user_state.set_editor("code")
    client = FakeClient()
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        looks.extend(["/bin/code", None])
        edit_decision(app, str(_decision(tmp_path)))
        await _shown(pilot)
        assert client.edits == [] and any("no longer on this system's PATH" in note for note in _notes(app))

    run_app(app, scenario)


def test_a_detail_whose_read_failed_offers_no_edit(tmp_path, user_state, monkeypatch):
    """What it shows may no longer be so: no action on it, Edit neither."""
    from adrpy_tui.ui.explore import DetailScreen

    _with_editor(monkeypatch, user_state, "code")
    client = _repository_client(tmp_path, None)
    decision = client.answers["explore"]["data"]["decisions"][0]
    client.answers["explore"] = {"success": False, "code": "tui-timeout", "detail": "d"}
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        app.push_screen(DetailScreen(decision))
        await settle(pilot)
        assert not app.screen.query("#actions")

    run_app(app, scenario)


def test_a_failed_command_s_result_says_no_next_step(tmp_path, user_state):
    from adrpy_tui.core.client import Result
    from adrpy_tui.ui.result import ResultScreen

    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        app.push_screen(ResultScreen("new", Result((), 1, False, code="x", detail="d",
                                                   data={"created": str(tmp_path / "x.md")})))
        await settle(pilot)
        assert not app.screen.query("#next-step")

    run_app(app, scenario)
