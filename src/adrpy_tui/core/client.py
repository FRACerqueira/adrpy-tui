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
from dataclasses import dataclass, field

from adrpy_tui.core.text import safe, safe_json

SKILLS_PREFIX = "skills:"
# The TUI's own code for a response that is not one adrpy JSON object --
# never one of adrpy's codes, so it can't be mistaken for one.
CONTRACT_VIOLATION = "tui-contract-violation"

_PROGRAMS = {
    False: ("adrpy", (sys.executable, "-m", "adrpy")),
    True: ("adrpy-skills", (sys.executable, "-m", "adrpy.skills")),
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
    return subprocess.list2cmdline(argv) if sys.platform == "win32" else shlex.join(argv)


def _run(argv):
    # stdin is the TUI's terminal; adrpy never prompts, so give it nothing.
    return subprocess.run(
        argv, capture_output=True, stdin=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace"
    )


class Client:
    def __init__(self, runner=_run):
        self._runner = runner
        # One adrpy call at a time, whichever worker asks (adrpy-ai ADR001V01).
        self._lock = threading.Lock()

    def run(self, command, flags=()):
        _, prefix, verb = _split(command)
        argv = (*prefix, verb, *flags)
        with self._lock:
            completed = self._runner(list(argv))
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
    except ValueError:
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
        code=payload.get("code"),
        detail=payload.get("detail"),
        warnings=list(warnings or []),
    )
