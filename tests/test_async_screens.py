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
    does when the person leaves it. Never longer than 10 s, like the other
    fakes: a regression then fails, instead of hanging the suite."""

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
                for _ in range(500):
                    if self.release.wait(0.02):
                        break
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
        switch = app.screen.query_one(Switch)
        before = switch.value
        await pilot.press("f3", "f2")
        await pilot.pause()
        assert isinstance(app.screen, FormScreen)
        assert switch.value == before  # show-all did not flip
        assert list(app._notifications) == []  # nor did the preview try to open anything
        client.release.set()
        await settle(pilot)

    run_app(app, scenario)


def test_the_preview_key_does_nothing_while_migrate_runs(tmp_path, user_state):
    client = _holding(tmp_path, "migrate")
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _walk(app, pilot, ["repository", "repository.migrate"])
        await pilot.press("ctrl+r")
        await settle(pilot)
        await pilot.press("enter")  # Yes
        assert await _held(pilot, client)
        await pilot.press("f3")
        await pilot.pause()
        assert not isinstance(app.screen, PreviewScreen)
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


def test_quitting_during_a_read_does_not_wait_for_it(tmp_path, user_state):
    """The interpreter joined the read's thread at exit, so the process
    lingered until adrpy answered (up to READ_TIMEOUT)."""
    import time

    client = _holding(tmp_path, "check")
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)
    started = []

    async def scenario(pilot):
        await _walk(app, pilot, ["explore"])
        options = app.screen.query_one("#options")
        options.highlighted = options.get_option_index("explore.check")
        await pilot.press("enter")
        assert await _held(pilot, client)
        started.append(time.monotonic())
        app.exit()

    run_app(app, scenario)
    # Not waiting: a held call would take Holding's 10 s ceiling; 5 s leaves room
    # for the app's own shutdown under the parallel suite's load.
    assert time.monotonic() - started[0] < 5


def test_quitting_during_a_write_leaves_it(tmp_path, user_state):
    """ADR006V01: quitting never waits for a write; it is left to its end."""
    import time

    client = _holding(tmp_path, "approve")
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)
    started = []

    async def scenario(pilot):
        await _approve_and_run(app, pilot)
        assert await _held(pilot, client)
        started.append(time.monotonic())
        app.exit()

    run_app(app, scenario)
    # Not waiting: a held call would take Holding's 10 s ceiling; 5 s leaves room
    # for the app's own shutdown under the parallel suite's load.
    assert time.monotonic() - started[0] < 5


async def _two_keys(app, pilot, *keys):
    """Keys that reach the app back to back, before the first is handled --
    what a busy moment does to keys typed at human speed."""
    from textual import events

    for key in keys:
        app.post_message(events.Key(key, None))
    await settle(pilot)


def test_a_second_key_queued_on_the_key_capture_does_not_close_the_keys_screen(tmp_path, user_state):
    from adrpy_tui.ui.keys import KeyCaptureScreen, KeysScreen

    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        await _walk(app, pilot, ["keys"])
        options = app.screen.query_one("#actions")
        options.highlighted = options.get_option_index("preview")
        await pilot.press("enter")
        await settle(pilot)
        assert isinstance(app.screen, KeyCaptureScreen)
        await _two_keys(app, pilot, "f5", "f6")
        assert isinstance(app.screen, KeysScreen)

    run_app(app, scenario)


def test_a_second_enter_queued_on_a_submenu_s_back_row_does_not_close_the_main_menu(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=_focus_client(tmp_path), user_state=user_state)

    async def scenario(pilot):
        await _walk(app, pilot, ["decisions"])
        options = app.screen.query_one("#options")
        options.highlighted = 0  # Back
        await _two_keys(app, pilot, "enter", "enter")
        assert _stack(app) == ["Screen", "MenuScreen"]

    run_app(app, scenario)


def test_enter_on_a_migrate_preview_row_is_not_taken_for_a_file(tmp_path, user_state):
    """The files list's handler took the preview list's rows for files: a row
    past the number of files raised IndexError and ended the app."""
    from textual.widgets import Button

    client = _focus_client(tmp_path)
    client.answers["explore"]["data"]["migrationpattern_preview"] = [
        {"file": f"/r/{n:04}-x.md", "number": n, "version": 0, "title": "x"} for n in range(1, 6)]
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)

    async def scenario(pilot):
        await _walk(app, pilot, ["repository", "repository.migrate"])
        sample = str(app.screen.query_one("#sample").render())
        app.screen.query_one("#preview", Button).press()
        await settle(pilot)
        options = app.screen.query_one("#preview-options")
        options.focus()
        options.highlighted = 4
        await pilot.press("enter")
        await settle(pilot)
        assert str(app.screen.query_one("#sample").render()) == sample

    run_app(app, scenario)



class _Unprintable(Exception):
    def __str__(self):
        raise RuntimeError("str() itself fails")


def test_a_failure_that_cannot_be_put_into_words_is_still_shown(tmp_path, user_state):
    """The note of a failure was built with f"{error}": an exception whose
    str() raises -- or a message holding a lone surrogate, which the log
    could not encode -- made the failure mechanism itself end the app."""
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state)

    async def scenario(pilot):
        assert "_Unprintable" in app.internal_error_text(_Unprintable())
        assert app.internal_error_text(OSError(2, "gone: a" + chr(0xD800) + "b"))
        assert user_state.error_log.exists()

    run_app(app, scenario)



def test_what_arrives_for_a_screen_already_left_is_dropped(tmp_path, user_state):
    """A change, a list's paging or a read's answer delivered after the
    screen was left must do nothing -- forced here, not left to a race."""
    from adrpy_tui.ui.paged import PagedList

    app = AdrpyTui(tmp_path, client=_focus_client(tmp_path), user_state=user_state)
    shown = []

    async def scenario(pilot):
        await _walk(app, pilot, ["repository", "repository.migrate"])
        migrate = app.screen
        paged = migrate.query_one(PagedList)
        number = migrate._reads
        await app.pop_screen()
        await settle(pilot)
        migrate._refresh()
        paged.update_page()
        await migrate._deliver(number, lambda outcome: shown.append(outcome), "late")
        assert shown == []

    run_app(app, scenario)


def test_a_restart_asked_while_one_is_under_way_reads_the_repository_once(tmp_path, user_state):
    client = _holding(tmp_path, "config", skip=1)
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

    run_app(app, scenario)
    assert client.verbs().count("config") == 2  # the start-up read, then one restart's


def test_esc_on_the_start_up_screen_quits(tmp_path, user_state):
    """While adrpy does not answer the first read, Esc leaves. Run without
    run_app: its settle would wait out the held read, and the main menu --
    whose Esc quits too -- would answer instead."""
    import asyncio

    from adrpy_tui.ui.startup import StartupScreen

    client = _holding(tmp_path, "config")
    app = AdrpyTui(tmp_path, client=client, user_state=user_state)
    quits = []

    async def main():
        async with app.run_test() as pilot:
            assert await _held(pilot, client)
            assert isinstance(app.screen, StartupScreen)
            exit_app = app.exit
            app.exit = lambda *args, **kwargs: quits.append(True)  # recorded, then the real one restored
            await pilot.press("escape")
            await pilot.pause()
            app.exit = exit_app
            client.release.set()

    asyncio.run(main())
    assert quits == [True]