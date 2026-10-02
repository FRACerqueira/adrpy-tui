"""Confirming and running a screen's commands, then showing the result.

Once a run starts, the result replaces the screen when it ends, so nothing
may leave the screen or start another run meanwhile: the screen's body is
disabled (no field or list takes a key; `loading` alone does not stop key
bindings) and `command_running` tells its own key actions to do nothing.
The screens that run commands -- forms, the config editors, migrate -- all
go through here."""

import asyncio
import threading

from textual.containers import Vertical
from textual.widgets import Button, Static

from adrpy_tui.core import client as client_module
from adrpy_tui.core.client import display_command
from adrpy_tui.core.registry import destroys
from adrpy_tui.core.text import visible
from adrpy_tui.ui.confirm import ConfirmScreen
from adrpy_tui.ui.result import ResultScreen


class CommandRunner:
    _command_running = False
    _then = None

    @property
    def command_running(self):
        return self._command_running

    def running_hints(self):
        """The key line while a command runs: Leave's key, once it is there."""
        return (("enter", "leave"),) if self.query("#leave-running") else ()

    def confirm_and_run(self, commands, then=None, also=None):
        """Asks with every command line, then runs them in order, stopping at
        the first that fails; the result shown is the last one run. `then`
        gets a success's result once it is shown, and `also` says on the
        confirmation what it will do."""
        if self._command_running:
            return
        lines = "\n".join(visible(display_command(command, flags)) for command, flags in commands)
        # A CR cannot be drawn: a value keeping CRLF line endings is said so.
        crlf = any("\r\n" in str(flag) for _, flags in commands for flag in flags)
        note = "\n".join(text for text in (self.app.texts("confirm.crlf") if crlf else None, also) if text) or None
        self._then = then
        danger = any(destroys(command, flags, self.app.configured) for command, flags in commands)
        self.app.push_screen(ConfirmScreen(lines, note=note, danger=danger), lambda yes: yes and self._run(commands))

    def _run(self, commands):
        if self._command_running:
            return
        self._command_running = True
        body = self.query_one("#body")
        body.loading = True
        body.disabled = True
        self.refresh_hints()
        app = self.app  # the worker reaches the app directly, never through this screen
        leave = self._leave = threading.Event()

        def work():
            # Client.run returns a Result whatever happens (core/client.py).
            for command, flags in commands:
                result = app.client.run(command, flags, write=True, leave=leave)
                if not result.success:
                    break
            app.call_from_thread(self._finish, command, result)

        app.run_worker(work, thread=True)
        # A write is never stopped; past the time a read may take, the person
        # is told and may leave it (ADR0006V02). The loop's own timer: a
        # Textual timer sleeps in a thread on Windows, and one still sleeping
        # at quit held the app about READ_TIMEOUT.
        self._still_running = asyncio.get_running_loop().call_later(client_module.READ_TIMEOUT,
                                                                    self._say_still_running)

    async def _finish(self, command, result):
        """The result replaces this screen -- whatever was opened over it."""
        app = self.app
        self._still_running.cancel()
        if not self.is_attached or self not in app.screen_stack:  # closed meanwhile, or the app quitting
            return
        while app.screen is not self and self in app.screen_stack:
            await app.pop_screen()
        await app.switch_screen(ResultScreen(command, result))
        if result.success and self._then:
            # From the event loop, as an Edit chosen on screen: not inside this
            # finish, which the write's worker is still waiting on.
            app.call_later(self._then, result)

    def _say_still_running(self):
        if not self.is_attached or not self._command_running or self.query("#still-running"):
            return
        texts = self.app.texts
        self.mount(Vertical(
            Static(texts("running.still", seconds=client_module.READ_TIMEOUT), id="still-running-note",
                   classes="warning", markup=False),
            Button(texts("running.leave"), id="leave-running", variant="warning", action="screen.leave_running"),
            id="still-running"), before=self.query_one("#hints"))
        # The only key that acts now: given the focus, named on the line.
        self.call_after_refresh(lambda: self.is_attached and self.query_one("#leave-running").focus())

    def action_leave_running(self):
        """Stops waiting for the write; adrpy goes on to its own end."""
        self._leave.set()
