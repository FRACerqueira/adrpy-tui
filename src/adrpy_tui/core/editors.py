"""The editors a Proposed decision opens in (ADR0007V01): a closed list of
the ones that return only once the file is closed, each found on the PATH
of the system the TUI runs on."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Editor:
    name: str
    program: str
    # What makes it wait for the file to be closed.
    args: tuple = ()
    # It takes the terminal: the TUI is suspended while it runs.
    terminal: bool = False


EDITORS = (
    Editor("vim", "vim", terminal=True),
    Editor("nvim", "nvim", terminal=True),
    Editor("nano", "nano", terminal=True),
    Editor("micro", "micro", terminal=True),
    Editor("hx", "hx", terminal=True),
    Editor("code", "code", ("--wait",)),
    Editor("codium", "codium", ("--wait",)),
    Editor("subl", "subl", ("--wait",)),
    Editor("kate", "kate", ("--block",)),
    Editor("gedit", "gedit", ("--standalone",)),
    Editor("gvim", "gvim", ("-f",)),
    Editor("notepad", "notepad"),
)


def find(name):
    return next((editor for editor in EDITORS if editor.name == name), None)


# What CreateProcess starts (.cmd and .bat through cmd.exe); PATHEXT may also
# list scripts it cannot (.VBS, .JS).
_RUNNABLE = (".com", ".exe", ".bat", ".cmd")


def located(editor):
    """The program's path on this system's PATH, or None. Only absolute
    entries are searched, never the current folder -- which is the
    repository, and where shutil.which looks first on Windows: a launcher a
    cloned repository ships would be taken for the editor."""
    if os.name == "nt":
        extensions = [ext for ext in os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";")
                      if ext.lower() in _RUNNABLE]
        names = [editor.program + ext for ext in extensions]
    else:
        names = [editor.program]
    for folder in os.environ.get("PATH", "").split(os.pathsep):
        if not os.path.isabs(folder):
            continue
        for name in names:
            candidate = os.path.join(folder, name)
            if os.path.isfile(candidate) and (os.name == "nt" or os.access(candidate, os.X_OK)):
                return candidate
    return None


def command(editor, program, file):
    """What starts `program` (located) on `file`, and its environment (None:
    the TUI's own)."""
    if os.name == "nt" and program.lower().endswith((".cmd", ".bat")):
        return _through_cmd(editor, program, file)
    return [program, *editor.args, file], None


def _through_cmd(editor, program, file):
    """A .cmd launcher (code.cmd) runs through cmd.exe, which splits an
    unquoted argument at a comma, expands %VAR% and takes & as a second
    command -- all of which a decision's name may hold. The paths reach it
    as variables: expanded once, their values are never parsed again, and
    quoted they keep commas, & and ^ (`/v:off`: ! too)."""
    env = {**os.environ, "ADRPY_TUI_PROGRAM": program, "ADRPY_TUI_FILE": file}
    flags = "".join(f" {arg}" for arg in editor.args)  # the table's own, plain words
    # As Python's own shell=True: COMSPEC, else System32's cmd.exe, never one
    # found in the current folder.
    shell = os.environ.get("COMSPEC", "").strip('"') or os.path.join(
        os.environ.get("SystemRoot", r"C:\Windows"), "System32", "cmd.exe")
    return f'"{shell}" /d /v:off /s /c ""%ADRPY_TUI_PROGRAM%"{flags} "%ADRPY_TUI_FILE%""', env
