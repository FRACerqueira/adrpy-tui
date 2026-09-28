"""Confirming and running a screen's commands, then showing the result.

Once a run starts, the result replaces the screen when it ends, so nothing
may leave the screen or start another run meanwhile: the screen's body is
disabled (no field or list takes a key; `loading` alone does not stop key
bindings) and `command_running` tells its own key actions to do nothing.
The screens that run commands -- forms, the config editors, migrate -- all
go through here."""

import threading

from textual.containers import Vertical
from textual.widgets import Button, Static

from adrpy_tui.core import client as client_module
from adrpy_tui.core.client import INTERNAL_ERROR, Result, display_command
from adrpy_tui.core.text import visible
from adrpy_tui.ui.confirm import ConfirmScreen
from adrpy_tui.ui.result import ResultScreen


class CommandRunner:
    _command_running = False

    @property
    def command_running(self):
        return self._command_running

    def confirm_and_run(self, commands):
        """Asks with every command line, then runs them in order, stopping at
        the first that fails; the result shown is the last one run."""
        if self._command_running:
            return
        lines = "\n".join(visible(display_command(command, flags)) for command, flags in commands)
        self.app.push_screen(ConfirmScreen(lines), lambda yes: yes and self._run(commands))

    def _run(self, commands):
        if self._command_running:
            return
        self._command_running = True
        body = self.query_one("#body")
        body.loading = True
        body.disabled = True
        app = self.app  # the worker reaches the app directly, never through this screen
        leave = self._leave = threading.Event()
        app.running_leaves.add(leave)

        def work():
            command = commands[0][0]
            try:
                for command, flags in commands:
                    result = app.client.run(command, flags, write=True, leave=leave)
                    if not result.success:
                        break
            except Exception as error:  # noqa: BLE001 -- shown as the result, never lost
                result = Result((), -1, False, code=INTERNAL_ERROR, detail=app.internal_error_text(error))
            app.call_from_thread(self._finish, command, result)

        app.run_worker(work, thread=True)
        # A write is never stopped; past the time a read may take, the person
        # is told and may leave it (ADR006V01).
        self._still_running = self.set_timer(client_module.READ_TIMEOUT, self._say_still_running)

    async def _finish(self, command, result):
        """The result replaces this screen -- whatever was opened over it."""
        app = self.app
        app.running_leaves.discard(self._leave)
        self._still_running.stop()
        while app.screen is not self and self in app.screen_stack:
            await app.pop_screen()
        await app.switch_screen(ResultScreen(command, result))

    def _say_still_running(self):
        if not self._command_running or self.query("#still-running"):
            return
        texts = self.app.texts
        self.mount(Vertical(
            Static(texts("running.still", seconds=client_module.READ_TIMEOUT), id="still-running-note",
                   classes="warning", markup=False),
            Button(texts("running.leave"), id="leave-running", action="screen.leave_running"),
            id="still-running"), before=self.query_one("#hints"))

    def action_leave_running(self):
        """Stops waiting for the write; adrpy goes on to its own end."""
        self._leave.set()
