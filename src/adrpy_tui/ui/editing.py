"""A Proposed decision opened in the person's editor, then `adrpy check`
(ADR0007V01). The TUI starts the editor and waits; the editor writes the
file, never the TUI."""

import os
import threading
from pathlib import Path

from textual.app import SuspendNotSupported
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from adrpy_tui.core import editors
from adrpy_tui.core.files import is_file, outside_reason
from adrpy_tui.core.text import visible
from adrpy_tui.ui.base import dialog_keys, on_top
from adrpy_tui.ui.check import CheckScreen
from adrpy_tui.ui.preview import refusal


def edit_decision(app, path):
    """Opens `path` in the editor chosen (app.editor), then shows check; says
    why not when it can't be. Only a file of the decisions folder is opened,
    by its absolute path: the editor takes it as given."""
    editor = app.editor
    if editor is None:
        return
    path = Path(os.path.normpath(os.path.abspath(path)))
    reason = outside_reason(app.repo, path)
    folder = os.path.normpath(os.path.abspath(app.repo / app.folderadr))
    if reason is None and os.path.commonpath([folder, str(path)]) != folder:
        reason = "outside"
    if reason:
        app.notify(refusal(app, reason, path), severity="warning", markup=False)
        return
    if not is_file(path):
        app.notify(app.texts("preview.missing", path=visible(str(path))), severity="warning", markup=False)
        return
    if app.client.still_writing():
        # The file a left write rewrites, or a left editor still has open:
        # saving it here would undo the other.
        app.notify(app.texts("editing.writing"), severity="warning", markup=False)
        return
    program = editors.located(editor)
    if program is None:
        app.notify(app.texts("editing.gone", editor=editor.name), severity="warning", markup=False)
        return
    command, env = editors.command(editor, program, str(path))
    if not editor.terminal:
        app.push_screen(EditorWaitScreen(editor, path, command, env))
        return
    error = None
    try:
        with app.suspend():
            # Caught inside: Textual resumes the TUI only after a body that
            # returned, and would leave it suspended, drawing nothing.
            try:
                code = app.client.edit_in_terminal(command, env)
            except OSError as failure:
                error = failure
    except SuspendNotSupported:
        app.notify(app.texts("editing.no_terminal", editor=editor.name), severity="warning", markup=False)
        return
    if error is not None:
        _failed(app, editor, error)
    else:
        _edited(app, editor, code, path)


def _failed(app, editor, error):
    app.notify(app.texts("editing.failed", editor=editor.name, error=visible(str(error))), severity="error",
               markup=False)


def _edited(app, editor, code, path):
    """Check, once the editor is closed (code) or left open (None)."""
    if code is None:
        app.notify(app.texts("editing.left", editor=editor.name), severity="warning", markup=False)
    elif code:
        app.notify(app.texts("editing.exit_code", editor=editor.name, code=code), severity="warning", markup=False)
    if code is not None and not _utf8(path):
        app.notify(app.texts("editing.not_utf8", file=visible(path.name)), severity="warning", markup=False)
    app.push_screen(CheckScreen(edited=path))


def _utf8(path):
    """Whether the file the editor saved is UTF-8 -- or could not be read,
    which check says. adrpy check passes a cp1252 file, and approve then
    replaces each byte that is not UTF-8 with U+FFFD, the text lost."""
    try:
        path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return False
    except OSError:
        pass
    return True


class EditorWaitScreen(ModalScreen):
    """While an editor with a window is open on the decision: as a write
    runs, nothing else does (the screen below takes no key), and the person
    may stop waiting (ADR0007V01) -- with its button only: Esc, pressed by
    habit to leave the result below, would leave the editor open."""

    def __init__(self, editor, path, command, env):
        super().__init__()
        self._editor = editor
        self._path = path
        self._command = command
        self._env = env
        self._leave = threading.Event()

    def compose(self):
        texts = self.app.texts
        with Vertical(id="dialog"):
            yield Static(texts("editing.waiting", editor=self._editor.name, file=visible(self._path.name)),
                         id="editor-waiting", markup=False)
            with Horizontal(id="buttons"):
                yield Button(texts("editing.stop"), id="stop-waiting", variant="warning")
            yield dialog_keys(self.app, self.hints())

    def hints(self):
        return (("enter", "stop_waiting"),)

    def on_mount(self):
        self.query_one("#stop-waiting", Button).focus()
        app = self.app  # the worker reaches the app directly, never through this screen

        def work():
            try:
                code, error = app.client.edit(self._command, self._env, self._leave), None
            except OSError as failure:
                code, error = None, failure
            app.call_from_thread(self._done, code, error)

        app.run_worker(work, thread=True)

    def on_button_pressed(self, event):
        if not on_top(self):
            return
        if event.button.id == "stop-waiting":
            self.action_stop_waiting()

    def action_stop_waiting(self):
        """The editor stays open; the waiting ends as the client sees it."""
        self._leave.set()

    async def _done(self, code, error):
        app = self.app
        if not self.is_attached or self not in app.screen_stack:  # the app quitting
            return
        # This screen, not whatever was opened over it.
        while app.screen is not self and self in app.screen_stack:
            await app.pop_screen()
        await app.pop_screen()
        if error is not None:
            _failed(app, self._editor, error)
        else:
            _edited(app, self._editor, code, self._path)
