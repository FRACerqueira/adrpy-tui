import sys

from adrpy_tui.core.client import CONTRACT_VIOLATION, Client, display_command

from conftest import completed


def _client(payload, returncode=0, stderr=""):
    calls = []

    def runner(argv):
        calls.append(argv)
        return completed(payload, returncode, stderr)

    return Client(runner=runner), calls


def test_runs_adrpy_from_this_interpreter():
    client, calls = _client({"success": True, "data": {"warnings": []}})
    client.run("new", ("--path", "."))
    assert calls == [[sys.executable, "-m", "adrpy", "new", "--path", "."]]


def test_runs_adrpy_skills_from_this_interpreter():
    client, calls = _client({"success": True, "data": {"warnings": []}})
    client.run("skills:list")
    assert calls == [[sys.executable, "-m", "adrpy.skills", "list"]]


def test_help_of_a_skills_command_asks_adrpy_skills():
    client, calls = _client({"success": True, "data": {"commands": []}})
    client.help("skills:install")
    assert calls == [[sys.executable, "-m", "adrpy.skills", "help", "install"]]


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
