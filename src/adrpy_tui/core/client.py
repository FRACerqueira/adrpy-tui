"""The only module that runs adrpy (ADR0001V01): one command in, one Result out.

A command is an adrpy verb ("new") or an adrpy-skills one ("skills:list").
Both run from this interpreter, so the adrpy used is the one installed next
to the TUI (ADR0003V01).
"""

import json
import os
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
# (ADR0006V02): a read stopped at its timeout, a write the person left while
# adrpy still ran, an adrpy that could not be started.
TIMED_OUT = "tui-timeout"
ABANDONED = "tui-left-running"
RUN_FAILED = "tui-run-failed"
# A write the TUI did not start: the person left while it waited for adrpy,
# or one left running still runs (two adrpy writes on one working copy are
# a usage error for adrpy-ai, its own ADR0001V01).
NOT_STARTED = "tui-not-started"
WRITE_STILL_RUNNING = "tui-write-still-running"
STOPPED = "tui-stopped"  # a read stopped because the TUI is quitting
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
    # alone would read as the start of another command line. Such a value is
    # quoted from itself, never from list2cmdline's output, whose own escape
    # of a quote would be doubled.
    return " ".join(_quoted(arg) if "\n" in arg else subprocess.list2cmdline([arg]) for arg in argv)


def _quoted(arg):
    """`arg` quoted as Windows parses it back: the backslashes before a quote,
    and those before the closing one, doubled."""
    quoted, backslashes = [], 0
    for char in arg:
        if char == "\\":
            backslashes += 1
            continue
        quoted.append("\\" * (backslashes * 2 + 1) + '"' if char == '"' else "\\" * backslashes + char)
        backslashes = 0
    return '"' + "".join(quoted) + "\\" * (backslashes * 2) + '"'


class _TimedOut(Exception):
    pass


class _Left(Exception):
    """The waiting ended because the person left or the TUI quits."""

    def __init__(self, process=None, started=False):
        super().__init__()
        self.process = process  # a write's, still running
        self.started = started  # adrpy was started (a read stopped, or a write left)


def _environment():
    """This environment for adrpy, but a PYTHONPATH entry that is empty or
    relative -- which names the current folder, what -P keeps out -- dropped."""
    environment = dict(os.environ)
    if "PYTHONPATH" in environment:
        kept = [entry for entry in environment["PYTHONPATH"].split(os.pathsep) if entry and os.path.isabs(entry)]
        if kept:
            environment["PYTHONPATH"] = os.pathsep.join(kept)
        else:
            del environment["PYTHONPATH"]
    return environment


def _stop(process):
    process.kill()
    try:
        # Bounded: a process adrpy started may hold the output open past the kill.
        process.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        pass


def _drain(process):
    """Reads a left write's output to its end, and drops it: nobody else
    reads it, and on POSIX a full pipe would block adrpy forever."""
    try:
        process.communicate()
    except (OSError, ValueError):
        pass


def _run(argv, timeout=None, leave=None):
    """Runs adrpy. A read (a timeout) is stopped after `timeout` seconds, or
    once `leave` is set; a write (no timeout) is never stopped -- when
    `leave` is set, the waiting ends and adrpy goes on to its own end
    (ADR0006V02)."""
    if leave is not None and leave.is_set():
        raise _Left()
    # stdin is the TUI's terminal; adrpy never prompts, so give it nothing.
    process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding="utf-8", errors="replace", env=_environment())
    deadline = None if timeout is None else time.monotonic() + timeout
    while True:
        try:
            stdout, stderr = process.communicate(timeout=0.2)
            return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)
        except subprocess.TimeoutExpired:
            if deadline is not None and time.monotonic() > deadline:
                _stop(process)
                raise _TimedOut() from None
            if leave is not None and leave.is_set():
                if timeout is not None:  # a read changes nothing: stop it
                    _stop(process)
                    raise _Left(started=True) from None
                threading.Thread(target=_drain, args=(process,), daemon=True).start()
                raise _Left(process, started=True) from None


class _Either:
    """Set once either event is."""

    def __init__(self, *events):
        self._events = [event for event in events if event is not None]

    def is_set(self):
        return any(event.is_set() for event in self._events)


class Client:
    def __init__(self, runner=_run):
        self._runner = runner
        # One adrpy call at a time, whichever worker asks (adrpy-ai ADR0001V01).
        self._lock = threading.Lock()
        self._closing = threading.Event()  # the TUI is quitting: stop reads, leave writes
        self._left = []  # the processes of writes left running

    def shutdown(self):
        """Every call in flight or waiting ends now: a read is stopped, a
        write left to its own end."""
        self._closing.set()

    def still_writing(self):
        """Whether a write the person left still runs."""
        self._left = [process for process in self._left if process.poll() is None]
        return bool(self._left)

    def run(self, command, flags=(), write=False, leave=None):
        """One call, always a Result: a read is stopped after READ_TIMEOUT;
        a write is not, and ends with ABANDONED once `leave` is set."""
        _, prefix, verb = _split(command)
        argv = (*prefix, verb, *flags)
        stop = _Either(leave, self._closing)
        # Waiting for the lock ends too when the person leaves: a write queued
        # behind a hung read must not start after they left.
        while not self._lock.acquire(timeout=0.2):
            if stop.is_set():
                return Result(argv, -1, False, code=NOT_STARTED,
                              detail="adrpy was not run: another call still held it when you left.")
        try:
            if write and self.still_writing():
                return Result(argv, -1, False, code=WRITE_STILL_RUNNING,
                              detail="A command you left is still running: wait for it to end, then run check "
                              "to see the repository's state.")
            try:
                completed = self._runner(list(argv), timeout=None if write else READ_TIMEOUT, leave=stop)
            except _TimedOut:
                return Result(argv, -1, False, code=TIMED_OUT,
                              detail=f"adrpy did not answer within {READ_TIMEOUT} s and was stopped "
                              "(a read changes nothing).")
            except _Left as left:
                if not left.started:
                    return Result(argv, -1, False, code=NOT_STARTED, detail="adrpy was not run: you left first.")
                if left.process is None:
                    return Result(argv, -1, False, code=STOPPED,
                                  detail="adrpy was stopped: the TUI is quitting (a read changes nothing).")
                self._left.append(left.process)
                return Result(argv, -1, False, code=ABANDONED,
                              detail="adrpy is still running: its result is unknown. Run check to see the "
                              "repository's state.")
            except (OSError, ValueError, TypeError) as error:
                return Result(argv, -1, False, code=RUN_FAILED,
                              detail=f"adrpy could not be started: {safe(str(error))}")
        finally:
            self._lock.release()
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
