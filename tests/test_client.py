import os
import sys
import threading
import time

import pytest

from adrpy_tui.core import client as client_module
from adrpy_tui.core.client import ABANDONED, CONTRACT_VIOLATION, RUN_FAILED, TIMED_OUT, Client, display_command

from conftest import completed


def _client(payload, returncode=0, stderr=""):
    calls = []

    def runner(argv, **_):
        calls.append(argv)
        return completed(payload, returncode, stderr)

    return Client(runner=runner), calls


def test_runs_adrpy_from_this_interpreter():
    client, calls = _client({"success": True, "data": {"warnings": []}})
    client.run("new", ("--path", "."))
    assert calls == [[sys.executable, "-P", "-m", "adrpy", "new", "--path", "."]]


def test_runs_adrpy_skills_from_this_interpreter():
    client, calls = _client({"success": True, "data": {"warnings": []}})
    client.run("skills:list")
    assert calls == [[sys.executable, "-P", "-m", "adrpy.skills", "list"]]


def test_help_of_a_skills_command_asks_adrpy_skills():
    client, calls = _client({"success": True, "data": {"commands": []}})
    client.help("skills:install")
    assert calls == [[sys.executable, "-P", "-m", "adrpy.skills", "help", "install"]]


def test_success_carries_data_and_its_warnings():
    client, _ = _client({"success": True, "data": {"created": "x.md", "warnings": ["w"]}})
    result = client.run("new")
    assert result.success and result.data["created"] == "x.md" and result.warnings == ["w"]
    assert result.code is None


def test_failure_carries_code_detail_data_and_top_level_warnings():
    payload = {"success": False, "code": "repository-inconsistent", "detail": "why", "data": {"errors": [{}]}, "warnings": ["w"]}
    client, _ = _client(payload, returncode=1)
    result = client.run("new")
    assert not result.success
    assert (result.code, result.detail, result.data, result.warnings, result.exit_code) == (
        "repository-inconsistent", "why", {"errors": [{}]}, ["w"], 1,
    )


def test_output_that_is_not_json_is_a_contract_violation():
    client, _ = _client("Traceback (most recent call last): ...", returncode=1)
    result = client.run("new")
    assert not result.success and result.code == CONTRACT_VIOLATION
    assert "Traceback" in result.detail


def test_json_without_a_boolean_success_is_a_contract_violation():
    for payload in ('["success"]', '{"data": {}}', '{"success": "yes"}'):
        client, _ = _client(payload)
        assert client.run("new").code == CONTRACT_VIOLATION


def test_empty_stdout_reports_stderr():
    client, _ = _client("", returncode=1, stderr="No module named adrpy")
    assert "No module named adrpy" in client.run("new").detail


def test_a_value_holding_a_line_break_is_shown_quoted_on_windows(monkeypatch):
    """list2cmdline quotes a value only for a space or a tab, so a body
    "first" LF "adrpy-skills" LF "install" read as three command lines on
    the confirmation. Only the display changes; the argv does not."""
    monkeypatch.setattr("sys.platform", "win32")
    body = "first" + chr(10) + "adrpy-skills" + chr(10) + "install"
    line = display_command("log", ["--body", body, "--refdate", "2026-01-01"])
    assert line == 'adrpy log --body "' + body + '" --refdate 2026-01-01'


def test_display_command_is_what_a_person_would_type():
    line = display_command("new", ["--path", "C:/my repo", "--title", "Use it"])
    assert line.startswith("adrpy new --path ")
    assert "my repo" in line and ("'C:/my repo'" in line or '"C:/my repo"' in line)
    assert display_command("skills:list", []) == "adrpy-skills list"


def test_control_characters_in_adrpy_s_answer_never_reach_a_screen():
    """A file name or a header cell is file content adrpy echoes back: an
    escape sequence in it would reach the terminal (Textual does not drop
    ESC). Tab and line breaks, CRLF included, are kept: a template's line
    endings must survive a round trip through the config editor."""
    payload = {"success": False, "code": "no-header", "detail": "bad \x1b]0;owned\x07 file",
               "warnings": ["w\x1b[2J"],
               "data": {"errors": [{"file": "ADR001V01-x\x1b[31m.md", "hint": "a\r\nb\tc\rd"}]}}
    client, _ = _client(payload, returncode=1)
    result = client.run("check")
    assert result.detail == "bad ]0;owned file"
    assert result.warnings == ["w[2J"]
    assert result.data["errors"][0] == {"file": "ADR001V01-x[31m.md", "hint": "a\r\nb\tcd"}


def test_a_folder_named_adrpy_in_the_current_folder_is_never_run(tmp_path, monkeypatch):
    """`python -m` puts the current folder first on the module path: a
    repository holding an `adrpy/` folder ran its own code, with no key
    pressed, when the TUI was started inside it (SECURITY.md)."""
    fake = tmp_path / "adrpy"
    fake.mkdir()
    (fake / "__init__.py").write_text("", encoding="utf-8")
    (fake / "__main__.py").write_text(
        "import pathlib; pathlib.Path('RAN').write_text('x'); print('{\"success\": true, \"data\": {}}')",
        encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = Client().run("config", ("--path", "."))
    assert not (tmp_path / "RAN").exists()
    assert result.code == "config-not-found"  # the installed adrpy's own answer


def _hanging(monkeypatch, seconds, then=""):
    """adrpy replaced by a program that answers after `seconds`, then runs
    `then` (Python code)."""
    code = f"import time; time.sleep({seconds}); {then}"
    monkeypatch.setattr(client_module, "_PROGRAMS", {False: ("adrpy", (sys.executable, "-c", code)),
                                                      True: ("adrpy-skills", (sys.executable, "-c", code))})


def _answering(monkeypatch):
    """adrpy replaced by a program that answers success at once."""
    code = "import json; print(json.dumps({'success': True, 'data': {}}))"
    monkeypatch.setattr(client_module, "_PROGRAMS", {False: ("adrpy", (sys.executable, "-c", code)),
                                                      True: ("adrpy-skills", (sys.executable, "-c", code))})


def test_a_read_that_does_not_answer_is_stopped(monkeypatch):
    """ADR0006V02: a read changes nothing, so one that hangs is stopped and
    becomes a failure; it no longer holds every later call behind it."""
    _hanging(monkeypatch, 20)
    monkeypatch.setattr(client_module, "READ_TIMEOUT", 0.5)
    started = time.monotonic()
    result = Client().run("explore", ("--path", "."))
    assert time.monotonic() - started < 5
    assert (result.success, result.code) == (False, TIMED_OUT)


def test_a_write_is_never_stopped_only_left(tmp_path, monkeypatch):
    """ADR0006V02: a write may be half-way through its files, so the TUI
    never ends it; leaving stops the waiting, and adrpy goes on to its end."""
    marker = tmp_path / "finished"
    _hanging(monkeypatch, 1.5, f"open({str(marker)!r}, 'w').write('x')")
    monkeypatch.setattr(client_module, "READ_TIMEOUT", 0.2)  # not applied to a write
    leave = threading.Event()
    threading.Timer(0.5, leave.set).start()
    started = time.monotonic()
    result = Client().run("new", ("--path", "."), write=True, leave=leave)
    assert time.monotonic() - started < 1.4
    assert (result.success, result.code) == (False, ABANDONED)
    time.sleep(2.5)
    assert marker.exists()  # adrpy was not stopped


def test_adrpy_that_cannot_be_started_is_a_failure_not_an_exception():
    def runner(argv, **_):
        raise FileNotFoundError(2, "No such file", argv[0])

    result = Client(runner=runner).run("explore")
    assert (result.success, result.code) == (False, RUN_FAILED)
    assert "No such file" in result.detail


def test_fields_of_the_wrong_type_are_normalised():
    """A warnings of 5 raised TypeError in a worker (the app ended); a
    string became a list of its characters."""
    for warnings, expected in ((5, []), ("one", ["one"]), ([1, "two"], ["1", "two"]), (None, [])):
        client, _ = _client({"success": True, "data": {"warnings": warnings}})
        assert client.run("explore").warnings == expected
    client, _ = _client({"success": False, "code": 5, "detail": {"x": 1}, "warnings": []})
    result = client.run("explore")
    assert (result.code, result.detail) == ("5", "{'x': 1}")


def test_a_json_too_deep_to_read_is_a_contract_violation():
    client, _ = _client("[" * 100000)
    assert client.run("explore").code == CONTRACT_VIOLATION


def test_one_adrpy_call_at_a_time():
    """architecture.md, boundary 3: never two at once, whichever worker asks."""
    running, most = [0], [0]
    guard = threading.Lock()

    def runner(argv, **_):
        with guard:
            running[0] += 1
            most[0] = max(most[0], running[0])
        time.sleep(0.05)
        with guard:
            running[0] -= 1
        return completed({"success": True, "data": {}})

    client = Client(runner=runner)
    threads = [threading.Thread(target=client.run, args=("explore",)) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert most[0] == 1


def test_a_value_holding_a_line_break_and_ending_in_backslashes_is_shown_as_it_runs(monkeypatch):
    """The wrapper added quotes without doubling the trailing backslashes, so
    the closing quote read as escaped: "a<LF>\\" was shown as a value ending in
    a quote. A trailing backslash is doubled before the closing quote, as the
    Windows rules parse it."""
    monkeypatch.setattr("sys.platform", "win32")
    body = "a" + chr(10) + "b" + chr(92)
    line = display_command("log", ["--body", body])
    assert line == 'adrpy log --body "a' + chr(10) + "b" + chr(92) * 2 + '"'


def test_a_write_waiting_behind_a_hung_read_can_be_left_before_it_starts():
    """Leave only reached a running adrpy: a write queued behind a hung read
    ignored it, then started once the lock was free -- after the person had
    left. Now the waiting for the lock ends too, and the write never starts."""
    release, calls = threading.Event(), []

    def runner(argv, **_):
        calls.append(argv)
        release.wait(10)
        return completed({"success": True, "data": {}})

    client = Client(runner=runner)
    reading = threading.Thread(target=client.run, args=("explore",))
    reading.start()
    time.sleep(0.1)
    leave = threading.Event()
    threading.Timer(0.3, leave.set).start()
    started = time.monotonic()
    result = client.run("new", ("--path", "."), write=True, leave=leave)
    release.set()
    reading.join()
    assert time.monotonic() - started < 1.5
    assert (result.success, result.code) == (False, client_module.NOT_STARTED)
    assert [argv for argv in calls if "new" in argv] == []


def test_a_stopped_read_does_not_wait_for_what_adrpy_left_holding_its_output(monkeypatch):
    """After the kill, the wait for the output was unbounded: a process adrpy
    started, still holding the pipe, kept the call -- and the lock -- as long
    as it lived."""
    grandchild = "import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(20)'])"
    code = f"{grandchild}; time.sleep(20)"
    monkeypatch.setattr(client_module, "_PROGRAMS", {False: ("adrpy", (sys.executable, "-c", code)),
                                                      True: ("adrpy-skills", (sys.executable, "-c", code))})
    monkeypatch.setattr(client_module, "READ_TIMEOUT", 0.5)
    started = time.monotonic()
    result = Client().run("explore")
    assert time.monotonic() - started < 5
    assert result.code == TIMED_OUT


def test_shutdown_stops_a_read_and_leaves_a_write(tmp_path, monkeypatch):
    """Quitting waited for a read in flight (the process lingered up to
    READ_TIMEOUT). shutdown() stops a read -- it changes nothing -- and
    leaves a write to its own end, never stopping it (ADR0006V02)."""
    marker = tmp_path / "finished"
    _hanging(monkeypatch, 1.5, f"open({str(marker)!r}, 'w').write('x')")
    client = Client()
    threading.Timer(0.3, client.shutdown).start()
    started = time.monotonic()
    assert client.run("explore").success is False
    assert time.monotonic() - started < 1.2
    time.sleep(2)
    assert not marker.exists()  # the read's process was stopped

    client = Client()
    threading.Timer(0.3, client.shutdown).start()
    result = client.run("new", write=True)
    assert result.code == ABANDONED
    time.sleep(2.5)
    assert marker.exists()  # the write's was not


def test_a_write_is_refused_while_one_left_running_still_runs(tmp_path, monkeypatch):
    """Leaving a write released the one-call lock while adrpy still wrote: a
    second write could run beside it -- two adrpy processes on one working
    copy, what adrpy-ai's own ADR0001V01 calls a usage error. A read (Check)
    still runs; another write waits until the first has ended."""
    marker = tmp_path / "finished"
    _hanging(monkeypatch, 1.5, f"open({str(marker)!r}, 'w').write('x')")
    client = Client()
    leave = threading.Event()
    threading.Timer(0.3, leave.set).start()
    assert client.run("new", write=True, leave=leave).code == ABANDONED
    assert client.run("approve", write=True).code == client_module.WRITE_STILL_RUNNING
    time.sleep(2)
    assert marker.exists()
    _answering(monkeypatch)
    assert client.run("approve", write=True).success


def test_a_read_runs_while_a_write_left_running_still_runs(tmp_path, monkeypatch):
    _hanging(monkeypatch, 1.5)
    client = Client()
    leave = threading.Event()
    threading.Timer(0.3, leave.set).start()
    assert client.run("new", write=True, leave=leave).code == ABANDONED
    _answering(monkeypatch)
    assert client.run("check").success


def test_other_failures_to_start_adrpy_are_failures_too():
    for error in (ValueError("embedded null character"), TypeError("expected str")):
        def runner(argv, _error=error, **_):
            raise _error

        result = Client(runner=runner).run("explore")
        assert (result.success, result.code) == (False, RUN_FAILED)


def test_an_empty_or_relative_pythonpath_entry_does_not_let_the_current_folder_in(tmp_path, monkeypatch):
    """-P keeps the current folder off the module path, but an empty or "."
    PYTHONPATH entry (left by `set PYTHONPATH=%PYTHONPATH%;C:\\x`) put it
    back: a repository's own adrpy/ ran again."""
    fake = tmp_path / "adrpy"
    fake.mkdir()
    (fake / "__init__.py").write_text("", encoding="utf-8")
    (fake / "__main__.py").write_text("import pathlib; pathlib.Path('RAN').write_text('x')", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    for value in (os.pathsep, ".", "", f"{os.pathsep}C:/elsewhere"):
        monkeypatch.setenv("PYTHONPATH", value)
        result = Client().run("config", ("--path", "."))
        assert not (tmp_path / "RAN").exists(), repr(value)
        assert result.code == "config-not-found"



@pytest.mark.skipif(sys.platform != "win32", reason="Windows' own command-line parser")
def test_the_confirmation_reads_back_as_the_argv_on_windows():
    """A value with a quote and a line break was quoted twice (list2cmdline's
    escape, then ours): Windows read "a\\"b..." back. Every value the forms can
    send is shown so that CommandLineToArgvW returns it exactly."""
    import ctypes
    import itertools
    from ctypes import wintypes

    parse = ctypes.windll.shell32.CommandLineToArgvW
    parse.restype = ctypes.POINTER(wintypes.LPWSTR)
    wrong = []
    for size in range(1, 5):
        for chars in itertools.product('a "\\' + chr(10) + chr(9), repeat=size):
            value = "".join(chars)
            count = ctypes.c_int()
            argv = parse(display_command("log", ["--body", value]), ctypes.byref(count))
            if argv[count.value - 1] != value:
                wrong.append(value)
    assert wrong == []



def test_a_write_already_left_is_never_started(tmp_path, monkeypatch):
    """_run checks leave before starting adrpy; that half of the fix had no
    test. And a call that never started was reported "still running"."""
    marker = tmp_path / "started"
    _hanging(monkeypatch, 0, f"open({str(marker)!r}, 'w').write('x')")
    leave = threading.Event()
    leave.set()
    result = Client().run("new", write=True, leave=leave)
    time.sleep(1.5)
    assert not marker.exists()
    assert result.code == client_module.NOT_STARTED


def test_a_read_stopped_because_the_tui_quits_says_so(monkeypatch):
    _hanging(monkeypatch, 20)
    client = Client()
    threading.Timer(0.3, client.shutdown).start()
    assert client.run("explore").code == client_module.STOPPED


@pytest.mark.skipif(sys.platform == "win32", reason="Windows drains the pipes in communicate's own threads")
def test_a_left_write_printing_more_than_a_pipe_holds_still_ends(tmp_path, monkeypatch):
    """On POSIX nobody read a left write's pipes: one printing more than about
    64 KB blocked on the full pipe, never ended, and every later write was
    refused (reproduced on Linux). Its output is drained, and dropped. Red is
    not achievable on Windows, where communicate's threads drain the pipes
    anyway; this runs on the Linux and macOS CI legs."""
    _hanging(monkeypatch, 1, "import sys; sys.stdout.write('x' * 200000)")
    client = Client()
    leave = threading.Event()
    threading.Timer(0.3, leave.set).start()
    assert client.run("new", write=True, leave=leave).code == ABANDONED
    time.sleep(4)
    _answering(monkeypatch)
    assert client.run("approve", write=True).success


def test_a_left_write_is_drained_on_every_system(monkeypatch):
    """The drain of a left write's output ran only on the POSIX legs: on
    Windows, removing it passed the suite. Leaving a write starts it with the
    write's own process, and it reads the output to its end, whatever fails."""
    drained = []
    monkeypatch.setattr(client_module, "_drain", drained.append)
    _hanging(monkeypatch, 20)
    leave = threading.Event()
    threading.Timer(0.3, leave.set).start()
    client = Client()
    assert client.run("new", write=True, leave=leave).code == ABANDONED
    time.sleep(0.2)
    assert drained == client._left
    client._left[0].kill()

    class Process:
        def __init__(self, error=None):
            self.error, self.read = error, False

        def communicate(self):
            self.read = True
            if self.error:
                raise self.error

    for error in (None, OSError("closed"), ValueError("closed file")):
        process = Process(error)
        _drain_original(process)
        assert process.read


_drain_original = client_module._drain
