[← README](README.md)

# Security Policy

## Supported Versions

Only the latest released version is supported with security fixes, until a stable `1.x` line exists ([ADR0003V01](doc/adr/ADR0003V01R01-adrpy-ai-is-a-declared-dependency-run-through-the-tui%27s-own-interpreter,-and-adrpy-tui-is-not-published-until-adrpy-ai-is-on-py-pi.md) says which adrpy-ai each one requires).

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

1. Go to the **Security** tab of this repository on GitHub.
2. Click **"Report a vulnerability"** (GitHub Private Vulnerability Reporting).
3. Include: affected version, reproduction steps, impact, and any suggested mitigation.

If private vulnerability reporting is unavailable for any reason, open an issue asking the maintainer, [@FRACerqueira](https://github.com/FRACerqueira), for a private channel — without any detail of the vulnerability in it.

This is a small, early-stage project maintained by one person — there's no formal SLA, but reports will be acknowledged and investigated as promptly as possible.

## Scope

adrpy-tui is a **local terminal UI**. It writes nothing to a repository itself: every change is an `adrpy` or `adrpy-skills` command run from its own interpreter ([ADR0001V01](doc/adr/ADR0001V01R01-every-read-and-change-goes-through-the-adrpy-cli-as-a-subprocess,-and-the-tui-decides-on-the-json-code-and-data-only.md)). The only files it writes are its own per-user state (language, appearance and colors, changed keys, last menu items) and, next to it, `error.log` with the traceback of its own last failure. It does not expose network services and does not handle credentials.

Concerns that are in scope:

- The TUI running a command other than the one its confirmation screen showed, or with different flags.
- A value in a text field -- typed, pasted or filled in from a suggestion or the repository -- holding a control, bidirectional or tag character that makes the confirmation read differently from what runs (every field drops them; the other invisible characters stay, and the confirmation writes them out as `<U+XXXX>`).
- The TUI running an executable other than the adrpy installed next to it.
- A decision file's content, shown in the TUI, being able to act on the terminal (escape sequences) or on the UI (markup), or a link in it making the TUI open a file outside the repository or reach another machine ([ADR0006V02](doc/adr/ADR0006V02R02-a-read-from-adrpy-that-hangs-is-stopped,-a-write-never-is,-and-a-link-in-a-file-opens-only-a-file-inside-the-repository.md)).
- A repository's own files running as adrpy (the TUI runs adrpy with `python -P`, and drops empty or relative `PYTHONPATH` entries).
- A folder link (symlink, junction) inside a repository, or a configuration naming a folder outside it, making the TUI read files outside the repository.
- Supply-chain issues in its runtime dependencies (`textual` and what it pulls in) or its build/dev toolchain.

Vulnerabilities in adrpy itself belong to [adrpy-ai](https://github.com/FRACerqueira/adrpy-ai/security).

## Security Best Practices for Users

- Keep your Python installation, adrpy-tui and adrpy-ai up to date -- adrpy-ai within the range your adrpy-tui requires; the main menu says when it is not.
- Read the command on the confirmation screen before running it.
