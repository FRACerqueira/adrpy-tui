<!-- Do not edit or remove this comment, lines and table (1-12) -->
|Fields|Values|
|--|--|
|File title md|On every start the TUI checks PyPI for a newer adrpy-tui in the background, with the standard library only, and only shows a notice|
|Version|01|
|Revision|01|
|Scope||
|Domain||
|Created|Proposed (2026-10-02) <!-- Proposed -->|
|Changed|Accepted (2026-10-02) <!-- Accepted -->|
|Superseded||
<!-- Do not edit or remove this comment, lines and table (1-12) -->
---
# On every start the TUI checks PyPI for a newer adrpy-tui in the background, with the standard library only, and only shows a notice

## Deciders

* Deciders: [list everyone involved in the decision] <!-- optional -->

## Context and Problem Statement

A person who installed adrpy-tui learns of a newer release only by looking on PyPI. How does the TUI tell them?

## Decision Drivers <!-- optional -->

* The simplest way that tells the person.
* No automatic update: its complexity (pip, pipx, a venv) is avoided.
* As few external dependencies as possible.

## Considered Options

* Check on every start and only show a notice.
* Check once a day, show the update command, and offer to update on exit.

## Decision Outcome

Chosen option: "Check on every start and only show a notice", because it is the simplest and leaves the update to the person.

1. On every start, the TUI checks PyPI for a newer adrpy-tui in the background, without delaying the start.
2. Only the standard library is used: no new dependency.
3. A newer version is shown as a notice naming it and the installed one. The TUI shows no update command and never updates itself.
4. A failed check shows nothing.
5. Two per-user settings: "check for a new version", on by default; "include pre-releases", off by default.

### Positive Consequences <!-- optional -->

* No new dependency, and nothing is run on the person's installation.

### Negative Consequences <!-- optional -->

* The TUI reaches the network on every start while the check is on.
