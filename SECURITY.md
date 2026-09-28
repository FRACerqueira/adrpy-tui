# Security Policy

## Supported Versions

adrpy-tui is pre-release: nothing is published yet ([ADR003V01](doc/adr/ADR003V01R01-adrpy-ai-is-a-declared-dependency-run-through-the-tui%27s-own-interpreter,-and-adrpy-tui-is-not-published-until-adrpy-ai-is-on-py-pi.md)). Once it is, only the latest released version is supported with security fixes until a stable `1.x` line exists.

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

1. Go to the **Security** tab of this repository on GitHub.
2. Click **"Report a vulnerability"** (GitHub Private Vulnerability Reporting).
3. Include: affected version, reproduction steps, impact, and any suggested mitigation.

If private vulnerability reporting is unavailable for any reason, open an issue asking the maintainer, [@FRACerqueira](https://github.com/FRACerqueira), for a private channel — without any detail of the vulnerability in it.

This is a small, early-stage project maintained by one person — there's no formal SLA, but reports will be acknowledged and investigated as promptly as possible.

## Scope

adrpy-tui is a **local terminal UI**. It writes nothing to a repository itself: every change is an `adrpy` or `adrpy-skills` command run from its own interpreter ([ADR001V01](doc/adr/ADR001V01R01-every-read-and-change-goes-through-the-adrpy-cli-as-a-subprocess,-and-the-tui-decides-on-the-json-code-and-data-only.md)). The only file it writes is its own per-user state (chosen language, last menu items). It does not expose network services and does not handle credentials.

Concerns that are in scope:

- The TUI running a command other than the one its confirmation screen showed, or with different flags.
- The TUI running an executable other than the adrpy installed next to it.
- A decision file's content, shown in the TUI, being able to act on the terminal (escape sequences).
- Supply-chain issues in its runtime dependencies (`textual` and what it pulls in) or its build/dev toolchain.

Vulnerabilities in adrpy itself belong to [adrpy-ai](https://github.com/FRACerqueira/adrpy-ai/security).

## Security Best Practices for Users

- Keep your Python installation, adrpy-tui and adrpy-ai up to date.
- Read the command on the confirmation screen before running it.
