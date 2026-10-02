"""The notice of a newer adrpy-tui on the main menu, and the Updates screen
(ADR0008V01), driven headless through Textual's Pilot."""

import asyncio
import http.client
import threading
import time

import pytest
from textual.widgets import OptionList, Static

from adrpy_tui.core import versions
from adrpy_tui.ui.app import AdrpyTui
from adrpy_tui.ui.menu import MenuScreen
from adrpy_tui.ui.updates import UpdatesScreen

from conftest import FakeClient, run_app, settle


@pytest.fixture(autouse=True)
def installed_0_2_0(monkeypatch):
    real = versions.installed_version
    monkeypatch.setattr(versions, "installed_version", lambda name: "0.2.0" if name == "adrpy-tui" else real(name))


class Published:
    """PyPI's versions, counting the times they are asked for."""

    def __init__(self, *found, error=None):
        self.found, self.error, self.calls = list(found), error, 0

    def __call__(self):
        self.calls += 1
        if self.error:
            raise self.error
        return self.found


@pytest.fixture
def thread_errors(monkeypatch):
    """What a thread ended with, instead of a return: none is expected."""
    errors = []
    monkeypatch.setattr(threading, "excepthook", lambda args: errors.append(args.exc_value))
    return errors


async def _answered(pilot):
    """Waits until the app has PyPI's answer, or knows the check failed."""
    for _ in range(100):
        if pilot.app.update_status not in ("checking",):
            return
        await pilot.pause(0.02)
    raise AssertionError("PyPI's answer never came")


async def _notice(pilot, shown=True):
    """The main menu's notice, once the check has answered (it runs on its own thread)."""
    for _ in range(100):
        notice = pilot.app.screen.query_one("#newer-version", Static)
        if notice.display == shown and (not shown or str(notice.render())):
            return notice
        await pilot.pause(0.02)
    return notice


def test_a_newer_version_on_pypi_is_said_on_the_main_menu(tmp_path, user_state):
    published = Published("0.1.0", "0.2.0", "0.3.0")
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state, published=published)

    async def scenario(pilot):
        notice = await _notice(pilot)
        assert notice.display
        assert str(notice.render()) == "adrpy-tui 0.3.0 is available (installed: 0.2.0)."

    run_app(app, scenario)
    assert published.calls == 1


@pytest.mark.parametrize("answer", [{"found": ("0.1.0", "0.2.0")}, {"error": OSError("offline")},
                                    {"error": ValueError("not json")}, {"error": http.client.BadStatusLine("garbage")}],
                         ids=["up-to-date", "offline", "unreadable", "not-http"])
def test_no_newer_version_or_a_failed_check_says_nothing(tmp_path, user_state, answer, thread_errors):
    published = Published(*answer.get("found", ()), error=answer.get("error"))
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state, published=published)

    async def scenario(pilot):
        await _answered(pilot)
        assert not app.screen.query_one("#newer-version", Static).display
        assert isinstance(app.screen, MenuScreen)

    run_app(app, scenario)
    assert published.calls == 1
    assert not user_state.error_log.exists()
    assert thread_errors == []


def test_with_the_check_off_pypi_is_not_asked(tmp_path, user_state):
    user_state.set_update_check(False)
    published = Published("9.0.0")
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state, published=published)

    async def scenario(pilot):
        await pilot.pause(0.2)
        assert not app.screen.query_one("#newer-version", Static).display

    run_app(app, scenario)
    assert published.calls == 0


async def _open_updates(pilot):
    options = pilot.app.screen.query_one("#options", OptionList)
    options.highlighted = options.get_option_index("updates")
    await pilot.press("enter")
    await settle(pilot)
    return pilot.app.screen.query_one("#settings", OptionList)


def _prompt(settings, setting):
    return str(settings.get_option(setting).prompt)


def test_pre_releases_are_said_only_once_included(tmp_path, user_state):
    published = Published("0.2.0", "0.3.0rc1")
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state, published=published)

    async def scenario(pilot):
        await _notice(pilot, shown=False)
        await pilot.pause(0.2)
        assert not app.screen.query_one("#newer-version", Static).display
        settings = await _open_updates(pilot)
        assert isinstance(app.screen, UpdatesScreen)
        assert _prompt(settings, "check").startswith("[x] ") and _prompt(settings, "prereleases").startswith("[ ] ")
        settings.highlighted = settings.get_option_index("prereleases")
        await pilot.press("enter")
        await settle(pilot)
        assert _prompt(settings, "prereleases").startswith("[x] ")
        assert user_state.prereleases is True
        await pilot.press("escape")
        await settle(pilot)
        notice = await _notice(pilot)
        assert str(notice.render()) == "adrpy-tui 0.3.0rc1 is available (installed: 0.2.0)."

    run_app(app, scenario)


def test_turning_the_check_off_hides_the_notice_and_on_again_asks_once(tmp_path, user_state):
    user_state.set_update_check(False)
    published = Published("0.3.0")
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state, published=published)

    async def scenario(pilot):
        settings = await _open_updates(pilot)
        assert _prompt(settings, "check").startswith("[ ] ")
        settings.highlighted = settings.get_option_index("check")
        await pilot.press("enter")
        await settle(pilot)
        assert user_state.update_check is True
        await pilot.press("escape")
        await settle(pilot)
        await _notice(pilot)
        settings = await _open_updates(pilot)
        settings.highlighted = settings.get_option_index("check")
        await pilot.press("enter")  # off
        await pilot.press("enter")  # on again: already asked in this run
        await pilot.press("enter")  # off
        await settle(pilot)
        await pilot.press("escape")
        await settle(pilot)
        assert not app.screen.query_one("#newer-version", Static).display

    run_app(app, scenario)
    assert published.calls == 1
    assert user_state.update_check is False


def test_pypi_is_asked_once_per_run_not_on_each_restart(tmp_path, user_state):
    published = Published("0.3.0")
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state, published=published)

    async def scenario(pilot):
        await _notice(pilot)
        await app.reload_repository()
        await settle(pilot)
        notice = await _notice(pilot)
        assert str(notice.render()) == "adrpy-tui 0.3.0 is available (installed: 0.2.0)."

    run_app(app, scenario)
    assert published.calls == 1


def test_quitting_does_not_wait_for_pypi(tmp_path, user_state):
    """The check runs on a daemon thread: an answer that never comes keeps
    neither the app nor the process from ending."""
    hanging, asked = threading.Event(), threading.Event()

    def published():
        asked.set()
        hanging.wait(30)
        return ["9.0.0"]

    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state, published=published)

    async def scenario(pilot):
        assert asked.wait(5)
        assert next(t for t in threading.enumerate() if t.name == "update-check").daemon
        app.exit()

    started = time.monotonic()
    run_app(app, scenario)
    assert time.monotonic() - started < 10
    hanging.set()


def test_an_answer_after_the_app_has_quit_is_dropped(tmp_path, user_state, thread_errors):
    release = threading.Event()

    def published():
        release.wait(10)
        return ["9.0.0"]

    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state, published=published)

    async def scenario(pilot):
        await asyncio.sleep(0)

    run_app(app, scenario)
    thread = next(t for t in threading.enumerate() if t.name == "update-check")
    release.set()
    thread.join(5)
    assert not thread.is_alive()
    assert not user_state.error_log.exists()
    assert thread_errors == []


def test_a_failure_showing_the_answer_is_not_swallowed(tmp_path, user_state, monkeypatch):
    """A bug in the TUI's own hand-off fails as any other handler's would,
    instead of ending quietly in the check's thread."""

    def broken(screen):
        if screen.app.published_versions is not None:
            raise KeyError("a bug in the notice")

    monkeypatch.setattr(MenuScreen, "say_the_newer_version", broken)
    answer = threading.Event()

    def published():  # answers once the main menu is shown, so only the hand-off can meet the bug
        answer.wait(10)
        return ["0.3.0"]

    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state, published=published)

    async def scenario(pilot):
        assert isinstance(app.screen, MenuScreen)
        answer.set()
        for _ in range(100):
            await pilot.pause(0.02)

    with pytest.raises(KeyError, match="a bug in the notice"):
        run_app(app, scenario)


async def _status(pilot):
    return str(pilot.app.screen.query_one("#update-status", Static).render())


@pytest.mark.parametrize("answer, says", [
    ({"found": ("0.2.0", "0.3.0")}, "adrpy-tui 0.3.0 is available (installed: 0.2.0)."),
    ({"found": ("0.1.0", "0.2.0", "0.3.0rc1")}, "No newer version on PyPI (installed: 0.2.0)."),
    ({"error": OSError("offline")}, "PyPI could not be asked, or its answer could not be read, in this run."),
], ids=["available", "current", "failed"])
def test_the_updates_screen_says_what_the_check_found(tmp_path, user_state, answer, says):
    published = Published(*answer.get("found", ()), error=answer.get("error"))
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state, published=published)

    async def scenario(pilot):
        await _answered(pilot)
        await _open_updates(pilot)
        assert await _status(pilot) == says

    run_app(app, scenario)


def test_the_updates_screen_says_while_pypi_is_asked_and_when_the_check_is_off(tmp_path, user_state):
    answer = threading.Event()

    def published():
        answer.wait(10)
        return ["0.3.0"]

    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state, published=published)

    async def scenario(pilot):
        settings = await _open_updates(pilot)
        assert await _status(pilot) == "Asking PyPI..."
        answer.set()
        for _ in range(100):
            if await _status(pilot) != "Asking PyPI...":
                break
            await pilot.pause(0.02)
        assert await _status(pilot) == "adrpy-tui 0.3.0 is available (installed: 0.2.0)."
        settings.highlighted = settings.get_option_index("check")
        await pilot.press("enter")
        await settle(pilot)
        assert await _status(pilot) == "The check is off: the TUI does not ask PyPI."

    run_app(app, scenario)
    answer.set()


def test_space_marks_a_setting_as_enter_does_and_the_key_line_says_so(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=FakeClient(), user_state=user_state, published=Published())

    async def scenario(pilot):
        settings = await _open_updates(pilot)
        settings.highlighted = settings.get_option_index("prereleases")
        await settle(pilot)
        assert "Space/Enter mark" in str(app.screen.query_one("#hints", Static).render())
        await pilot.press("space")
        await settle(pilot)
        assert user_state.prereleases is True and _prompt(settings, "prereleases").startswith("[x] ")
        settings.highlighted = settings.get_option_index("back")
        await settle(pilot)
        line = str(app.screen.query_one("#hints", Static).render())
        assert "mark" not in line and "Enter select" in line

    run_app(app, scenario)
