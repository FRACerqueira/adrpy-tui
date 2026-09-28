"""Confirming and running a screen's commands, then showing the result.

Once a run starts, the result replaces the screen when it ends, so nothing
may leave the screen or start another run meanwhile: the screen's body is
disabled (no field or list takes a key; `loading` alone does not stop key
bindings) and `command_running` tells its own key actions to do nothing.
The screens that run commands -- forms, the config editors, migrate -- all
go through here."""

from adrpy_tui.core.client import display_command
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
        lines = "\n".join(display_command(command, flags) for command, flags in commands)
        self.app.push_screen(ConfirmScreen(lines), lambda yes: yes and self._run(commands))

    def _run(self, commands):
        if self._command_running:
            return
        self._command_running = True
        body = self.query_one("#body")
        body.loading = True
        body.disabled = True
        app = self.app  # the worker reaches the app directly, never through this screen

        def work():
            for command, flags in commands:
                result = app.client.run(command, flags)
                if not result.success:
                    break
            app.call_from_thread(app.switch_screen, ResultScreen(command, result))

        app.run_worker(work, thread=True)
