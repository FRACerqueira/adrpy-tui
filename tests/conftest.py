import asyncio
import json
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from adrpy_tui.core.client import Client
from adrpy_tui.core.state import UserState


@pytest.fixture(autouse=True)
def no_pypi(monkeypatch):
    """No test reaches PyPI (ADR0008V01): the check fails as with no network,
    unless a test gives the app its own `published`."""
    from adrpy_tui.core import updates

    def offline():
        raise OSError("no network in tests")

    monkeypatch.setattr(updates, "published", offline)


@pytest.fixture
def client():
    return Client()


FIXTURE_CONFIG = Path(__file__).parent / "fixtures" / ".adrpy.json"


@pytest.fixture
def repo(tmp_path, client):
    """A repository initialized by the real adrpy from the fixture config --
    never from this machine's install-level config."""
    result = client.run("init", ("--path", str(tmp_path), "--seed", str(FIXTURE_CONFIG)))
    assert result.success, result
    return tmp_path


@pytest.fixture
def user_state(tmp_path_factory):
    """A per-user state that already chose English, in its own folder."""
    state = UserState(tmp_path_factory.mktemp("state") / "state.json")
    state.set_language("en-us")
    return state


def command_of(argv):
    """The command an adrpy argv runs ("new", "skills:list"): the verb
    right after `-m <module>`, wherever the interpreter's options put it."""
    at = argv.index("-m")
    module, verb = argv[at + 1], argv[at + 2]
    return f"skills:{verb}" if module == "adrpy.skills" else verb


def completed(payload, returncode=0, stderr=""):
    stdout = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.CompletedProcess([], returncode, stdout=stdout, stderr=stderr)


@dataclass
class FakeClient(Client):
    """Records every call and answers from `answers` (command -> payload),
    `{"success": true, "data": {}}` otherwise."""

    answers: dict = field(default_factory=dict)
    calls: list = field(default_factory=list)
    # The editor (ADR0007V01): the commands it was started with, its exit
    # code once `editor_closed` is set, or what starting it raises.
    edits: list = field(default_factory=list)
    editor_code: int = 0
    editor_error: Exception | None = None
    editor_closed: threading.Event = field(default_factory=threading.Event)

    def __post_init__(self):
        super().__init__(runner=self._answer)

    def edit(self, command, env, leave=None):
        self.edits.append((command, env))
        if self.editor_error:
            raise self.editor_error
        deadline = time.monotonic() + 20  # a regressed test fails, not hangs
        while not self.editor_closed.wait(0.02) and time.monotonic() < deadline:
            if (leave is not None and leave.is_set()) or self._closing.is_set():
                self._left.append(_OpenEditor(self.editor_closed))
                return None
        return self.editor_code

    def edit_in_terminal(self, command, env):
        self.edits.append((command, env))
        if self.editor_error:
            raise self.editor_error
        return self.editor_code

    def _answer(self, argv, **_):
        self.calls.append(argv)
        return completed(self.answers.get(command_of(argv), {"success": True, "data": {"warnings": []}}))

    def verbs(self):
        return [command_of(argv).removeprefix("skills:") for argv in self.calls]


class _OpenEditor:
    """A left editor, open until its `closed` event is set."""

    def __init__(self, closed):
        self._closed = closed

    def poll(self):
        return 0 if self._closed.is_set() else None


def run_app(app, scenario, size=(120, 60)):
    """Runs `scenario(pilot)` against `app`, headless."""

    async def main():
        async with app.run_test(size=size) as pilot:
            await settle(pilot)
            await scenario(pilot)

    asyncio.run(main())


async def settle(pilot):
    """Waits for the workers the last action started and what they did --
    all but a DirectoryTree's folder loader, which runs as long as the tree
    does (it never completes)."""
    from textual.widgets import DirectoryTree

    for _ in range(3):
        finishing = [worker for worker in pilot.app.workers if not isinstance(worker.node, DirectoryTree)]
        if finishing:  # an empty list would mean every worker to Textual
            await pilot.app.workers.wait_for_complete(finishing)
        await pilot.pause()
