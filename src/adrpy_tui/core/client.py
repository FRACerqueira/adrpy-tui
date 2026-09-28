"""The only module that runs adrpy (ADR001V01): one command in, one Result out.

A command is an adrpy verb ("new") or an adrpy-skills one ("skills:list").
Both run from this interpreter, so the adrpy used is the one installed next
to the TUI (ADR003V01).
"""

import json
import shlex
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field

from adrpy_tui.core.text import safe, safe_json

SKILLS_PREFIX = "skills:"
# The TUI's own code for a response that is not one adrpy JSON object --
# never one of adrpy's codes, so it can't be mistaken for one.
CONTRACT_VIOLATION = "tui-contract-violation"
# The TUI's own codes for a call that did not end with an answer
# (ADR006V01): a read stopped at its timeout, a write the person left while
# adrpy still ran, an adrpy that could not be started.
TIMED_OUT = "tui-timeout"
ABANDONED = "tui-left-running"
RUN_FAILED = "tui-run-failed"
INTERNAL_ERROR = "tui-internal-error"  # the TUI itself failed; the traceback is in the error log
READ_TIMEOUT = 60  # seconds a read may take before it is stopped

# -P: `python -m` would put the current folder first on the module path, so
# a repository holding an `adrpy/` folder would run instead of the adrpy
# installed next to the TUI.
_PROGRAMS = {
    False: ("adrpy", (sys.executable, "-P", "-m", "adrpy")),
    True: ("adrpy-skills", (sys.executable, "-P", "-m", "adrpy.skills")),
}


@dataclass(frozen=True)
class Result:
    argv: tuple
    exit_code: int
    success: bool
    data: dict = field(default_factory=dict)
    code: str | None = None
    detail: str | None = None
    warnings: list = field(default_factory=list)


def _split(command):
    is_skills = command.startswith(SKILLS_PREFIX)
    verb = command[len(SKILLS_PREFIX):] if is_skills else command
    name, prefix = _PROGRAMS[is_skills]
    return name, prefix, verb


def display_command(command, flags):
    """The command line a person would type for this call, for the
    confirmation screen."""
    name, _, verb = _split(command)
    argv = [name, verb, *flags]
    if sys.platform != "win32":
        return shlex.join(argv)
    # list2cmdline quotes a value only for a space or a tab: a line break
    # alone would read as the start of another command line.
    parts = (subprocess.list2cmdline([arg]) for arg in argv)
    return " ".join(f'"{part}"' if "\n" in part and not part.startswith('"') else part for part in parts)


class _TimedOut(Exception):
    pass


class _Left(Exception):
    pass


def _run(argv, timeout=None, leave=None):
    """Runs adrpy. A read stops it after `timeout` seconds; a write (no
    timeout) is never stopped -- when `leave` is set, the waiting ends and
    adrpy goes on to its own end (ADR006V01)."""
    # stdin is the TUI's terminal; adrpy never prompts, so give it nothing.
    process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding="utf-8", errors="replace")
    deadline = None if timeout is None else time.monotonic() + timeout
    while True:
        try:
            stdout, stderr = process.communicate(timeout=0.2)
            return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)
        except subprocess.TimeoutExpired:
            if deadline is not None and time.monotonic() > deadline:
                process.kill()
                process.communicate()
                raise _TimedOut() from None
            if leave is not None and leave.is_set():
                raise _Left() from None


class Client:
    def __init__(self, runner=_run):
        self._runner = runner
        # One adrpy call at a time, whichever worker asks (adrpy-ai ADR001V01).
        self._lock = threading.Lock()

    def run(self, command, flags=(), write=False, leave=None):
        """One call, always a Result: a read is stopped after READ_TIMEOUT;
        a write is not, and ends with ABANDONED once `leave` is set."""
        _, prefix, verb = _split(command)
        argv = (*prefix, verb, *flags)
        with self._lock:
            try:
                completed = self._runner(list(argv), timeout=None if write else READ_TIMEOUT, leave=leave)
            except _TimedOut:
                return Result(argv, -1, False, code=TIMED_OUT,
                              detail=f"adrpy did not answer within {READ_TIMEOUT} s and was stopped "
                              "(a read changes nothing).")
            except _Left:
                return Result(argv, -1, False, code=ABANDONED,
                              detail="adrpy is still running: its result is unknown. Run check to see the "
                              "repository's state.")
            except OSError as error:
                return Result(argv, -1, False, code=RUN_FAILED,
                              detail=f"adrpy could not be started: {safe(str(error))}")
        return _parse(argv, completed)

    def help(self, command):
        """`help <verb>` of the program the command belongs to."""
        name, _, verb = _split(command)
        return self.run("skills:help" if name == "adrpy-skills" else "help", (verb,))


def _parse(argv, completed):
    try:
        # File names and header cells come back in it: nothing of them may
        # act on the terminal (SECURITY.md).
        payload = safe_json(json.loads(completed.stdout))
    except (ValueError, RecursionError):
        payload = None
    if not isinstance(payload, dict) or not isinstance(payload.get("success"), bool):
        return Result(
            argv,
            completed.returncode,
            False,
            code=CONTRACT_VIOLATION,
            detail=f"adrpy did not answer with one JSON object (exit code {completed.returncode}): "
            f"{safe((completed.stdout or completed.stderr).strip()[:300])}",
        )
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    # A success carries its warnings inside data; a failure, next to code.
    warnings = data.get("warnings") if payload["success"] else payload.get("warnings")
    return Result(
        argv,
        completed.returncode,
        payload["success"],
        data=data,
        code=_text_or_none(payload.get("code")),
        detail=_text_or_none(payload.get("detail")),
        warnings=_texts(warnings),
    )


def _text_or_none(value):
    return None if value is None else str(value)


def _texts(value):
    """Warnings as a list of strings, whatever shape they came in."""
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value] if isinstance(value, list) else []
