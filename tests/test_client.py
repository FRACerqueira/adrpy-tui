import sys
import threading
import time

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


def test_a_read_that_does_not_answer_is_stopped(monkeypatch):
    """ADR006V01: a read changes nothing, so one that hangs is stopped and
    becomes a failure; it no longer holds every later call behind it."""
    _hanging(monkeypatch, 20)
    monkeypatch.setattr(client_module, "READ_TIMEOUT", 0.5)
    started = time.monotonic()
    result = Client().run("explore", ("--path", "."))
    assert time.monotonic() - started < 5
    assert (result.success, result.code) == (False, TIMED_OUT)


def test_a_write_is_never_stopped_only_left(tmp_path, monkeypatch):
    """ADR006V01: a write may be half-way through its files, so the TUI
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
