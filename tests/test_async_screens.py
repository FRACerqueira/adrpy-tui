"""What arrives while the person keeps using the TUI -- a read's answer, a
command's result -- lands on the screen that asked, only while that screen
is still there and only if it is the latest; a failure becomes something on
the screen, never the end of the app; a write that does not answer can be
left (ADR006V01). One person, one TUI (the product's own assumption)."""

import threading

from textual.widgets import Button, Markdown, Switch

from adrpy_tui.core import client as client_module
from adrpy_tui.core.client import ABANDONED
from adrpy_tui.ui.app import AdrpyTui
from adrpy_tui.ui.check import CheckScreen
from adrpy_tui.ui.explore import DetailScreen
from adrpy_tui.ui.form import FormScreen
from adrpy_tui.ui.menu import MenuScreen
from adrpy_tui.ui.preview import PreviewScreen
from adrpy_tui.ui.repository import RepositoryScreen
from adrpy_tui.ui.result import ResultScreen

from conftest import FakeClient, command_of, run_app, settle
from test_ui import _focus_client, _walk


class Holding(FakeClient):
    """Holds `command` (after its first `skip` calls) until `release` is
    set, as a slow adrpy would; a write held here ends as the real runner
    does when the person leaves it."""

    def __init__(self, command, answers, skip=0):
        super().__init__(answers=answers)
        self.command, self.skip = command, skip
        self.release, self.held = threading.Event(), threading.Event()

    def _answer(self, argv, timeout=None, leave=None, **options):
        if command_of(argv) == self.command:
            if self.skip:
                self.skip -= 1
            else:
                self.held.set()
                while not self.release.wait(0.02):
                    if leave is not None and leave.is_set():
                        raise client_module._Left()
        return super()._answer(argv)


def _holding(tmp_path, command, skip=0):
    return Holding(command, _focus_client(tmp_path).answers, skip=skip)


async def _approve_and_run(app, pilot):
    await _walk(app, pilot, ["decisions", "decisions.approve"])
    app.screen.query_one("#field-file-options").focus()
    await pilot.press("enter")
    await pilot.press("ctrl+r")
    await settle(pilot)
    await pilot.press("enter")  # Yes
    await pilot.pause()


async def _held(pilot, client):
    """Waits, without blocking the app, until `client` holds its call."""
    for _ in range(250):
        if client.held.is_set():
            return True
        await pilot.pause(0.02)
    return False


def _stack(app):
    return [type(screen).__name__ for screen in app.screen_stack]


def test_the_result_replaces_the_screen_that_ran_the_command(tmp_path, user_state):
    """A screen pushed over the form while its command ran (a preview, the
    command palette) was the one the result replaced; the form came back
    still "running", and neither Esc nor any key left it."""
    client = _holding(tmp_path, "approve")
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)
    page = tmp_path / "x.md"
    page.write_text("# x\n", encoding="utf-8")

    async def scenario(pilot):
        await _approve_and_run(app, pilot)
        assert await _held(pilot, client)
        app.push_screen(PreviewScreen(page))
        await pilot.pause()
        client.release.set()
        await settle(pilot)
        assert _stack(app)[-2:] == ["MenuScreen", "ResultScreen"]
        await pilot.press("escape")
        await settle(pilot)
        assert isinstance(app.screen, MenuScreen)

    run_app(app, scenario)


def test_the_command_palette_is_off(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        await pilot.press("ctrl+p")
        await settle(pilot)
        assert isinstance(app.screen, MenuScreen)

    run_app(app, scenario)


def test_the_preview_and_show_all_keys_do_nothing_while_a_command_runs(tmp_path, user_state):
    client = _holding(tmp_path, "approve")
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _approve_and_run(app, pilot)
        assert await _held(pilot, client)
        await pilot.press("f3", "f2")
        await pilot.pause()
        assert isinstance(app.screen, FormScreen)
        client.release.set()
        await settle(pilot)

    run_app(app, scenario)


def test_a_write_past_its_time_can_be_left_and_check_is_offered(tmp_path, user_state, monkeypatch):
    """ADR006V01: a write is never stopped; past the time a read may take,
    the screen says adrpy still runs, lets the person leave, and the
    result it then shows is "unknown", with Check at hand."""
    monkeypatch.setattr(client_module, "READ_TIMEOUT", 0.3)
    client = _holding(tmp_path, "approve")
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _approve_and_run(app, pilot)
        assert await _held(pilot, client)
        await pilot.pause(0.8)
        assert "still running" in str(app.screen.query_one("#still-running-note").render())
        app.screen.query_one("#leave-running", Button).press()
        await settle(pilot)
        assert isinstance(app.screen, ResultScreen) and app.screen.result.code == ABANDONED
        app.screen.query_one("#run-check", Button).press()
        await settle(pilot)
        assert isinstance(app.screen, CheckScreen)
        client.release.set()

    run_app(app, scenario)


def test_an_answer_of_the_wrong_shape_is_shown_as_a_failure_not_fatal(tmp_path, user_state):
    """A decision without "filename" ended the app (KeyError in a result
    handler); the traceback goes to a file the person can find."""
    client = _focus_client(tmp_path)
    client.answers["explore"] = {"success": True, "data": {"decisions": [{"x": 1}], "warnings": []}}
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _walk(app, pilot, ["explore", "explore.explore"])
        note = str(app.screen.query_one("#internal-error").render())
        assert "KeyError" in note
        assert user_state.error_log.exists()

    run_app(app, scenario)


def test_a_failure_inside_a_read_is_shown_not_fatal(tmp_path, user_state):
    class Failing(FakeClient):
        def _answer(self, argv, **options):
            if command_of(argv) == "check":
                raise RuntimeError("the runner broke")
            return super()._answer(argv, **options)

    app = AdrpyTui(tmp_path, client=Failing(answers=_focus_client(tmp_path).answers), user_state=user_state)

    async def scenario(pilot):
        await _walk(app, pilot, ["explore", "explore.check"])
        assert "the runner broke" in str(app.screen.query_one("#internal-error").render())

    run_app(app, scenario)


def test_two_restarts_in_a_row_leave_one_main_menu(tmp_path, user_state):
    """Two Enter on "Change repository" before the first restart ran: the
    first start-up screen's read landed after it was gone (NoActiveAppError)."""
    client = _holding(tmp_path, "config", skip=1)  # the first start-up read answers at once
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        app.push_screen(RepositoryScreen())
        await settle(pilot)
        app.screen.query_one("#repository-path").value = str(tmp_path)
        app.screen.action_use()
        app.screen.action_use()
        await pilot.pause(0.3)
        client.release.set()
        await settle(pilot)
        assert _stack(app) == ["Screen", "MenuScreen"]

    run_app(app, scenario)


def test_leaving_a_screen_while_it_is_being_filled_is_harmless(tmp_path, user_state):
    """Esc as a read's answer landed: the rest of the handler ran on the
    leaving screen (NoMatches) and ended the app -- config every time."""
    for path, command in ((["repository", "repository.config"], "config"),
                          (["skills", "skills.list"], "skills:list"),
                          (["repository", "repository.migrate"], "explore")):
        for attempt in range(3):
            repo = tmp_path / f"{command.replace(':', '-')}-{attempt}"
            repo.mkdir()
            client = _holding(repo, command, skip=1 if command == "config" else 0)
            app = AdrpyTui(repo, client=client, user_state=user_state)

            async def scenario(pilot):
                await _walk(app, pilot, path[:1])
                options = app.screen.query_one("#options")
                options.highlighted = options.get_option_index(path[1])
                await pilot.press("enter")
                assert await _held(pilot, client)
                client.release.set()
                await pilot.press("escape")
                await settle(pilot)
                assert isinstance(app.screen, MenuScreen)

            run_app(app, scenario)


def test_a_migrate_preview_for_an_old_pattern_is_dropped(tmp_path, user_state):
    client = _holding(tmp_path, "explore", skip=1)  # the screen's own read answers at once
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _walk(app, pilot, ["repository", "repository.migrate"])
        app.screen.query_one("#preview", Button).press()
        assert await _held(pilot, client)
        switch = app.screen.query(Switch).first()
        switch.value = not switch.value  # the pattern changes while the preview runs
        await pilot.pause()
        client.release.set()
        await settle(pilot)
        assert not app.screen.query_one("#preview-area").children

    run_app(app, scenario)


def test_a_detail_that_cannot_be_read_again_says_so(tmp_path, user_state):
    client = _focus_client(tmp_path)
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _walk(app, pilot, ["explore", "explore.explore", ":detail"])
        assert isinstance(app.screen, DetailScreen) and app.screen.query("#actions")
        client.answers["explore"] = {"success": False, "code": "target-directory-not-found",
                                     "detail": "Directory does not exist", "warnings": []}
        app.screen.on_screen_resume()
        await settle(pilot)
        assert "Directory does not exist" in str(app.screen.query_one("#read-failed").render())
        assert not app.screen.query("#actions")

    run_app(app, scenario)


def test_two_reads_in_flight_show_the_screen_once(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=_focus_client(tmp_path), user_state=user_state)

    async def scenario(pilot):
        await _walk(app, pilot, ["explore", "explore.explore", ":detail"])
        app.screen.on_screen_resume()
        app.screen.on_screen_resume()
        await settle(pilot)
        assert len(app.screen.query(Markdown)) == 1
        assert len(app.screen.query("#actions")) == 1

    run_app(app, scenario)
