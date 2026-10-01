"""The editors a Proposed decision opens in (ADR0007V01): the closed list,
how each is found on PATH, and the command that starts it."""

import json
import os
import subprocess
import sys

import pytest

from adrpy_tui.core import editors
from adrpy_tui.core.state import UserState

# ADR0007V01R02, item 2.
LISTED = {"vim", "nvim", "nano", "micro", "hx", "code", "codium", "subl", "kate", "gedit", "gvim", "notepad"}
# What a decision's name may hold that a Windows .cmd launcher mangles:
# adrpy's titles refuse only <>:"/\|?* and controls.
AWKWARD = "ADR0001V01R01-a,b's %PATH% & c^d!e (f) ç中文.md"


def test_the_list_is_the_adr_s_and_visual_studio_is_not_on_it():
    assert {editor.name for editor in editors.EDITORS} == LISTED
    assert editors.find("devenv") is None


@pytest.mark.parametrize("name, waits_with, terminal", [
    ("vim", (), True), ("nano", (), True), ("hx", (), True),
    ("code", ("--wait",), False), ("codium", ("--wait",), False), ("subl", ("--wait",), False),
    ("kate", ("--block",), False), ("gedit", ("--standalone",), False), ("gvim", ("-f",), False),
    ("notepad", (), False),
])
def test_each_editor_waits_for_its_file_to_be_closed(name, waits_with, terminal):
    editor = editors.find(name)
    assert editor.args == waits_with and editor.terminal is terminal


def test_the_command_is_the_program_its_wait_flag_and_the_file():
    command, env = editors.command(editors.find("code"), "/usr/bin/code", "/r/doc/adr/x.md")
    assert command == ["/usr/bin/code", "--wait", "/r/doc/adr/x.md"]
    assert env is None


@pytest.mark.skipif(sys.platform != "win32", reason="a .cmd launcher runs through cmd.exe on Windows only")
def test_a_cmd_launcher_gets_the_decision_s_name_whole(tmp_path):
    """code is code.CMD on Windows: cmd.exe splits an unquoted argument at a
    comma, expands %PATH% and takes & as a second command -- in the file's
    name and in the launcher's own folder (VS Code's lives in the person's
    profile). The fake forwards %* as code.cmd does, to Python, which gets
    the arguments whole, non-ASCII too."""
    folder = tmp_path / "A&B %PATH% (x) !y^ ,;="
    folder.mkdir()
    (folder / "record.py").write_text(
        "import json, pathlib, sys\n"
        "pathlib.Path(__file__).with_name('received.json').write_text(json.dumps(sys.argv[1:]), encoding='utf-8')\n",
        encoding="utf-8")
    launcher = folder / "FAKE.CMD"
    launcher.write_text(f'@echo off\r\nsetlocal\r\n"{sys.executable}" "%~dp0record.py" %*\r\n', encoding="ascii")
    file = str(tmp_path / AWKWARD)
    command, env = editors.command(editors.find("code"), str(launcher), file)
    subprocess.run(command, env=env, check=True, timeout=60)
    assert json.loads((folder / "received.json").read_text(encoding="utf-8")) == ["--wait", file]


def _program_in(folder, name):
    """A program `name` in `folder`, as this system runs one."""
    if sys.platform == "win32":
        program = folder / f"{name}.cmd"
        program.write_text("@echo off\r\n", encoding="ascii")
    else:
        program = folder / name
        program.write_text("#!/bin/sh\n", encoding="ascii")
        program.chmod(0o755)
    return program


def test_an_editor_is_found_on_path(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))
    assert editors.located(editors.find("notepad")) is None
    program = _program_in(tmp_path, "notepad")
    assert os.path.normcase(editors.located(editors.find("notepad"))) == os.path.normcase(str(program))


def test_an_editor_in_the_current_folder_is_not_taken(tmp_path, monkeypatch):
    """The TUI runs in the repository: a notepad.cmd shipped with a cloned
    repository is not the editor on PATH. Python's shutil.which looks in
    the current folder first on Windows."""
    repository, bin_folder = tmp_path / "repo", tmp_path / "bin"
    repository.mkdir()
    bin_folder.mkdir()
    _program_in(repository, "notepad")
    monkeypatch.chdir(repository)
    monkeypatch.delenv("NoDefaultCurrentDirectoryInExePath", raising=False)
    monkeypatch.setenv("PATH", str(bin_folder))
    assert editors.located(editors.find("notepad")) is None


def test_a_relative_path_entry_is_not_searched(tmp_path, monkeypatch):
    """"." or an empty entry on PATH is the current folder again."""
    _program_in(tmp_path, "notepad")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("NoDefaultCurrentDirectoryInExePath", raising=False)
    for path in (".", os.pathsep, f"{os.pathsep}."):
        monkeypatch.setenv("PATH", path)
        assert editors.located(editors.find("notepad")) is None, path


@pytest.mark.skipif(sys.platform != "win32", reason="PATHEXT is Windows'")
def test_only_a_program_windows_starts_is_taken(tmp_path, monkeypatch):
    """PATHEXT also lists .VBS, .JS, .WSF: a script CreateProcess cannot start."""
    (tmp_path / "notepad.vbs").write_text("", encoding="ascii")
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("PATHEXT", ".COM;.EXE;.BAT;.CMD;.VBS;.JS")
    assert editors.located(editors.find("notepad")) is None


def test_the_editor_is_kept_per_user_and_none_is_the_default(tmp_path):
    path = tmp_path / "state.json"
    state = UserState(path)
    assert state.editor is None
    state.set_editor("code")
    assert UserState(path).editor == "code"
    state.set_editor(None)
    assert UserState(path).editor is None


def test_a_stored_editor_that_is_not_text_is_none(tmp_path):
    path = tmp_path / "state.json"
    path.write_text('{"editor": 3}', encoding="utf-8")
    assert UserState(path).editor is None
